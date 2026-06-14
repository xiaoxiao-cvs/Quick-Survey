"""
IP 归属地解析单元测试。

- _format_region: 纯函数, 始终运行 (国内去"中国"前缀+去国家代码、海外保留国家、空值降级)。
- lookup: 依赖离线 xdb 数据文件, 文件缺失则跳过 (xdb 已 gitignore, 部署时单独提供);
  私网/无效/空一律 None (这部分不依赖 xdb, 始终运行)。
"""
import pytest

from app.services.ip_location import lookup, _format_region, _XDB_PATH

xdb_required = pytest.mark.skipif(not _XDB_PATH.exists(), reason="ip2region xdb 数据文件不存在")


def test_format_region_domestic_drops_china_prefix_and_country_code():
    assert _format_region("中国|江苏省|南京市|0|CN") == "江苏省 南京市"
    assert _format_region("中国|浙江省|杭州市|阿里|CN") == "浙江省 杭州市 阿里"


def test_format_region_overseas_keeps_country():
    assert _format_region("United States|California|0|Google LLC|US") == "United States California Google LLC"


def test_format_region_dedupes_and_handles_empty():
    assert _format_region(None) is None
    assert _format_region("") is None
    assert _format_region("0|0|0|0|0") is None
    # 直辖市省市同名去重
    assert _format_region("中国|北京市|北京市|联通|CN") == "北京市 联通"


def test_lookup_rejects_private_invalid_and_empty():
    # 这部分在 xdb 之前短路, 不依赖数据文件
    assert lookup("192.168.1.1") is None
    assert lookup("10.0.0.5") is None
    assert lookup("127.0.0.1") is None
    assert lookup("not-an-ip") is None
    assert lookup("") is None
    assert lookup(None) is None


@xdb_required
def test_lookup_known_domestic_ip():
    r = lookup("114.114.114.114")
    assert r is not None and "江苏" in r and "南京" in r, f"got {r!r}"


@xdb_required
def test_lookup_overseas_ip():
    r = lookup("8.8.8.8")
    assert r is not None and "California" in r, f"got {r!r}"
