# 延迟导入，避免循环依赖
def get_app():
    from app.main import app
    return app

__all__ = ["get_app"]
