#!/usr/bin/env python
"""Quick-Survey 启动脚本"""

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
