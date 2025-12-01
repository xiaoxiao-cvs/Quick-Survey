from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import ApiResponse, SubmissionCreate, PublicSurveyResponse
from app.services import SurveyService, SubmissionService, FileService
from app.core import (
    verify_turnstile,
    check_ip_rate_limit,
    record_ip_submission,
    check_upload_rate_limit,
    record_ip_upload,
    check_submit_time,
    get_real_ip,
    get_security_config,
)


router = APIRouter(prefix="/public", tags=["公开接口"])


@router.get("/security-config", response_model=ApiResponse)
async def get_security_settings():
    """获取安全配置（供前端使用）"""
    return ApiResponse(
        success=True,
        data=get_security_config()
    )



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
    
    # 获取真实 IP 地址
    ip_address = get_real_ip(request)
    
    # === 安全检查 ===
    
    # 1. Turnstile 验证
    await verify_turnstile(data.turnstile_token, ip_address)
    
    # 2. IP 频率限制检查
    await check_ip_rate_limit(ip_address, code)
    
    # 3. 提交时间检测，同时获取填写耗时
    fill_duration = check_submit_time(data.start_time)
    
    # === 业务逻辑验证 ===

    
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
    
    # 创建提交（包含填写耗时）
    submission = await SubmissionService.create_submission(
        db, survey, data, ip_address, fill_duration
    )
    
    # 记录 IP 提交（用于频率限制）
    await record_ip_submission(ip_address, code)
    
    return ApiResponse(
        success=True,
        data={
            "id": submission.id,
            "message": "提交成功，请等待审核",
        }
    )


@router.post("/upload", response_model=ApiResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传文件（公开，用于问卷中的图片上传）"""
    # 获取真实 IP 地址并检查上传频率
    ip_address = get_real_ip(request)
    await check_upload_rate_limit(ip_address)
    
    uploaded = await FileService.save_file(db, file)
    
    # 记录上传
    await record_ip_upload(ip_address)
    
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


@router.get("/submissions/query", response_model=ApiResponse)
async def query_submission_status(
    player_name: Optional[str] = Query(None, min_length=1, max_length=64, description="游戏名称"),
    qq: Optional[str] = Query(None, min_length=5, max_length=15, description="QQ号"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询问卷提交状态（公开接口）
    
    根据游戏名或 QQ 号查询问卷状态，返回审核进度时间线：
    - 提交时间
    - 管理员首次查看时间
    - 审核通过/拒绝时间
    - 是否已加入白名单（如果通过）
    """
    if not player_name and not qq:
        raise HTTPException(
            status_code=400, 
            detail="请提供游戏名称或QQ号进行查询"
        )
    
    # 查询提交记录
    submissions = await SubmissionService.query_submissions_public(
        db, player_name=player_name, qq=qq
    )
    
    if not submissions:
        raise HTTPException(
            status_code=404, 
            detail="未找到相关的问卷提交记录"
        )
    
    # 构建返回数据
    results = []
    for sub in submissions:
        # 计算状态文本
        status_text = {
            "pending": "待审核",
            "approved": "已通过",
            "rejected": "未通过",
        }.get(sub.status, "未知")
        
        results.append({
            "id": sub.id,
            "player_name": sub.player_name,
            "status": sub.status,
            "status_text": status_text,
            # 时间线
            "timeline": {
                "submitted_at": sub.created_at.isoformat() if sub.created_at else None,
                "first_viewed_at": sub.first_viewed_at.isoformat() if sub.first_viewed_at else None,
                "reviewed_at": sub.reviewed_at.isoformat() if sub.reviewed_at else None,
            },
            # 填写耗时（格式化为分:秒）
            "fill_duration": _format_duration(sub.fill_duration) if sub.fill_duration else None,
            # 审核备注（仅在被拒绝时显示）
            "review_note": sub.review_note if sub.status == "rejected" else None,
            # 问卷标题
            "survey_title": sub.survey.title if sub.survey else None,
        })
    
    return ApiResponse(
        success=True,
        data={
            "count": len(results),
            "submissions": results,
        }
    )


def _format_duration(seconds: float) -> str:
    """格式化填写耗时"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}分{secs}秒"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}小时{mins}分"
