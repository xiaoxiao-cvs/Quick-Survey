from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    """获取当前 UTC 时间（兼容 Python 3.12+）"""
    return datetime.now(timezone.utc)


class Survey(Base):
    """问卷模板"""
    __tablename__ = "surveys"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 基本信息
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)  # 访问短码
    
    # 配置
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否启用
    is_random: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否随机题目
    random_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 随机抽取题目数量
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 创建者 admin_id
    
    # 关系
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="survey", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="survey")


class Question(Base):
    """问题"""
    __tablename__ = "questions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False)
    
    # 题目内容
    title: Mapped[str] = mapped_column(Text, nullable=False)  # 题目标题
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 题目描述
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 类型: single, multiple, boolean, text, image
    
    # 选项 (JSON 数组，用于单选/多选题)
    # 格式: [{"value": "A", "label": "选项A"}, ...]
    options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 配置
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否必填
    order: Mapped[int] = mapped_column(Integer, default=0)  # 排序
    
    # 验证规则 (JSON)
    # 格式: {"min_length": 10, "max_length": 500, "max_images": 3}
    validation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # 关系
    survey: Mapped["Survey"] = relationship("Survey", back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="question")


class Submission(Base):
    """问卷提交"""
    __tablename__ = "submissions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey("surveys.id"), nullable=False)
    
    # 提交者信息
    player_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 玩家名
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IP地址
    
    # 时间记录
    fill_duration: Mapped[Optional[float]] = mapped_column(nullable=True)  # 填写耗时（秒）
    first_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 管理界面首次查看时间
    
    # 审核状态
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 审核时间
    reviewed_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 审核者 admin_id
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 审核备注
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)  # 提交时间
    
    # 关系
    survey: Mapped["Survey"] = relationship("Survey", back_populates="submissions")
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="submission", cascade="all, delete-orphan")


class Answer(Base):
    """回答"""
    __tablename__ = "answers"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    
    # 回答内容 (JSON)
    # 单选: {"value": "A"}
    # 多选: {"values": ["A", "B"]}
    # 判断: {"value": true}
    # 文本: {"text": "..."}
    # 图片: {"images": ["upload/xxx.jpg", ...]}
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # 关系
    submission: Mapped["Submission"] = relationship("Submission", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")


class UploadedFile(Base):
    """上传的文件"""
    __tablename__ = "uploaded_files"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 文件信息
    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # 原始文件名
    stored_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # 存储文件名
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)  # 存储路径
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # 文件大小 (bytes)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)  # MIME 类型
    
    # 关联
    submission_id: Mapped[Optional[int]] = mapped_column(ForeignKey("submissions.id"), nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
