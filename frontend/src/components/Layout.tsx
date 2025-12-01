import { motion } from 'framer-motion'
import { ThemeToggle } from './ThemeToggle'
import { FileText } from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground transition-colors duration-300">
      {/* Header */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="sticky top-0 z-50 backdrop-blur-xl bg-background/80 border-b border-border/40 shrink-0"
      >
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <motion.div
            className="flex items-center gap-3"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <span className="font-semibold text-lg">Quick Survey</span>
          </motion.div>
          
          <ThemeToggle />
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 md:py-10 flex-1 flex flex-col">
        {children}
      </main>

      {/* Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.4 }}
        className="border-t border-border/40 py-6 shrink-0"
      >
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} Quick Survey. All rights reserved.</p>
        </div>
      </motion.footer>
    </div>
  )
}
