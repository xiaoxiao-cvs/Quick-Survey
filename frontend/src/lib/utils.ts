import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// shadcn 标准 className 合并工具: clsx 拼接 + tailwind-merge 去重冲突的 Tailwind 类
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
