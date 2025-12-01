import { useEffect, useRef, useCallback, useState } from 'react'
import { waitForTurnstile } from '@/lib/turnstile-preload'

declare global {
  interface Window {
    turnstile?: {
      render: (
        container: string | HTMLElement,
        options: TurnstileOptions
      ) => string
      reset: (widgetId: string) => void
      remove: (widgetId: string) => void
    }
    onTurnstileLoad?: () => void
  }
}

interface TurnstileOptions {
  sitekey: string
  callback?: (token: string) => void
  'error-callback'?: () => void
  'expired-callback'?: () => void
  theme?: 'light' | 'dark' | 'auto'
  size?: 'normal' | 'compact'
  language?: string
  retry?: 'auto' | 'never'
  'retry-interval'?: number
}

interface TurnstileProps {
  siteKey: string
  onVerify: (token: string) => void
  onError?: () => void
  onExpire?: () => void
  theme?: 'light' | 'dark' | 'auto'
  className?: string
}

export function Turnstile({
  siteKey,
  onVerify,
  onError,
  onExpire,
  theme = 'auto',
  className,
}: TurnstileProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetIdRef = useRef<string | null>(null)
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [retryCount, setRetryCount] = useState(0)

  const handleError = useCallback(() => {
    setStatus('error')
    onError?.()
  }, [onError])

  const handleVerify = useCallback((token: string) => {
    setStatus('ready')
    onVerify(token)
  }, [onVerify])

  const renderWidget = useCallback(() => {
    if (!containerRef.current || !window.turnstile) {
      return
    }

    // 清理旧的 widget
    if (widgetIdRef.current) {
      try {
        window.turnstile.remove(widgetIdRef.current)
      } catch {
        // 忽略
      }
      widgetIdRef.current = null
    }

    try {
      setStatus('loading')
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: siteKey,
        callback: handleVerify,
        'error-callback': handleError,
        'expired-callback': () => {
          setStatus('loading')
          onExpire?.()
        },
        theme,
        language: 'zh-cn',
        retry: 'auto',
        'retry-interval': 3000,
      })
    } catch (error) {
      console.error('Turnstile render error:', error)
      setStatus('error')
    }
  }, [siteKey, handleVerify, handleError, onExpire, theme])

  // 手动重试
  const handleRetry = useCallback(() => {
    setRetryCount(c => c + 1)
    if (window.turnstile) {
      renderWidget()
    }
  }, [renderWidget])

  useEffect(() => {
    // 使用预加载模块等待脚本加载完成
    waitForTurnstile()
      .then(() => {
        renderWidget()
      })
      .catch(() => {
        setStatus('error')
      })

    return () => {
      // 清理 widget
      if (widgetIdRef.current && window.turnstile) {
        try {
          window.turnstile.remove(widgetIdRef.current)
        } catch {
          // 忽略清理错误
        }
        widgetIdRef.current = null
      }
    }
  }, [renderWidget, retryCount])

  return (
    <div className={className}>
      <div ref={containerRef} />
      {status === 'loading' && (
        <p className="text-xs text-muted-foreground mt-1">正在等待Cloudflare Turnstile安全验证...</p>
      )}
      {status === 'error' && (
        <div className="mt-2">
          <p className="text-xs text-destructive">验证加载失败</p>
          <button 
            type="button"
            onClick={handleRetry}
            className="text-xs text-primary hover:underline mt-1"
          >
            点击重试
          </button>
        </div>
      )}
    </div>
  )
}

export default Turnstile
