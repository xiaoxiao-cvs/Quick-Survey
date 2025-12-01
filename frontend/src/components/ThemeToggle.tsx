import { Moon, Sun, Monitor } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '@/providers/ThemeProvider'
import { Button } from '@/components/ui/button'

const themes = [
  { value: 'light' as const, icon: Sun, label: '浅色' },
  { value: 'dark' as const, icon: Moon, label: '深色' },
  { value: 'system' as const, icon: Monitor, label: '跟随系统' },
]

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  const currentIndex = themes.findIndex((t) => t.value === theme)
  const nextTheme = themes[(currentIndex + 1) % themes.length]
  const CurrentIcon = themes[currentIndex].icon

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(nextTheme.value)}
      className="relative h-10 w-10 rounded-2xl"
      title={`当前: ${themes[currentIndex].label}，点击切换到${nextTheme.label}`}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={theme}
          initial={{ scale: 0, rotate: -180, opacity: 0 }}
          animate={{ scale: 1, rotate: 0, opacity: 1 }}
          exit={{ scale: 0, rotate: 180, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          <CurrentIcon className="h-5 w-5" />
        </motion.div>
      </AnimatePresence>
    </Button>
  )
}
