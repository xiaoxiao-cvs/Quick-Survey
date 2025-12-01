from fastapi import APIRouter

from app.api.surveys import router as surveys_router
from app.api.submissions import router as submissions_router
from app.api.public import router as public_router


router = APIRouter(prefix="/api/v1")

# 注册路由
router.include_router(surveys_router)
router.include_router(submissions_router)
router.include_router(public_router)
