import imageCompression from 'browser-image-compression'

// 上传前在浏览器内把图片近似无损地重编码为 WebP, 减小体积:
// - BA 大厅截图是文字/UI, 同体积下 WebP 比 JPEG 文字更清晰, q0.9 肉眼无差。
// - 仅对超大图缩到最长边 2560 兜底; 手机截图本身多在 1080~1284px, 不会被缩放。
// - 核心收益是减少走移动网络的字节, 顺带消除上传超时 (配合 uploadImage 放大的 timeout)。
// 压缩失败 (个别 webview 不支持 canvas 编 webp) 时回退原图, 不让压缩成为上传的拦路。

const TARGET_TYPE = 'image/webp'

// GIF 可能是动图, 压成 webp 会丢帧, 原样放行; 其余位图重编码。
function shouldCompress(file: File): boolean {
  return file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'image/webp'
}

function toWebpName(name: string): string {
  const dot = name.lastIndexOf('.')
  return `${dot > 0 ? name.slice(0, dot) : name}.webp`
}

export async function compressImage(file: File): Promise<File> {
  if (!shouldCompress(file)) return file
  try {
    const compressed = await imageCompression(file, {
      maxWidthOrHeight: 2560, // 仅给超大图兜底, 不动常规手机截图
      initialQuality: 0.9, // 近似无损
      fileType: TARGET_TYPE,
      useWebWorker: true,
      maxSizeMB: 5, // 宽松上限, 避免为压到极小而牺牲清晰度
    })
    // 压完反而更大 (本就是高压图) 则保留原图; 否则规范成 .webp 名与类型。
    if (compressed.size >= file.size) return file
    return new File([compressed], toWebpName(file.name), { type: TARGET_TYPE })
  } catch {
    return file
  }
}
