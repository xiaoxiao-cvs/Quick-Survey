import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import type { Question, AnswerSubmit } from '@/types/survey'
import { ImageUploader } from './ImageUploader'

interface QuestionCardProps {
  question: Question
  value?: AnswerSubmit['content']
  onChange: (content: AnswerSubmit['content']) => void
  index: number
}

export function QuestionCard({ question, value, onChange, index }: QuestionCardProps) {
  const renderQuestionContent = () => {
    switch (question.type) {
      case 'single':
        return (
          <RadioGroup
            value={value?.value as string || ''}
            onValueChange={(v) => onChange({ value: v })}
            className="space-y-3"
          >
            {question.options?.map((option, i) => (
              <motion.div
                key={option.value}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + i * 0.05 }}
              >
                <Label
                  htmlFor={`option-${option.value}`}
                  className="flex items-center space-x-3 p-4 rounded-2xl border border-border/50 cursor-pointer transition-all duration-200 hover:bg-accent/50 hover:border-primary/30 has-[input:checked]:bg-primary/5 has-[input:checked]:border-primary/50"
                >
                  <RadioGroupItem value={option.value} id={`option-${option.value}`} />
                  <span className="flex-1 text-base">{option.label}</span>
                </Label>
              </motion.div>
            ))}
          </RadioGroup>
        )

      case 'multiple':
        const selectedValues = (value?.values as string[]) || []
        return (
          <div className="space-y-3">
            {question.options?.map((option, i) => (
              <motion.div
                key={option.value}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + i * 0.05 }}
              >
                <Label
                  htmlFor={`option-${option.value}`}
                  className="flex items-center space-x-3 p-4 rounded-2xl border border-border/50 cursor-pointer transition-all duration-200 hover:bg-accent/50 hover:border-primary/30 has-[input:checked]:bg-primary/5 has-[input:checked]:border-primary/50"
                >
                  <Checkbox
                    id={`option-${option.value}`}
                    checked={selectedValues.includes(option.value)}
                    onCheckedChange={(checked) => {
                      const newValues = checked
                        ? [...selectedValues, option.value]
                        : selectedValues.filter((v) => v !== option.value)
                      onChange({ values: newValues })
                    }}
                  />
                  <span className="flex-1 text-base">{option.label}</span>
                </Label>
              </motion.div>
            ))}
          </div>
        )

      case 'boolean':
        // 使用 undefined 作为初始状态，只有明确选择后才有值
        const boolValue = value?.value as boolean | undefined
        const hasSelected = boolValue !== undefined
        return (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex items-center justify-center gap-6 p-6"
          >
            <Label
              htmlFor="boolean-switch"
              className={`text-lg font-medium transition-colors ${
                hasSelected && boolValue === false ? 'text-foreground' : 'text-muted-foreground'
              }`}
            >
              否
            </Label>
            <Switch
              id="boolean-switch"
              checked={boolValue === true}
              onCheckedChange={(checked) => onChange({ value: checked })}
              className="scale-125"
            />
            <Label
              htmlFor="boolean-switch"
              className={`text-lg font-medium transition-colors ${
                hasSelected && boolValue === true ? 'text-foreground' : 'text-muted-foreground'
              }`}
            >
              是
            </Label>
          </motion.div>
        )

      case 'text':
        return (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Textarea
              placeholder="请输入您的回答..."
              value={(value?.text as string) || ''}
              onChange={(e) => onChange({ text: e.target.value })}
              className="min-h-32 rounded-2xl resize-none text-base"
              maxLength={question.validation?.max_length}
            />
            {question.validation?.max_length && (
              <p className="text-sm text-muted-foreground mt-2 text-right">
                {((value?.text as string) || '').length} / {question.validation.max_length}
              </p>
            )}
          </motion.div>
        )

      case 'image':
        return (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <ImageUploader
              value={(value?.images as string[]) || []}
              onChange={(images: string[]) => onChange({ images })}
              maxImages={question.validation?.max_images || 5}
            />
          </motion.div>
        )

      default:
        return <p className="text-muted-foreground">不支持的题目类型</p>
    }
  }

  return (
    <Card className="rounded-3xl border-border/50 shadow-lg overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent pointer-events-none" />
      
      <CardHeader className="relative pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge 
                variant="secondary" 
                className="rounded-full px-3 text-xs font-medium"
              >
                第 {index + 1} 题
              </Badge>
              {question.is_required && (
                <Badge variant="destructive" className="rounded-full px-2 text-xs">
                  必填
                </Badge>
              )}
            </div>
            <CardTitle className="text-xl leading-relaxed">
              {question.title}
            </CardTitle>
            {question.description && (
              <CardDescription className="mt-2 text-base">
                {question.description}
              </CardDescription>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="relative pt-2 pb-6">
        {renderQuestionContent()}
      </CardContent>
    </Card>
  )
}
