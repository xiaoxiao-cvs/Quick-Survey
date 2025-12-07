import { motion } from 'framer-motion'
import { Check, X, Clock, Eye, FileText } from 'lucide-react'
import type { SubmissionStatus } from '@/types/survey'

interface StatusTimelineProps {
  submission: SubmissionStatus
}

interface TimelineNode {
  id: string
  title: string
  description: string
  time: string | null
  status: 'completed' | 'current' | 'pending' | 'failed'
  icon: React.ReactNode
}

function formatDateTime(isoString: string | null): string {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function StatusTimeline({ submission }: StatusTimelineProps) {
  const { timeline, status, review_note, player_name, fill_duration } = submission

  // 构建时间线节点
  const nodes: TimelineNode[] = [
    {
      id: 'submitted',
      title: '提交问卷',
      description: fill_duration ? `填写用时 ${fill_duration}` : '问卷已提交',
      time: timeline.submitted_at,
      status: 'completed',
      icon: <FileText className="w-4 h-4" />,
    },
    {
      id: 'viewed',
      title: '管理员查看',
      description: timeline.first_viewed_at ? '管理员已查看您的问卷' : '等待管理员查看',
      time: timeline.first_viewed_at,
      status: timeline.first_viewed_at ? 'completed' : status === 'pending' ? 'current' : 'pending',
      icon: <Eye className="w-4 h-4" />,
    },
  ]

  // 根据状态添加审核结果节点
  if (status === 'approved') {
    nodes.push({
      id: 'approved',
      title: '审核通过',
      description: `${player_name} 已记录到白名单`,
      time: timeline.reviewed_at,
      status: 'completed',
      icon: <Check className="w-4 h-4" />,
    })
  } else if (status === 'rejected') {
    nodes.push({
      id: 'rejected',
      title: '审核未通过',
      description: review_note || '管理员拒绝了您的问卷',
      time: timeline.reviewed_at,
      status: 'failed',
      icon: <X className="w-4 h-4" />,
    })
  } else {
    nodes.push({
      id: 'pending',
      title: '等待审核',
      description: '管理员正在审核您的问卷',
      time: null,
      status: timeline.first_viewed_at ? 'current' : 'pending',
      icon: <Clock className="w-4 h-4" />,
    })
  }

  const getNodeStyles = (nodeStatus: TimelineNode['status']) => {
    switch (nodeStatus) {
      case 'completed':
        return {
          circle: 'bg-primary border-primary text-primary-foreground',
          line: 'bg-primary',
          title: 'text-foreground',
          desc: 'text-muted-foreground',
        }
      case 'current':
        return {
          circle: 'bg-primary/20 border-primary text-primary animate-pulse',
          line: 'bg-border',
          title: 'text-foreground',
          desc: 'text-muted-foreground',
        }
      case 'failed':
        return {
          circle: 'bg-destructive border-destructive text-destructive-foreground',
          line: 'bg-destructive',
          title: 'text-destructive',
          desc: 'text-destructive/80',
        }
      case 'pending':
      default:
        return {
          circle: 'bg-muted border-border text-muted-foreground',
          line: 'bg-border',
          title: 'text-muted-foreground',
          desc: 'text-muted-foreground/60',
        }
    }
  }

  return (
    <div className="relative pl-8">
      {nodes.map((node, index) => {
        const styles = getNodeStyles(node.status)
        const isLast = index === nodes.length - 1

        return (
          <motion.div
            key={node.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.15, duration: 0.3 }}
            className="relative pb-8 last:pb-0"
          >
            {/* 连接线 */}
            {!isLast && (
              <div
                className={`absolute -left-5 top-8 w-0.5 h-[calc(100%-16px)] ${styles.line}`}
              />
            )}

            {/* 节点圆圈 */}
            <div
              className={`absolute -left-7 top-0 w-8 h-8 rounded-full border-2 flex items-center justify-center ${styles.circle}`}
            >
              {node.icon}
            </div>

            {/* 内容 */}
            <div className="min-h-8">
              <div className="flex items-center gap-3 mb-1">
                <h4 className={`font-medium ${styles.title}`}>{node.title}</h4>
                {node.time && (
                  <span className="text-xs text-muted-foreground">
                    {formatDateTime(node.time)}
                  </span>
                )}
              </div>
              <p className={`text-sm ${styles.desc}`}>{node.description}</p>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
