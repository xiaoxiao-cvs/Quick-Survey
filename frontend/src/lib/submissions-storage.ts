// 本机记住"这个浏览器提交过的问卷 token", 便于玩家回到查询页时自动回填、无需手抄。
//
// 安全定位: 这只是便利层, 不是凭证管理。token 本身才是 bearer 凭证, 存在 localStorage
// 不改变其安全性 (同"玩家自己抄下来")。主要风险是共享/公用电脑会把 token 留给下一个人,
// 故查询页提供"清除本机记录"按钮, 且仍提示玩家自行保存 token (清浏览器数据即丢失本地副本)。
// 用 localStorage 而非 cookie: 服务端无需读它 (查询/领码端点显式收 token 参数),
// cookie 的自动随请求外发只会扩大泄漏面。

const STORAGE_KEY = 'qs_submissions'
// 软过期: 超过此天数的本地记录在读取时清理 (仅本地便利, 不影响服务端数据)
const MAX_AGE_DAYS = 30

export interface StoredSubmission {
  token: string
  surveyTitle: string | null
  savedAt: number // epoch ms
}

function read(): StoredSubmission[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter(
      (item): item is StoredSubmission =>
        item && typeof item.token === 'string' && typeof item.savedAt === 'number',
    )
  } catch {
    return []
  }
}

function write(items: StoredSubmission[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // localStorage 不可用 (隐私模式/禁用) 时静默降级: 便利层失效不影响主流程
  }
}

// 读取本机记住的提交, 顺便清理过期项, 最近保存的在前。
export function getStoredSubmissions(): StoredSubmission[] {
  const cutoff = Date.now() - MAX_AGE_DAYS * 86400 * 1000
  const fresh = read().filter((item) => item.savedAt >= cutoff)
  // 若清理掉了过期项则回写
  if (fresh.length !== read().length) write(fresh)
  return [...fresh].sort((a, b) => b.savedAt - a.savedAt)
}

// 记住一条提交 (按 token 去重, 同 token 更新标题与时间)。
export function saveSubmission(token: string, surveyTitle: string | null): void {
  if (!token) return
  const items = read().filter((item) => item.token !== token)
  items.push({ token, surveyTitle, savedAt: Date.now() })
  write(items)
}

// 清除本机所有记录 (查询页"这不是我/清除本机记录"按钮用)。
export function clearStoredSubmissions(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // 同 write: 静默降级
  }
}
