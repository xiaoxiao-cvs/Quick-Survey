/// <reference types="vite/client" />

interface ImportMetaEnv {
  // 问卷后端基址: 留空则用同源相对路径 (/api/v1, /uploads); 开发时指向 http://localhost:8000
  readonly VITE_API_URL?: string
  // Cloudflare Turnstile sitekey (后端启用 turnstile 时才需要)
  readonly VITE_TURNSTILE_SITE_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
