import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import { ThemeProvider } from '@/providers/ThemeProvider'
import { Layout } from '@/components/Layout'
import { HomePage } from '@/pages/HomePage'
import { SurveyPage } from '@/pages/SurveyPage'

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
