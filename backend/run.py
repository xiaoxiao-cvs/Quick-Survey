#!/usr/bin/env python
"""Quick-Survey 启动脚本"""

import os
import sys

# 切换到 backend 目录，确保配置文件能正确读取
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

# 添加 src 目录到 Python 路径
src_dir = os.path.join(backend_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import uvicorn
from app.core.config import get_settings


def main():
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug,
    )


if __name__ == "__main__":
    main()
