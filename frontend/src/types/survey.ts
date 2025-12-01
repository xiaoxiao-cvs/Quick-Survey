// 问题选项
export interface QuestionOption {
  value: string
  label: string
}

// 问题验证规则
export interface QuestionValidation {
  min_length?: number
  max_length?: number
  max_images?: number
}

// 问题类型
export type QuestionType = 'single' | 'multiple' | 'boolean' | 'text' | 'image'

// 问题
export interface Question {
  id: number
  title: string
  description?: string
  type: QuestionType
  options?: QuestionOption[]
  is_required: boolean
  validation?: QuestionValidation
}

// 公开问卷响应
export interface PublicSurvey {
  code: string
  title: string
  description?: string
  questions: Question[]
}

// 答案提交
export interface AnswerSubmit {
  question_id: number
  content: {
    value?: string | boolean // 单选、判断
    values?: string[] // 多选
    text?: string // 简答
    images?: string[] // 图片上传
  }
}

// 提交请求
export interface SubmissionCreate {
  player_name: string
  answers: AnswerSubmit[]
}

// API 响应
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
  }
}

// 上传响应
export interface UploadResponse {
  filename: string
  stored_name: string
  url: string
  size: number
  mime_type: string
}
