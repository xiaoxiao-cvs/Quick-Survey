import secrets
import random
from typing import Optional
from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Survey, Question, Submission, Answer
from app.schemas import (
    SurveyCreate, SurveyUpdate, QuestionCreate, QuestionUpdate,
    SubmissionCreate, SubmissionReview
)


def generate_code(length: int = 8) -> str:
    """生成随机访问码"""
    return secrets.token_urlsafe(length)[:length]


class SurveyService:
    """问卷服务"""
    
    @staticmethod
    async def create_survey(
        db: AsyncSession, 
        data: SurveyCreate, 
        created_by: Optional[int] = None
    ) -> Survey:
        """创建问卷"""
        survey = Survey(
            title=data.title,
            description=data.description,
            code=generate_code(),
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
    async def get_surveys(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
    ) -> tuple[list[Survey], int]:
        """获取问卷列表"""
        query = select(Survey)
        count_query = select(func.count(Survey.id))
        
        if search:
            query = query.where(Survey.title.contains(search))
            count_query = count_query.where(Survey.title.contains(search))
        
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
    async def update_survey(
        db: AsyncSession, 
        survey: Survey, 
        data: SurveyUpdate
    ) -> Survey:
        """更新问卷"""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(survey, field, value)
        
        survey.updated_at = datetime.utcnow()
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
            order=data.order,
            validation=data.validation.model_dump() if data.validation else None,
        )
        db.add(question)
        await db.commit()
        await db.refresh(question)
        return question
    
    @staticmethod
    async def get_question_by_id(db: AsyncSession, question_id: int) -> Optional[Question]:
        """通过 ID 获取问题"""
        result = await db.execute(
            select(Question).where(Question.id == question_id)
        )
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
        
        for field, value in update_data.items():
            setattr(question, field, value)
        
        await db.commit()
        await db.refresh(question)
        return question
    
    @staticmethod
    async def delete_question(db: AsyncSession, question: Question) -> None:
        """删除问题"""
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
    ) -> Submission:
        """创建提交"""
        submission = Submission(
            survey_id=survey.id,
            player_name=data.player_name,
            ip_address=ip_address,
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
    async def get_submission_by_id(db: AsyncSession, submission_id: int) -> Optional[Submission]:
        """通过 ID 获取提交"""
        result = await db.execute(
            select(Submission)
            .options(
                selectinload(Submission.answers),
                selectinload(Submission.survey),
            )
            .where(Submission.id == submission_id)
        )
        return result.scalar_one_or_none()
    
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
        submission.reviewed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(submission)
        return submission
    
    @staticmethod
    async def get_random_questions(survey: Survey) -> list[Question]:
        """获取随机题目（用于随机题库）"""
        questions = list(survey.questions)
        
        if survey.is_random and survey.random_count:
            count = min(survey.random_count, len(questions))
            questions = random.sample(questions, count)
        
        return sorted(questions, key=lambda q: q.order)
