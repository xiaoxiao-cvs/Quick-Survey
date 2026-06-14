"""
Convenient-access mod 后端客户端。

仅在玩家凭 token 自助领码时被调用: 问卷后端以服务端身份 (X-API-Key) 调 mod 的
POST /api/v1/whitelist/regcode 为该玩家名签发一次性注册码。明文码经此一跳返回给玩家,
严禁写入日志。配置缺失或 mod 返回异常一律抛 HTTPException 自然冒泡, 不静默吞。
"""
import httpx
from fastapi import HTTPException

from app.core.config import get_settings


async def issue_registration_code(player_name: str) -> dict:
    """
    向 mod 取得绑定 player_name 的一次性注册码。

    Returns:
        {"registration_code": str, "code_expires_minutes": int}

    Raises:
        HTTPException: mod 未配置 / 网络失败 / mod 返回非成功 / 响应缺少注册码。
    """
    settings = get_settings()
    base = settings.mod.api_base.rstrip("/")
    api_key = settings.mod.api_key

    if not base or not api_key:
        raise HTTPException(status_code=503, detail="领码功能未配置 (缺少 mod 后端地址或密钥)")

    url = f"{base}/api/v1/whitelist/regcode"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={"name": player_name},
                headers={"X-API-Key": api_key},
                timeout=10.0,
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail="无法连接发码服务, 请稍后重试") from e

    body = resp.json() if resp.content else {}
    if resp.status_code != 200 or not body.get("success"):
        # 透传 mod 的可读错误 (如认证未启用 409), 但不暴露内部细节
        msg = (body.get("error") or {}).get("message") if isinstance(body.get("error"), dict) else None
        raise HTTPException(status_code=502, detail=msg or "发码服务返回异常, 请联系管理员")

    data = body.get("data") or {}
    code = data.get("registration_code")
    if not code:
        raise HTTPException(status_code=502, detail="发码服务未返回注册码, 请联系管理员")

    return {
        "registration_code": code,
        "code_expires_minutes": data.get("code_expires_minutes"),
    }
