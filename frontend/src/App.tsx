import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import { ThemeProvider } from '@/providers/ThemeProvider'
import { Layout } from '@/components/Layout'
import { HomePage } from '@/pages/HomePage'
import { SurveyPage } from '@/pages/SurveyPage'
import { preloadTurnstile } from '@/lib/turnstile-preload'

// 应用启动时预加载 Turnstile 脚本
// 这样用户进入问卷页面时，验证组件已经准备好了
preloadTurnstile()

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/survey/:code" element={<SurveyPage />} />
          </Routes>
        </Layout>
        <Toaster 
          position="top-center"
          toastOptions={{
            className: 'rounded-2xl',
          }}
        />
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
