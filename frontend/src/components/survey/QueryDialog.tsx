import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Loader2, AlertCircle, User } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { StatusTimeline } from './StatusTimeline'
import { querySubmissionStatus } from '@/lib/api'
import type { SubmissionStatus } from '@/types/survey'

interface QueryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function QueryDialog({ open, onOpenChange }: QueryDialogProps) {
  const [playerName, setPlayerName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<SubmissionStatus[] | null>(null)

  const handleSearch = useCallback(async () => {
    if (!playerName.trim()) {
      setError('请输入游戏名称')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const data = await querySubmissionStatus(playerName.trim())
      setResults(data.submissions)
    } catch (err) {
      setError(err instanceof Error ? err.message : '查询失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [playerName])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleSearch()
    }
  }

  const handleClose = () => {
    onOpenChange(false)
    // 延迟重置状态，等待动画结束
    setTimeout(() => {
      setPlayerName('')
      setError(null)
      setResults(null)
    }, 200)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent
        className="sm:max-w-md bg-background/95 backdrop-blur-xl border-border/50 rounded-2xl"
        showCloseButton={true}
      >
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold flex items-center gap-2">
            <Search className="w-5 h-5 text-primary" />
            查询进度
          </DialogTitle>
          <DialogDescription>
            输入您的游戏名称查询问卷审核状态
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          {/* 搜索输入 */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="请输入游戏名称"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                onKeyDown={handleKeyDown}
                className="pl-9 h-11 rounded-xl"
                disabled={loading}
              />
            </div>
            <Button
              onClick={handleSearch}
              disabled={loading || !playerName.trim()}
              className="h-11 px-6 rounded-xl"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
            </Button>
          </div>

          {/* 结果区域 */}
          <AnimatePresence mode="wait">
            {loading && (
              <motion.div
                key="loading"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center justify-center py-8"
              >
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
              </motion.div>
            )}

            {error && !loading && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center gap-2 p-4 rounded-xl bg-destructive/10 text-destructive"
              >
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span className="text-sm">{error}</span>
              </motion.div>
            )}

            {results && !loading && (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-4"
              >
                {results.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    未找到相关记录
                  </div>
                ) : (
                  results.map((submission, index) => (
                    <motion.div
                      key={submission.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 rounded-xl bg-muted/30 border border-border/50"
                    >
                      {/* 问卷标题 */}
                      {submission.survey_title && (
                        <div className="mb-4 pb-3 border-b border-border/50">
                          <h3 className="font-medium text-sm text-muted-foreground">
                            {submission.survey_title}
                          </h3>
                        </div>
                      )}
                      
                      {/* 时间线 */}
                      <StatusTimeline submission={submission} />
                    </motion.div>
                  ))
                )}
              </motion.div>
            )}

            {/* 初始状态 - 无结果时的提示 */}
            {!loading && !error && !results && (
              <motion.div
                key="initial"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center py-6 text-muted-foreground text-sm"
              >
                输入游戏名称后点击搜索按钮查询
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </DialogContent>
    </Dialog>
  )
}
