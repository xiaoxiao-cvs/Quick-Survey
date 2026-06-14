"""
查询端点 per-IP per-minute 限流单元测试 (默认 rate_limit.enabled=True)。
"""
import pytest
from fastapi import HTTPException

from app.core.rate_limit import check_query_rate_limit, MAX_QUERY_PER_MINUTE, _query_hits


async def test_blocks_after_per_minute_cap():
    ip = "203.0.113.7"  # TEST-NET-3, 不与真实数据冲突
    _query_hits.pop(ip, None)
    for _ in range(MAX_QUERY_PER_MINUTE):
        await check_query_rate_limit(ip)  # 额度内不抛
    with pytest.raises(HTTPException) as exc:
        await check_query_rate_limit(ip)  # 超限
    assert exc.value.status_code == 429
    _query_hits.pop(ip, None)


async def test_skips_when_no_ip():
    # 取不到 IP 时放行, 不抛
    await check_query_rate_limit(None)
    await check_query_rate_limit("")
