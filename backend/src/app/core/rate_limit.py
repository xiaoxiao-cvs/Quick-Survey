"""
IP 限流模块 - 使用本地 JSON 文件存储
"""
import json
import asyncio
import aiofiles
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.core.config import get_settings


# JSON 文件路径
RATE_LIMIT_FILE = Path("data/rate_limit.json")

# 内存缓存
_cache: dict = {
    "submissions": {},  # {ip: [(timestamp, survey_code), ...]}
    "uploads": {},      # {ip: [timestamp, ...]}
}
_cache_dirty = False
_lock = asyncio.Lock()


async def _load_from_file() -> None:
    """从 JSON 文件加载数据到内存"""
    global _cache
    
    if not RATE_LIMIT_FILE.exists():
        return
    
    try:
        async with aiofiles.open(RATE_LIMIT_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            if content.strip():
                _cache = json.loads(content)
    except (json.JSONDecodeError, IOError):
        # 文件损坏或读取失败，使用空缓存
        _cache = {"submissions": {}, "uploads": {}}


async def _save_to_file() -> None:
    """保存内存数据到 JSON 文件"""
    global _cache_dirty
    
    # 确保目录存在
    RATE_LIMIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(RATE_LIMIT_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(_cache, ensure_ascii=False, indent=2))
    
    _cache_dirty = False


async def _ensure_loaded() -> None:
    """确保数据已加载"""
    if not _cache.get("_loaded"):
        await _load_from_file()
        _cache["_loaded"] = True


async def _save_if_dirty() -> None:
    """如果数据有变化则保存"""
    global _cache_dirty
    if _cache_dirty:
        await _save_to_file()


def _clean_old_records(records: list, cutoff_time: float) -> list:
    """清理过期记录"""
    if isinstance(records[0] if records else None, list):
        # submissions 格式: [[timestamp, survey_code], ...]
        return [r for r in records if r[0] > cutoff_time]
    else:
        # uploads 格式: [timestamp, ...]
        return [r for r in records if r > cutoff_time]


async def check_ip_rate_limit(ip: str, survey_code: str) -> None:
    """
    检查 IP 提交频率限制
    
    Args:
        ip: 用户 IP 地址
        survey_code: 问卷代码
    
    Raises:
        HTTPException: 超过限制时抛出
    """
    settings = get_settings()
    
    if not settings.security.rate_limit.enabled:
        return
    
    if not ip:
        return
    
    async with _lock:
        await _ensure_loaded()
        
        max_submissions = settings.security.rate_limit.max_submissions_per_day
        now = datetime.now(timezone.utc).timestamp()
        one_day_ago = now - 86400  # 24小时前
        
        # 获取并清理过期记录
        submissions = _cache.get("submissions", {})
        ip_records = submissions.get(ip, [])
        ip_records = _clean_old_records(ip_records, one_day_ago)
        
        # 统计当天提交次数
        today_count = len(ip_records)
        
        if today_count >= max_submissions:
            raise HTTPException(
                status_code=429, 
                detail=f"提交过于频繁，每个 IP 每天最多提交 {max_submissions} 次，请明天再试"
            )


async def record_ip_submission(ip: str, survey_code: str) -> None:
    """
    记录 IP 提交（在提交成功后调用）
    
    Args:
        ip: 用户 IP 地址
        survey_code: 问卷代码
    """
    global _cache_dirty
    
    if not ip:
        return
    
    async with _lock:
        await _ensure_loaded()
        
        now = datetime.now(timezone.utc).timestamp()
        one_day_ago = now - 86400
        
        if "submissions" not in _cache:
            _cache["submissions"] = {}
        
        # 清理过期记录并添加新记录
        ip_records = _cache["submissions"].get(ip, [])
        ip_records = _clean_old_records(ip_records, one_day_ago)
        ip_records.append([now, survey_code])
        _cache["submissions"][ip] = ip_records
        
        _cache_dirty = True
        await _save_if_dirty()


async def check_upload_rate_limit(ip: Optional[str]) -> None:
    """
    检查 IP 上传频率限制
    基于配置的每日最大提交次数来限制上传，每次提交最多允许上传 5 张图片
    
    Args:
        ip: 用户 IP 地址
    
    Raises:
        HTTPException: 超过限制时抛出
    """
    settings = get_settings()
    
    if not settings.security.rate_limit.enabled:
        return
    
    if not ip:
        return
    
    async with _lock:
        await _ensure_loaded()
        
        # 每日最大提交次数 * 每次最多 5 张图片 = 每日最大上传次数
        max_submissions = settings.security.rate_limit.max_submissions_per_day
        max_uploads_per_day = max_submissions * 5
        
        now = datetime.now(timezone.utc).timestamp()
        one_day_ago = now - 86400  # 24小时前
        
        # 获取并清理过期记录
        uploads = _cache.get("uploads", {})
        ip_records = uploads.get(ip, [])
        ip_records = [ts for ts in ip_records if ts > one_day_ago]
        
        # 统计当天上传次数
        day_count = len(ip_records)
        
        if day_count >= max_uploads_per_day:
            raise HTTPException(
                status_code=429, 
                detail=f"上传过于频繁，每个 IP 每天最多上传 {max_uploads_per_day} 张图片"
            )


async def record_ip_upload(ip: Optional[str]) -> None:
    """
    记录 IP 上传（在上传成功后调用）
    
    Args:
        ip: 用户 IP 地址
    """
    global _cache_dirty
    
    if not ip:
        return
    
    async with _lock:
        await _ensure_loaded()
        
        now = datetime.now(timezone.utc).timestamp()
        one_day_ago = now - 86400
        
        if "uploads" not in _cache:
            _cache["uploads"] = {}
        
        # 清理过期记录并添加新记录
        ip_records = _cache["uploads"].get(ip, [])
        ip_records = [ts for ts in ip_records if ts > one_day_ago]
        ip_records.append(now)
        _cache["uploads"][ip] = ip_records
        
        _cache_dirty = True
        await _save_if_dirty()


async def get_rate_limit_stats() -> dict:
    """获取限流统计信息（管理接口用）"""
    async with _lock:
        await _ensure_loaded()
        
        now = datetime.now(timezone.utc).timestamp()
        one_day_ago = now - 86400
        
        submissions = _cache.get("submissions", {})
        uploads = _cache.get("uploads", {})
        
        # 统计活跃 IP 数量
        active_submission_ips = sum(
            1 for records in submissions.values() 
            if any(r[0] > one_day_ago for r in records)
        )
        active_upload_ips = sum(
            1 for records in uploads.values() 
            if any(ts > one_day_ago for ts in records)
        )
        
        return {
            "active_submission_ips": active_submission_ips,
            "active_upload_ips": active_upload_ips,
            "total_ips_tracked": len(set(submissions.keys()) | set(uploads.keys())),
        }
