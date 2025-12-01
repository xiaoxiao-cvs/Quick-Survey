import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { FileText, ArrowRight, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getActiveSurvey } from '@/lib/api'
import { toast } from 'sonner'

export function HomePage() {
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(true)
  const [surveyInfo, setSurveyInfo] = useState<{ code: string; title: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  // 检查是否有可用问卷
  useEffect(() => {
    const checkActiveSurvey = async () => {
      try {
        setChecking(true)
        const data = await getActiveSurvey()
        setSurveyInfo({ code: data.code, title: data.title })
        setError(null)
      } catch {
        setError('当前没有可用的问卷')
        setSurveyInfo(null)
      } finally {
        setChecking(false)
      }
    }
    checkActiveSurvey()
  }, [])

  const handleEnterSurvey = async () => {
    if (!surveyInfo) {
      toast.error('当前没有可用的问卷')
      return
    }

    setLoading(true)
    try {
      navigate(`/survey/${surveyInfo.code}`)
    } catch {
      toast.error('进入问卷失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 40, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ 
          duration: 0.6, 
          ease: [0.25, 0.46, 0.45, 0.94],
          delay: 0.1 
        }}
        className="w-full max-w-md"
      >
        <Card className="rounded-3xl border-border/50 shadow-xl bg-card/80 backdrop-blur-sm overflow-hidden">
          {/* 装饰性渐变背景 */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/10 pointer-events-none" />
          
          <CardHeader className="relative text-center pb-2 pt-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ 
                type: 'spring', 
                damping: 15, 
                stiffness: 200,
                delay: 0.3 
              }}
              className="mx-auto mb-4 w-16 h-16 rounded-3xl bg-primary/10 flex items-center justify-center"
            >
              <FileText className="w-8 h-8 text-primary" />
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.4 }}
            >
              <CardTitle className="text-2xl font-bold">开始填写问卷</CardTitle>
              <CardDescription className="mt-2 text-base">
                {checking ? '正在检查问卷...' : surveyInfo ? surveyInfo.title : '暂无可用问卷'}
              </CardDescription>
            </motion.div>
          </CardHeader>

          <CardContent className="relative pt-4 pb-8 px-8">
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.4 }}
              >
                {checking ? (
                  <div className="h-14 flex items-center justify-center">
                    <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                  </div>
                ) : error ? (
                  <div className="h-14 flex items-center justify-center gap-2 text-muted-foreground">
                    <AlertCircle className="w-5 h-5" />
                    <span>{error}</span>
                  </div>
                ) : (
                  <div className="h-14 flex items-center justify-center text-muted-foreground">
                    <span>点击下方按钮开始填写</span>
                  </div>
                )}
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 0.4 }}
              >
                <Button
                  type="button"
                  size="lg"
                  className="w-full h-14 text-lg font-medium rounded-2xl transition-all duration-300"
                  disabled={loading || checking || !surveyInfo}
                  onClick={handleEnterSurvey}
                >
                  <AnimatePresence mode="wait">
                    {loading || checking ? (
                      <motion.div
                        key="loading"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="flex items-center gap-2"
                      >
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>{checking ? '检查中...' : '加载中...'}</span>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="submit"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="flex items-center gap-2"
                      >
                        <span>进入问卷</span>
                        <ArrowRight className="w-5 h-5" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Button>
              </motion.div>
            </div>
          </CardContent>
        </Card>

        {/* 底部装饰 */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.4 }}
          className="text-center text-sm text-muted-foreground mt-6"
        >
          问卷由管理员配置
        </motion.p>
      </motion.div>
    </div>
  )
}
