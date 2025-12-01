from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import ApiResponse, SubmissionCreate, PublicSurveyResponse
from app.services import SurveyService, SubmissionService, FileService


router = APIRouter(prefix="/public", tags=["公开接口"])


@router.get("/survey/active", response_model=ApiResponse)
async def get_active_survey(
    db: AsyncSession = Depends(get_db),
):
    """获取当前激活的问卷（公开，无需认证）"""
    survey = await SurveyService.get_active_survey(db)
    
    if not survey:
        raise HTTPException(status_code=404, detail="当前没有可用的问卷")
    
    # 获取问题（可能是随机的）
    questions = await SubmissionService.get_random_questions(survey)
    
    return ApiResponse(
        success=True,
        data={
            "code": survey.code,
            "title": survey.title,
            "description": survey.description,
            "questions": [
                {
                    "id": q.id,
                    "title": q.title,
                    "description": q.description,
                    "type": q.type,
                    "options": q.options,
                    "is_required": q.is_required,
                    "validation": q.validation,
                }
                for q in questions
            ],
        }
    )


@router.get("/surveys/{code}", response_model=ApiResponse)
async def get_public_survey(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """获取问卷（公开，无需认证）"""
    survey = await SurveyService.get_survey_by_code(db, code)
    
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    if not survey.is_active:
        raise HTTPException(status_code=400, detail="问卷已关闭")
    
    # 获取问题（可能是随机的）
    questions = await SubmissionService.get_random_questions(survey)
    
    return ApiResponse(
        success=True,
        data={
            "code": survey.code,
            "title": survey.title,
            "description": survey.description,
            "questions": [
                {
                    "id": q.id,
                    "title": q.title,
                    "description": q.description,
                    "type": q.type,
                    "options": q.options,
                    "is_required": q.is_required,
                    "validation": q.validation,
                }
                for q in questions
            ],
        }
    )


@router.post("/surveys/{code}/submit", response_model=ApiResponse)
async def submit_survey(
    code: str,
    data: SubmissionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """提交问卷（公开，无需认证）"""
    survey = await SurveyService.get_survey_by_code(db, code)
    
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    
    if not survey.is_active:
        raise HTTPException(status_code=400, detail="问卷已关闭")
    
    # 获取 IP 地址
    ip_address = request.client.host if request.client else None
    
    # 验证答案
    question_ids = {q.id for q in survey.questions}
    for answer in data.answers:
        if answer.question_id not in question_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的问题 ID: {answer.question_id}"
            )
    
    # 检查必填问题
    required_questions = {q.id for q in survey.questions if q.is_required}
    answered_questions = {a.question_id for a in data.answers}
    missing = required_questions - answered_questions
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"缺少必填问题的答案: {list(missing)}"
        )
    
    # 创建提交
    submission = await SubmissionService.create_submission(
        db, survey, data, ip_address
    )
    
    return ApiResponse(
        success=True,
        data={
            "id": submission.id,
            "message": "提交成功，请等待审核",
        }
    )


@router.post("/upload", response_model=ApiResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传文件（公开，用于问卷中的图片上传）"""
    uploaded = await FileService.save_file(db, file)
    
    return ApiResponse(
        success=True,
        data={
            "filename": uploaded.filename,
            "stored_name": uploaded.stored_name,
            "url": FileService.get_file_url(uploaded.stored_name),
            "size": uploaded.file_size,
            "mime_type": uploaded.mime_type,
        }
    )
