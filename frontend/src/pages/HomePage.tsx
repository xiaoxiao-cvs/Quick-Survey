import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { FileText, ArrowRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getSurveyByCode } from '@/lib/api'
import { toast } from 'sonner'

export function HomePage() {
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [shake, setShake] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!code.trim()) {
      setShake(true)
      setTimeout(() => setShake(false), 500)
      toast.error('请输入问卷码')
      return
    }

    setLoading(true)
    try {
      await getSurveyByCode(code.trim())
      navigate(`/survey/${code.trim()}`)
    } catch {
      setShake(true)
      setTimeout(() => setShake(false), 500)
      toast.error('问卷不存在或已关闭')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center">
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
                输入问卷码开始填写
              </CardDescription>
            </motion.div>
          </CardHeader>

          <CardContent className="relative pt-4 pb-8 px-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <motion.div
                animate={shake ? { x: [0, -10, 10, -10, 10, 0] } : {}}
                transition={{ duration: 0.4 }}
              >
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5, duration: 0.4 }}
                >
                  <Input
                    type="text"
                    placeholder="请输入问卷码"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="h-14 text-lg text-center rounded-2xl border-border/50 bg-background/50 focus:ring-2 focus:ring-primary/20 transition-all duration-300"
                    disabled={loading}
                  />
                </motion.div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 0.4 }}
              >
                <Button
                  type="submit"
                  size="lg"
                  className="w-full h-14 text-lg font-medium rounded-2xl transition-all duration-300"
                  disabled={loading}
                >
                  <AnimatePresence mode="wait">
                    {loading ? (
                      <motion.div
                        key="loading"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="flex items-center gap-2"
                      >
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>加载中...</span>
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
            </form>
          </CardContent>
        </Card>

        {/* 底部装饰 */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.4 }}
          className="text-center text-sm text-muted-foreground mt-6"
        >
          请从管理员处获取问卷码
        </motion.p>
      </motion.div>
    </div>
  )
}
