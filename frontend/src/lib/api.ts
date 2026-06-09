import axios, { AxiosError } from 'axios'
import type {
  ApiResponse,
  PublicSurvey,
  SubmissionCreate,
  SecurityConfig,
  UploadResponse,
  SubmissionQueryResponse,
} from '@/types/survey'

// 问卷后端基址。生产留空 -> 同源相对 (/api/v1, /uploads); 开发用 .env 的 VITE_API_URL 指向 localhost:8000。
const API_BASE = import.meta.env.VITE_API_URL || ''

const http = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 20000,
})

// 把后端错误统一转成带可读 message 的 Error 抛出:
// - HTTPException 走 FastAPI 默认格式 { detail }
// - 业务包装失败走 ApiResponse 的 error.message
function toError(err: unknown, fallback: string): Error {
  if (err instanceof AxiosError) {
    const body = err.response?.data as { detail?: string; error?: { message?: string } } | undefined
    const msg = body?.detail || body?.error?.message
    if (msg) return new Error(msg)
  }
  if (err instanceof Error) return err
  return new Error(fallback)
}

// 解包 ApiResponse; success=false 或 data 缺失也视为失败抛错, 不静默吞
function unwrap<T>(resp: ApiResponse<T>, fallback: string): T {
  if (!resp.success || resp.data === undefined) {
    throw new Error(resp.error?.message || fallback)
  }
  return resp.data
}

export async function getSurveyByCode(code: string): Promise<PublicSurvey> {
  try {
    const { data } = await http.get<ApiResponse<PublicSurvey>>(`/public/surveys/${encodeURIComponent(code)}`)
    return unwrap(data, '问卷不存在或已关闭')
  } catch (err) {
    throw toError(err, '问卷不存在或已关闭')
  }
}

export async function getActiveSurvey(): Promise<PublicSurvey> {
  try {
    const { data } = await http.get<ApiResponse<PublicSurvey>>('/public/survey/active')
    return unwrap(data, '当前没有可用的问卷')
  } catch (err) {
    throw toError(err, '当前没有可用的问卷')
  }
}

export async function submitSurvey(
  code: string,
  payload: SubmissionCreate,
): Promise<{ id: number; message: string }> {
  try {
    const { data } = await http.post<ApiResponse<{ id: number; message: string }>>(
      `/public/surveys/${encodeURIComponent(code)}/submit`,
      payload,
    )
    return unwrap(data, '提交失败，请稍后重试')
  } catch (err) {
    throw toError(err, '提交失败，请稍后重试')
  }
}

export async function getSecurityConfig(): Promise<SecurityConfig> {
  try {
    const { data } = await http.get<ApiResponse<SecurityConfig>>('/public/security-config')
    return unwrap(data, '获取安全配置失败')
  } catch (err) {
    throw toError(err, '获取安全配置失败')
  }
}

export async function querySubmissionStatus(playerName: string): Promise<SubmissionQueryResponse> {
  try {
    const { data } = await http.get<ApiResponse<SubmissionQueryResponse>>('/public/submissions/query', {
      params: { player_name: playerName },
    })
    return unwrap(data, '未找到相关的问卷提交记录')
  } catch (err) {
    throw toError(err, '未找到相关的问卷提交记录')
  }
}

export async function uploadImage(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  try {
    const { data } = await http.post<ApiResponse<UploadResponse>>('/public/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return unwrap(data, '上传失败，请重试')
  } catch (err) {
    throw toError(err, '上传失败，请重试')
  }
}

// 后端返回的图片地址为相对路径 (/uploads/xxx), 拼成可直接用于 img src 的完整地址。
// 已是绝对 http(s) 地址则原样返回。
export function getImageUrl(url: string): string {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  return `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`
}
