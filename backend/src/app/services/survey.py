import secrets
import random
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, delete, String, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Survey, Question, Submission, Answer
from app.schemas import (
    SurveyCreate, SurveyUpdate, QuestionCreate, QuestionUpdate,
    SubmissionCreate, SubmissionReview
)


class SurveyService:
    """问卷服务"""
    
    @staticmethod
    async def create_survey(
        db: AsyncSession, 
        data: SurveyCreate, 
        created_by: Optional[int] = None
    ) -> Survey:
        """创建问卷"""
        # 使用问卷标题生成简单的访问码
        code = secrets.token_urlsafe(8)[:8]
        survey = Survey(
            title=data.title,
            description=data.description,
            code=code,
            is_random=data.is_random,
            random_count=data.random_count,
            created_by=created_by,
        )
        
        # 添加问题
        for i, q_data in enumerate(data.questions):
            question = Question(
                title=q_data.title,
                description=q_data.description,
                type=q_data.type,
                options=[opt.model_dump() for opt in q_data.options] if q_data.options else None,
                is_required=q_data.is_required,
                order=q_data.order if q_data.order else i,
                validation=q_data.validation.model_dump() if q_data.validation else None,
            )
            survey.questions.append(question)
        
        db.add(survey)
        await db.commit()
        await db.refresh(survey)
        return survey
    
    @staticmethod
    async def get_survey_by_id(db: AsyncSession, survey_id: int) -> Optional[Survey]:
        """通过 ID 获取问卷"""
        result = await db.execute(
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(Survey.id == survey_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_survey_by_code(db: AsyncSession, code: str) -> Optional[Survey]:
        """通过访问码获取问卷"""
        result = await db.execute(
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(Survey.code == code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_survey(db: AsyncSession) -> Optional[Survey]:
        """获取当前激活的问卷（返回第一个激活的问卷）"""
        result = await db.execute(
            select(Survey)
            .options(selectinload(Survey.questions))
            .where(Survey.is_active == True)
            .order_by(Survey.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_surveys(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Survey], int]:
        """获取问卷列表"""
        query = select(Survey)
        count_query = select(func.count(Survey.id))
        
        if search:
            query = query.where(Survey.title.contains(search))
            count_query = count_query.where(Survey.title.contains(search))
        
        if is_active is not None:
            query = query.where(Survey.is_active == is_active)
            count_query = count_query.where(Survey.is_active == is_active)
        
        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        query = query.order_by(Survey.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await db.execute(query)
        surveys = result.scalars().all()
        
        return list(surveys), total
    
    @staticmethod
    async def get_survey_stats(db: AsyncSession) -> dict:
        """获取问卷统计"""
        # 启用中的问卷数
        active_result = await db.execute(
            select(func.count(Survey.id)).where(Survey.is_active == True)
        )
        active = active_result.scalar() or 0
        
        # 已停用的问卷数
        inactive_result = await db.execute(
            select(func.count(Survey.id)).where(Survey.is_active == False)
        )
        inactive = inactive_result.scalar() or 0
        
        return {
            "active": active,
            "inactive": inactive,
            "total": active + inactive,
        }
    
    @staticmethod
    async def update_survey(
        db: AsyncSession, 
        survey: Survey, 
        data: SurveyUpdate
    ) -> Survey:
        """更新问卷"""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(survey, field, value)
        
        survey.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(survey)
        return survey
    
    @staticmethod
    async def delete_survey(db: AsyncSession, survey: Survey) -> None:
        """删除问卷"""
        await db.delete(survey)
        await db.commit()
    
    @staticmethod
    async def get_question_count(db: AsyncSession, survey_id: int) -> int:
        """获取问卷的问题数量"""
        result = await db.execute(
            select(func.count(Question.id)).where(Question.survey_id == survey_id)
        )
        return result.scalar() or 0
    
    @staticmethod
    async def get_submission_count(db: AsyncSession, survey_id: int) -> int:
        """获取问卷的提交数量"""
        result = await db.execute(
            select(func.count(Submission.id)).where(Submission.survey_id == survey_id)
        )
        return result.scalar() or 0


class QuestionService:
    """问题服务"""
    
    @staticmethod
    async def add_question(
        db: AsyncSession, 
        survey_id: int, 
        data: QuestionCreate
    ) -> Question:
        """添加问题"""
        question = Question(
            survey_id=survey_id,
            title=data.title,
            description=data.description,
            type=data.type,
            options=[opt.model_dump() for opt in data.options] if data.options else None,
            is_required=data.is_required,
            is_pinned=data.is_pinned,
            order=data.order,
            validation=data.validation.model_dump() if data.validation else None,
            condition=data.condition.model_dump() if data.condition else None,
        )
        db.add(question)
        await db.commit()
        await db.refresh(question)
        return question
    
    @staticmethod
    async def get_question_by_id(db: AsyncSession, question_id: int, load_answers: bool = False) -> Optional[Question]:
        """通过 ID 获取问题"""
        query = select(Question).where(Question.id == question_id)
        if load_answers:
            query = query.options(selectinload(Question.answers))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_question(
        db: AsyncSession, 
        question: Question, 
        data: QuestionUpdate
    ) -> Question:
        """更新问题"""
        update_data = data.model_dump(exclude_unset=True)
        
        if "options" in update_data and update_data["options"]:
            update_data["options"] = [opt.model_dump() for opt in data.options]
        if "validation" in update_data and update_data["validation"]:
            update_data["validation"] = data.validation.model_dump()
        if "condition" in update_data and update_data["condition"]:
            update_data["condition"] = data.condition.model_dump()
        
        for field, value in update_data.items():
            setattr(question, field, value)
        
        await db.commit()
        await db.refresh(question)
        return question
    
    @staticmethod
    async def delete_question(db: AsyncSession, question: Question) -> None:
        """删除问题"""
        # 先删除关联的答案（因为 SQLite 外键约束可能未启用）
        for answer in question.answers:
            await db.delete(answer)
        await db.delete(question)
        await db.commit()


class SubmissionService:
    """提交服务"""
    
    @staticmethod
    async def create_submission(
        db: AsyncSession,
        survey: Survey,
        data: SubmissionCreate,
        ip_address: Optional[str] = None,
        fill_duration: Optional[float] = None,
    ) -> Submission:
        """创建提交"""
        submission = Submission(
            survey_id=survey.id,
            player_name=data.player_name,
            ip_address=ip_address,
            fill_duration=fill_duration,
            status="pending",
        )
        
        # 添加答案
        for answer_data in data.answers:
            answer = Answer(
                question_id=answer_data.question_id,
                content=answer_data.content,
            )
            submission.answers.append(answer)
        
        db.add(submission)
        await db.commit()
        await db.refresh(submission)
        return submission
    
    @staticmethod
    async def get_submission_by_id(
        db: AsyncSession, 
        submission_id: int,
        mark_viewed: bool = False,
    ) -> Optional[Submission]:
        """
        通过 ID 获取提交
        
        Args:
            db: 数据库会话
            submission_id: 提交 ID
            mark_viewed: 是否标记首次查看时间
        """
        result = await db.execute(
            select(Submission)
            .options(
                selectinload(Submission.answers),
                selectinload(Submission.survey),
            )
            .where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        
        # 如果需要标记首次查看时间，且之前未查看过
        if submission and mark_viewed and submission.first_viewed_at is None:
            submission.first_viewed_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(submission)
        
        return submission
    
    @staticmethod
    async def get_submissions(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        survey_id: Optional[int] = None,
        player_name: Optional[str] = None,
    ) -> tuple[list[Submission], int]:
        """获取提交列表"""
        query = select(Submission).options(selectinload(Submission.survey))
        count_query = select(func.count(Submission.id))
        
        if status:
            query = query.where(Submission.status == status)
            count_query = count_query.where(Submission.status == status)
        
        if survey_id:
            query = query.where(Submission.survey_id == survey_id)
            count_query = count_query.where(Submission.survey_id == survey_id)
        
        if player_name:
            query = query.where(Submission.player_name.contains(player_name))
            count_query = count_query.where(Submission.player_name.contains(player_name))
        
        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        query = query.order_by(Submission.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await db.execute(query)
        submissions = result.scalars().all()
        
        return list(submissions), total
    
    @staticmethod
    async def review_submission(
        db: AsyncSession,
        submission: Submission,
        data: SubmissionReview,
        reviewed_by: int,
    ) -> Submission:
        """审核提交"""
        submission.status = data.status
        submission.review_note = data.review_note
        submission.reviewed_by = reviewed_by
        submission.reviewed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(submission)
        return submission
    
    @staticmethod
    async def get_random_questions(survey: Survey) -> list[Question]:
        """获取随机题目（用于随机题库）
        
        随机抽题逻辑：
        1. 保留题目（is_pinned=True）始终出现
        2. 从非保留题目中随机抽取，使总数达到 random_count
        """
        questions = list(survey.questions)
        
        if survey.is_random and survey.random_count:
            # 分离保留题目和普通题目
            pinned = [q for q in questions if q.is_pinned]
            unpinned = [q for q in questions if not q.is_pinned]
            
            # 计算需要从普通题目中抽取的数量
            remaining_count = max(0, survey.random_count - len(pinned))
            remaining_count = min(remaining_count, len(unpinned))
            
            # 随机抽取普通题目
            selected_unpinned = random.sample(unpinned, remaining_count) if remaining_count > 0 else []
            
            # 合并保留题目和随机抽取的题目
            questions = pinned + selected_unpinned
        
        return sorted(questions, key=lambda q: q.order)
    
    @staticmethod
    async def query_submissions_public(
        db: AsyncSession,
        player_name: Optional[str] = None,
        qq: Optional[str] = None,
        limit: int = 10,
    ) -> list[Submission]:
        """
        公开查询提交记录（用于玩家查询自己的问卷状态）
        
        Args:
            db: 数据库会话
            player_name: 游戏名称（精确匹配）
            qq: QQ号（在答案中搜索）
            limit: 最大返回数量
        
        Returns:
            匹配的提交记录列表
        """
        results = []
        
        # 1. 按玩家名精确匹配
        if player_name:
            query = (
                select(Submission)
                .options(selectinload(Submission.survey))
                .where(Submission.player_name == player_name)
                .order_by(Submission.created_at.desc())
                .limit(limit)
            )
            result = await db.execute(query)
            results.extend(result.scalars().all())
        
        # 2. 按 QQ 号在答案中搜索（SQLite JSON 查询）
        if qq and len(results) < limit:
            # 在答案的 content 字段中搜索包含 QQ 号的记录
            # content 格式可能是 {"text": "123456789"} 或 {"value": "123456789"}
            remaining = limit - len(results)
            existing_ids = {s.id for s in results}
            
            # 使用 LIKE 在 JSON 字段中搜索（SQLite 兼容）
            query = (
                select(Submission)
                .options(selectinload(Submission.survey))
                .join(Answer, Answer.submission_id == Submission.id)
                .where(
                    and_(
                        Answer.content.cast(String).contains(qq),
                        Submission.id.notin_(existing_ids) if existing_ids else True
                    )
                )
                .distinct()
                .order_by(Submission.created_at.desc())
                .limit(remaining)
            )
            result = await db.execute(query)
            results.extend(result.scalars().all())
        
        return results
