import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, X, Loader2, Image as ImageIcon, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { uploadImage, getImageUrl } from '@/lib/api'
import { toast } from 'sonner'

interface ImageUploaderProps {
  value: string[]
  onChange: (images: string[]) => void
  maxImages?: number
}

export function ImageUploader({ value, onChange, maxImages = 5 }: ImageUploaderProps) {
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)

  const handleFileSelect = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return

    const remainingSlots = maxImages - value.length
    if (remainingSlots <= 0) {
      toast.error(`最多只能上传 ${maxImages} 张图片`)
      return
    }

    const filesToUpload = Array.from(files).slice(0, remainingSlots)
    
    // 验证文件类型和大小
    for (const file of filesToUpload) {
      if (!file.type.startsWith('image/')) {
        toast.error('只能上传图片文件')
        return
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error('图片大小不能超过 10MB')
        return
      }
    }

    setUploading(true)
    const uploadedUrls: string[] = []

    try {
      for (const file of filesToUpload) {
        const result = await uploadImage(file)
        uploadedUrls.push(result.url)
      }
      onChange([...value, ...uploadedUrls])
      toast.success(`成功上传 ${uploadedUrls.length} 张图片`)
    } catch {
      toast.error('上传失败，请重试')
    } finally {
      setUploading(false)
    }
  }, [value, maxImages, onChange])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    handleFileSelect(e.dataTransfer.files)
  }, [handleFileSelect])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }, [])

  const handleRemove = useCallback((index: number) => {
    const newImages = value.filter((_, i) => i !== index)
    onChange(newImages)
  }, [value, onChange])

  const canUploadMore = value.length < maxImages

  return (
    <div className="space-y-4">
      {/* 已上传的图片 */}
      <AnimatePresence mode="popLayout">
        {value.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="grid grid-cols-2 sm:grid-cols-3 gap-3"
          >
            {value.map((url, index) => (
              <motion.div
                key={url}
                layout
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.2 }}
                className="relative aspect-square rounded-2xl overflow-hidden group"
              >
                <img
                  src={getImageUrl(url)}
                  alt={`上传图片 ${index + 1}`}
                  className="w-full h-full object-cover"
                />
                <motion.div
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 1 }}
                  className="absolute inset-0 bg-black/50 flex items-center justify-center"
                >
                  <Button
                    variant="destructive"
                    size="icon"
                    className="rounded-full"
                    onClick={() => handleRemove(index)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </motion.div>
                <div className="absolute top-2 left-2">
                  <span className="bg-black/50 text-white text-xs px-2 py-1 rounded-full">
                    {index + 1}
                  </span>
                </div>
              </motion.div>
            ))}

            {/* 添加更多按钮 */}
            {canUploadMore && !uploading && (
              <motion.label
                layout
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="aspect-square rounded-2xl border-2 border-dashed border-border/50 flex flex-col items-center justify-center cursor-pointer hover:border-primary/50 hover:bg-accent/50 transition-all duration-200"
              >
                <Plus className="w-8 h-8 text-muted-foreground mb-1" />
                <span className="text-xs text-muted-foreground">添加图片</span>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(e) => handleFileSelect(e.target.files)}
                  className="hidden"
                />
              </motion.label>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 上传区域 */}
      {value.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`
            relative rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-200
            ${dragOver 
              ? 'border-primary bg-primary/5' 
              : 'border-border/50 hover:border-primary/30 hover:bg-accent/30'
            }
          `}
        >
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => handleFileSelect(e.target.files)}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={uploading}
          />

          <AnimatePresence mode="wait">
            {uploading ? (
              <motion.div
                key="uploading"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex flex-col items-center gap-3"
              >
                <Loader2 className="w-12 h-12 text-primary animate-spin" />
                <p className="text-muted-foreground">上传中...</p>
              </motion.div>
            ) : (
              <motion.div
                key="idle"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex flex-col items-center gap-3"
              >
                <motion.div
                  animate={dragOver ? { scale: 1.1 } : { scale: 1 }}
                  className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center"
                >
                  {dragOver ? (
                    <Upload className="w-8 h-8 text-primary" />
                  ) : (
                    <ImageIcon className="w-8 h-8 text-primary" />
                  )}
                </motion.div>
                <div>
                  <p className="font-medium">
                    {dragOver ? '释放以上传图片' : '点击或拖拽上传图片'}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    支持 JPG、PNG、GIF，最大 10MB，最多 {maxImages} 张
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}

      {/* 上传状态 */}
      {uploading && value.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-center gap-2 text-muted-foreground"
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm">正在上传...</span>
        </motion.div>
      )}

      {/* 图片数量提示 */}
      <p className="text-sm text-muted-foreground text-center">
        已上传 {value.length} / {maxImages} 张图片
      </p>
    </div>
  )
}
