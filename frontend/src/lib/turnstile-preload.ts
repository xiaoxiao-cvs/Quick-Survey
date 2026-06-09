// Cloudflare Turnstile 脚本预加载。
// App 启动时 preloadTurnstile() 注入一次脚本; Turnstile 组件挂载时 waitForTurnstile() 等待
// window.turnstile 就绪后再 render。脚本仅注入一次, 后续调用复用同一 Promise。

const TURNSTILE_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'

type TurnstileGlobal = { turnstile?: unknown }

let loadPromise: Promise<void> | null = null

function isReady(): boolean {
  return typeof (window as Window & TurnstileGlobal).turnstile !== 'undefined'
}

export function preloadTurnstile(): Promise<void> {
  if (loadPromise) return loadPromise

  loadPromise = new Promise<void>((resolve, reject) => {
    if (typeof window === 'undefined' || typeof document === 'undefined') {
      reject(new Error('当前环境无 window/document, 无法加载 Turnstile'))
      return
    }
    if (isReady()) {
      resolve()
      return
    }

    // 脚本 onload 后 window.turnstile 可能晚一拍挂载, 轮询确认就绪 (最长 10s)
    const waitReady = () => {
      const start = Date.now()
      const tick = () => {
        if (isReady()) {
          resolve()
        } else if (Date.now() - start > 10000) {
          reject(new Error('Turnstile 加载超时'))
        } else {
          window.setTimeout(tick, 50)
        }
      }
      tick()
    }

    const srcPrefix = TURNSTILE_SRC.split('?')[0]
    const existing = document.querySelector<HTMLScriptElement>(`script[src^="${srcPrefix}"]`)
    if (existing) {
      if (isReady()) {
        resolve()
      } else {
        existing.addEventListener('load', waitReady, { once: true })
        existing.addEventListener('error', () => reject(new Error('Turnstile 脚本加载失败')), { once: true })
      }
      return
    }

    const script = document.createElement('script')
    script.src = TURNSTILE_SRC
    script.async = true
    script.defer = true
    script.addEventListener('load', waitReady, { once: true })
    script.addEventListener('error', () => reject(new Error('Turnstile 脚本加载失败')), { once: true })
    document.head.appendChild(script)
  })

  // App.tsx 以 fire-and-forget 方式调用本函数, 这里吞掉一次拒绝避免 unhandledrejection;
  // waitForTurnstile 的调用方仍能拿到原 Promise 的拒绝并自行处理。
  loadPromise.catch(() => {})

  return loadPromise
}

export function waitForTurnstile(): Promise<void> {
  return loadPromise ?? preloadTurnstile()
}
