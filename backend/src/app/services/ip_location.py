"""
IP 归属地解析 (离线 ip2region xdb, 玩家 IP 不出本机, 无第三方/无频率限制)。

数据文件 app/resources/ip2region_v4.xdb (vendored 官方 v4 库, 已 gitignore, 由部署单独提供)。
缺失/损坏/海外/私网一律优雅降级返回 None, 不影响审核详情主流程。

ip2region 包 (src/ip2region) 由 run.py / pytest 把 src 加入 sys.path 后以顶层包导入。
v4 region 形态: "国家|省份|城市|ISP|国家代码"。
"""
import io
import ipaddress
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 解析器在 app/services/, 数据在 app/resources/
_XDB_PATH = Path(__file__).resolve().parent.parent / "resources" / "ip2region_v4.xdb"


@lru_cache(maxsize=1)
def _searcher():
    """惰性加载整个 xdb 到内存 (content 策略, ~10MB, 仅一次)。失败返回 None 由调用方降级。"""
    try:
        import ip2region.util as util
        import ip2region.searcher as xdb
    except Exception:
        logger.exception("ip2region 包导入失败, IP 归属地停用")
        return None

    if not _XDB_PATH.exists():
        logger.warning("ip2region xdb 不存在, IP 归属地停用: %s", _XDB_PATH)
        return None

    try:
        with io.open(_XDB_PATH, "rb") as f:
            header = util.load_header(f)
            version = util.version_from_header(header)
            if version is None:
                logger.error("ip2region xdb 头部无法识别版本, 停用")
                return None
            buffer = util.load_content(f)
        return xdb.new_with_buffer(version, buffer), util
    except Exception:
        logger.exception("ip2region searcher 初始化失败, IP 归属地停用")
        return None


def _format_region(region: Optional[str]) -> Optional[str]:
    """"国家|省份|城市|ISP|国家代码" -> "浙江省 杭州市 阿里" (国内去"中国"前缀; 丢国家代码与 0/空占位)。"""
    if not region:
        return None
    core = region.split("|")[:4]  # 取 国家/省/市/ISP, 丢末位国家代码
    parts = [p for p in core if p and p != "0"]
    if len(parts) > 1 and parts[0] == "中国":
        parts = parts[1:]
    seen: set[str] = set()
    out = []
    for p in parts:  # 去重保序 (直辖市等省市同名)
        if p not in seen:
            seen.add(p)
            out.append(p)
    return " ".join(out) if out else None


def lookup(ip: Optional[str]) -> Optional[str]:
    """IP -> 归属地中文串 (如 '浙江省 杭州市 阿里')。私网/无效/海外无数据/未加载 返回 None。"""
    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local:
        return None

    s = _searcher()
    if s is None:
        return None
    searcher, util = s
    try:
        region = searcher.search(util.parse_ip(ip))
    except Exception:
        # v6 地址命中 v4 库等情况: 降级为无归属地, 不冒泡打断审核详情
        logger.debug("IP 归属地查询失败: %s", ip, exc_info=True)
        return None
    return _format_region(region)
