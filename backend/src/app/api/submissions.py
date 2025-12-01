from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.core import get_current_user, CurrentUser
from app.schemas import ApiResponse, SubmissionReview
from app.services import SubmissionService, SurveyService, CleanupService
from app.models import Question


router = APIRouter(prefix="/submissions", tags=["提交管理"])


# 注意：stats 路由必须放在 /{submission_id} 之前，避免路由冲突
@router.post("/cleanup", response_model=ApiResponse)
async def run_cleanup(
    user: CurrentUser = Depends(get_current_user),
):
    """
    手动触发清理任务
    清理已审核提交的答案数据和图片文件，保留提交记录元数据
    """
    stats = await CleanupService.run_cleanup()
    
    # 格式化释放的空间
    bytes_freed = stats["bytes_freed"]
    if bytes_freed >= 1024 * 1024:
        freed_str = f"{bytes_freed / (1024 * 1024):.2f} MB"
    elif bytes_freed >= 1024:
        freed_str = f"{bytes_freed / 1024:.2f} KB"
    else:
        freed_str = f"{bytes_freed} bytes"
    
    return ApiResponse(
        success=True,
        data={
            "submissions_cleaned": stats["submissions_cleaned"],
            "answers_deleted": stats["answers_deleted"],
            "files_deleted": stats["files_deleted"],
            "orphan_files_deleted": stats["orphan_files_deleted"],
            "space_freed": freed_str,
        },
        message=f"清理完成，释放空间: {freed_str}"
    )


@router.get("/stats/overview", response_model=ApiResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """获取统计概览"""
    _, pending_count = await SubmissionService.get_submissions(db, 1, 1, "pending")
    _, approved_count = await SubmissionService.get_submissions(db, 1, 1, "approved")
    _, rejected_count = await SubmissionService.get_submissions(db, 1, 1, "rejected")
    
    return ApiResponse(
        success=True,
        data={
            "pending": pending_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "total": pending_count + approved_count + rejected_count,
        }
    )


@router.get("", response_model=ApiResponse)
async def get_submissions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(pending|approved|rejected)$"),
    survey_id: Optional[int] = None,
    player_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """获取提交列表（审核列表）"""
    submissions, total = await SubmissionService.get_submissions(
        db, page, size, status, survey_id, player_name
    )
    
    items = []
    for sub in submissions:
        items.append({
            "id": sub.id,
            "survey_id": sub.survey_id,
            "survey_title": sub.survey.title if sub.survey else "",
            "player_name": sub.player_name,
            "status": sub.status,
            "created_at": sub.created_at.isoformat(),
            "reviewed_at": sub.reviewed_at.isoformat() if sub.reviewed_at else None,
        })
    
    return ApiResponse(
        success=True,
        data={
            "items": items,
            "page": page,
            "size": size,
            "total": total,
            "pages": (total + size - 1) // size,
        }
    )


@router.get("/{submission_id}", response_model=ApiResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """获取提交详情"""
    # 获取提交并标记首次查看时间
    submission = await SubmissionService.get_submission_by_id(db, submission_id, mark_viewed=True)
    if not submission:
        raise HTTPException(status_code=404, detail="提交不存在")
    
    # 获取问卷以获取问题信息
    survey = await SurveyService.get_survey_by_id(db, submission.survey_id)
    questions_map = {q.id: q for q in survey.questions} if survey else {}
    
    answers = []
    for answer in submission.answers:
        question = questions_map.get(answer.question_id)
        answers.append({
            "id": answer.id,
            "question_id": answer.question_id,
            "question_title": question.title if question else "",
            "question_type": question.type if question else "",
            "content": answer.content,
        })
    
    return ApiResponse(
        success=True,
        data={
            "id": submission.id,
            "survey_id": submission.survey_id,
            "survey_title": submission.survey.title if submission.survey else "",
            "player_name": submission.player_name,
            "ip_address": submission.ip_address,
            "fill_duration": submission.fill_duration,  # 填写耗时
            "first_viewed_at": submission.first_viewed_at.isoformat() if submission.first_viewed_at else None,  # 首次查看时间
            "status": submission.status,
            "review_note": submission.review_note,
            "answers": answers,
            "created_at": submission.created_at.isoformat(),
            "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
            "reviewed_by": submission.reviewed_by,
        }
    )


@router.patch("/{submission_id}/review", response_model=ApiResponse)
async def review_submission(
    submission_id: int,
    data: SubmissionReview,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """审核提交"""
    submission = await SubmissionService.get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="提交不存在")
    
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="该提交已被审核")
    
    submission = await SubmissionService.review_submission(db, submission, data, user.id)
    
    return ApiResponse(
        success=True,
        data={
            "id": submission.id,
            "status": submission.status,
            "message": "审核成功",
        }
    )
