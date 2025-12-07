import { Check, X, Clock, Eye, FileText } from 'lucide-react'
import {
  Timeline,
  TimelineContent,
  TimelineDate,
  TimelineHeader,
  TimelineIndicator,
  TimelineItem,
  TimelineSeparator,
  TimelineTitle,
} from '@/components/ui/timeline'
import type { SubmissionStatus } from '@/types/survey'

interface StatusTimelineProps {
  submission: SubmissionStatus
}

function formatDateTime(isoString: string | null): string {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function StatusTimeline({ submission }: StatusTimelineProps) {
  const { timeline, status, review_note, player_name, fill_duration } = submission

  // 计算当前激活的步骤
  const getActiveStep = () => {
    if (status === 'approved' || status === 'rejected') return 3
    if (timeline.first_viewed_at) return 2
    return 1
  }

  // 构建时间线数据
  const items = [
    {
      id: 1,
      title: '提交问卷',
      description: fill_duration ? `填写用时 ${fill_duration}` : '问卷已成功提交',
      date: formatDateTime(timeline.submitted_at),
      icon: <FileText className="w-3.5 h-3.5" />,
    },
    {
      id: 2,
      title: '管理员查看',
      description: timeline.first_viewed_at ? '管理员已查看您的问卷' : '等待管理员查看',
      date: formatDateTime(timeline.first_viewed_at),
      icon: <Eye className="w-3.5 h-3.5" />,
    },
  ]

  // 根据状态添加最终节点
  if (status === 'approved') {
    items.push({
      id: 3,
      title: '审核通过',
      description: `${player_name} 已记录到白名单`,
      date: formatDateTime(timeline.reviewed_at),
      icon: <Check className="w-3.5 h-3.5" />,
    })
  } else if (status === 'rejected') {
    items.push({
      id: 3,
      title: '审核未通过',
      description: review_note || '管理员拒绝了您的问卷',
      date: formatDateTime(timeline.reviewed_at),
      icon: <X className="w-3.5 h-3.5" />,
    })
  } else {
    items.push({
      id: 3,
      title: '等待审核',
      description: '管理员正在审核您的问卷',
      date: '',
      icon: <Clock className="w-3.5 h-3.5" />,
    })
  }

  return (
    <Timeline defaultValue={getActiveStep()}>
      {items.map((item) => (
        <TimelineItem
          key={item.id}
          step={item.id}
          className="group-data-[orientation=vertical]/timeline:ms-10"
        >
          <TimelineHeader>
            <TimelineSeparator className="group-data-[orientation=vertical]/timeline:-left-7 group-data-[orientation=vertical]/timeline:h-[calc(100%-1.5rem-0.25rem)] group-data-[orientation=vertical]/timeline:translate-y-6.5" />
            <TimelineDate>{item.date}</TimelineDate>
            <TimelineTitle
              className={
                status === 'rejected' && item.id === 3
                  ? 'text-destructive'
                  : status === 'approved' && item.id === 3
                  ? 'text-primary'
                  : ''
              }
            >
              {item.title}
            </TimelineTitle>
            <TimelineIndicator
              className={`group-data-[orientation=vertical]/timeline:-left-7 flex size-6 items-center justify-center ${
                status === 'rejected' && item.id === 3
                  ? 'border-none bg-destructive text-destructive-foreground'
                  : status === 'approved' && item.id === 3
                  ? 'border-none bg-primary text-primary-foreground'
                  : 'group-data-completed/timeline-item:border-none group-data-completed/timeline-item:bg-primary group-data-completed/timeline-item:text-primary-foreground'
              }`}
            >
              {item.icon}
            </TimelineIndicator>
          </TimelineHeader>
          <TimelineContent
            className={
              status === 'rejected' && item.id === 3
                ? 'text-destructive/80'
                : ''
            }
          >
            {item.description}
          </TimelineContent>
        </TimelineItem>
      ))}
    </Timeline>
  )
}
