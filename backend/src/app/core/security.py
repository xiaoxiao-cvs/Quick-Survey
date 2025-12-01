"""
安全模块 - 处理 Turnstile 验证、提交时间检测
IP 限流已移至 rate_limit.py 模块
"""
import time
from typing import Optional
import httpx
from fastapi import HTTPException

from app.core.config import get_settings


async def verify_turnstile(token: str, ip: Optional[str] = None) -> bool:
    """
    验证 Cloudflare Turnstile token
    
    Args:
        token: 前端传来的 Turnstile token
        ip: 用户 IP 地址（可选，用于增强验证）
    
    Returns:
        验证是否成功
    """
    settings = get_settings()
    
    if not settings.security.turnstile.enabled:
        return True
    
    if not token:
        raise HTTPException(status_code=400, detail="缺少安全验证 token")
    
    secret_key = settings.security.turnstile.secret_key
    if not secret_key:
        # 未配置密钥，跳过验证（开发环境）
        return True
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": secret_key,
                    "response": token,
                    **({"remoteip": ip} if ip else {}),
                },
                timeout=10.0,
            )
            result = response.json()
            
            if not result.get("success"):
                error_codes = result.get("error-codes", [])
                raise HTTPException(
                    status_code=400, 
                    detail=f"安全验证失败: {', '.join(error_codes) if error_codes else '未知错误'}"
                )
            
            return True
    except httpx.RequestError as e:
        # 网络错误时，根据配置决定是否放行
        if settings.server.debug:
            return True
        raise HTTPException(status_code=500, detail="安全验证服务暂时不可用")


def check_submit_time(start_time: Optional[float]) -> float:
    """
    检查提交时间是否合理，并返回填写耗时
    
    Args:
        start_time: 用户开始填写问卷的时间戳（秒）
    
    Returns:
        填写耗时（秒），如果没有开始时间则返回 0
    
    Raises:
        HTTPException: 提交时间过短时抛出
    """
    settings = get_settings()
    
    if start_time is None:
        # 没有开始时间，跳过检测
        return 0.0
    
    elapsed = time.time() - start_time
    
    if settings.security.time_check.enabled:
        min_time = settings.security.time_check.min_submit_time
        if elapsed < min_time:
            raise HTTPException(
                status_code=400, 
                detail=f"提交时间过短（{elapsed:.1f}秒），请认真填写问卷"
            )
    
    return elapsed


def get_real_ip(request) -> Optional[str]:
    """
    获取用户真实 IP 地址
    
    支持常见的代理头部：
    - X-Forwarded-For
    - X-Real-IP
    - CF-Connecting-IP (Cloudflare)
    """
    # Cloudflare
    if cf_ip := request.headers.get("CF-Connecting-IP"):
        return cf_ip
    
    # X-Forwarded-For (可能包含多个 IP，取第一个)
    if forwarded := request.headers.get("X-Forwarded-For"):
        return forwarded.split(",")[0].strip()
    
    # X-Real-IP
    if real_ip := request.headers.get("X-Real-IP"):
        return real_ip
    
    # 直连
    if request.client:
        return request.client.host
    
    return None


def get_security_config() -> dict:
    """
    获取前端需要的安全配置
    """
    settings = get_settings()
    
    return {
        "turnstile_enabled": settings.security.turnstile.enabled,
        "time_check_enabled": settings.security.time_check.enabled,
        "min_submit_time": settings.security.time_check.min_submit_time if settings.security.time_check.enabled else 0,
    }
