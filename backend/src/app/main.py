from contextlib import asynccontextmanager
from pathlib import Path
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.db import init_db
from app.api import router
from app.services.cleanup import CleanupService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    settings = get_settings()
    
    # 确保数据目录存在
    Path("data").mkdir(exist_ok=True)
    Path(settings.upload.path).mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库
    await init_db()
    
    print(f"🚀 Quick-Survey 启动成功")
    print(f"📍 API 文档: http://{settings.server.host}:{settings.server.port}/docs")
    
    # 启动后台清理任务
    CleanupService.start_background_task()
    
    yield
    
    # 关闭时
    CleanupService.stop_background_task()
    print("👋 Quick-Survey 已关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    settings = get_settings()
    
    app = FastAPI(
        title="Quick-Survey API",
        description="问卷调查系统 API",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # CORS 中间件
    origins = settings.cors.allowed_origins
    # 如果配置了 ["*"]，需要特殊处理
    if origins == ["*"]:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,  # 使用通配符时不能启用 credentials
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 静态文件（上传的图片）
    upload_path = Path(settings.upload.path)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")
    
    # 注册路由
    app.include_router(router)
    
    # 请求验证错误处理器 - 记录详细的验证错误
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # 记录详细错误信息
        logger.error(f"[ValidationError] URL: {request.url}")
        logger.error(f"[ValidationError] Method: {request.method}")
        logger.error(f"[ValidationError] Errors: {exc.errors()}")
        
        # 尝试记录请求体（如果可能）
        try:
            body = await request.body()
            if len(body) < 2000:  # 只记录小于 2KB 的请求体
                logger.error(f"[ValidationError] Body: {body.decode('utf-8', errors='ignore')[:500]}")
        except Exception:
            pass
        
        # 返回更友好的错误信息
        error_messages = []
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error.get("loc", []))
            msg = error.get("msg", "")
            error_messages.append(f"{loc}: {msg}")
        
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "请求数据验证失败",
                    "details": error_messages,
                }
            }
        )
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "quick-survey"}
    
    return app


app = create_app()
