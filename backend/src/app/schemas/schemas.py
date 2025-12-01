from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator


# ==================== 通用响应 ====================

class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list
    page: int
    size: int
    total: int
    pages: int


# ==================== 问题相关 ====================

class QuestionOptionSchema(BaseModel):
    """题目选项"""
    value: str
    label: str


class QuestionValidationSchema(BaseModel):
    """题目验证规则"""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    max_images: Optional[int] = None


class QuestionCreate(BaseModel):
    """创建问题"""
    title: str = Field(..., min_length=1, max_length=1000)
    description: Optional[str] = None
    type: str = Field(..., pattern="^(single|multiple|boolean|text|image)$")
    options: Optional[list[QuestionOptionSchema]] = None
    is_required: bool = True
    order: int = 0
    validation: Optional[QuestionValidationSchema] = None


class QuestionUpdate(BaseModel):
    """更新问题"""
    title: Optional[str] = Field(None, min_length=1, max_length=1000)
    description: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(single|multiple|boolean|text|image)$")
    options: Optional[list[QuestionOptionSchema]] = None
    is_required: Optional[bool] = None
    order: Optional[int] = None
    validation: Optional[QuestionValidationSchema] = None


class QuestionResponse(BaseModel):
    """问题响应"""
    id: int
    title: str
    description: Optional[str]
    type: str
    options: Optional[list[QuestionOptionSchema]]
    is_required: bool
    order: int
    validation: Optional[QuestionValidationSchema]
    
    class Config:
        from_attributes = True


# ==================== 问卷相关 ====================

class SurveyCreate(BaseModel):
    """创建问卷"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_random: bool = False
    random_count: Optional[int] = Field(None, ge=1)
    questions: list[QuestionCreate] = []


class SurveyUpdate(BaseModel):
    """更新问卷"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_random: Optional[bool] = None
    random_count: Optional[int] = Field(None, ge=1)


class SurveyResponse(BaseModel):
    """问卷响应（列表）"""
    id: int
    title: str
    description: Optional[str]
    code: str
    is_active: bool
    is_random: bool
    random_count: Optional[int]
    question_count: int = 0
    submission_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SurveyDetailResponse(BaseModel):
    """问卷详情响应"""
    id: int
    title: str
    description: Optional[str]
    code: str
    is_active: bool
    is_random: bool
    random_count: Optional[int]
    questions: list[QuestionResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 公开问卷（玩家端）====================

class PublicSurveyResponse(BaseModel):
    """公开问卷响应（给玩家看的）"""
    title: str
    description: Optional[str]
    questions: list[QuestionResponse]


# ==================== 提交相关 ====================

class AnswerSubmit(BaseModel):
    """提交答案"""
    question_id: int
    content: dict  # 根据题型不同，格式不同


class SubmissionCreate(BaseModel):
    """创建提交"""
    player_name: str = Field(..., min_length=1, max_length=64)
    answers: list[AnswerSubmit]
    # 安全相关字段
    turnstile_token: Optional[str] = None  # Cloudflare Turnstile token
    start_time: Optional[float] = None  # 开始填写时间戳（秒）
    
    @field_validator('player_name')
    @classmethod
    def sanitize_player_name(cls, v: str) -> str:
        """清理玩家名称中的潜在恶意字符"""
        # 移除 HTML 标签和脚本
        v = re.sub(r'<[^>]*>', '', v)
        # 移除 JavaScript 事件处理器
        v = re.sub(r'on\w+\s*=', '', v, flags=re.IGNORECASE)
        # 移除潜在的 SQL 注入字符（基础防护，SQLAlchemy 已有参数化查询）
        v = v.replace(';', '').replace('--', '')
        return v.strip()


class AnswerResponse(BaseModel):
    """答案响应"""
    id: int
    question_id: int
    question_title: str = ""
    question_type: str = ""
    content: dict
    
    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    """提交列表响应"""
    id: int
    survey_id: int
    survey_title: str = ""
    player_name: str
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SubmissionDetailResponse(BaseModel):
    """提交详情响应"""
    id: int
    survey_id: int
    survey_title: str = ""
    player_name: str
    ip_address: Optional[str]
    status: str
    review_note: Optional[str]
    answers: list[AnswerResponse]
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]
    
    class Config:
        from_attributes = True


class SubmissionReview(BaseModel):
    """审核提交"""
    status: str = Field(..., pattern="^(approved|rejected)$")
    review_note: Optional[str] = None


# ==================== 文件上传 ====================

class UploadResponse(BaseModel):
    """文件上传响应"""
    filename: str
    stored_name: str
    url: str
    size: int
    mime_type: str
