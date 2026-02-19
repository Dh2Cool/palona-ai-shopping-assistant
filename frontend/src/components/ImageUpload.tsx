import { useRef, useState, useEffect } from 'react'

const MAX_SIZE = 800
const MAX_KB = 400

function compressImage(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string
      const img = new Image()
      img.onload = () => {
        let { naturalWidth: width, naturalHeight: height } = img
        // If within limits, send as-is
        const kb = (dataUrl.length * 3) / 4 / 1024
        if (width <= MAX_SIZE && height <= MAX_SIZE && kb <= MAX_KB) {
          resolve(dataUrl)
          return
        }
        // Resize and compress via canvas
        if (width > MAX_SIZE || height > MAX_SIZE) {
          if (width > height) {
            height = Math.round((height / width) * MAX_SIZE)
            width = MAX_SIZE
          } else {
            width = Math.round((width / height) * MAX_SIZE)
            height = MAX_SIZE
          }
        }
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        if (!ctx) return reject(new Error('Canvas error'))
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(0, 0, width, height)
        ctx.drawImage(img, 0, 0, width, height)
        let quality = 0.9
        const tryEncode = () => {
          const compressed = canvas.toDataURL('image/jpeg', quality)
          const compressedKb = (compressed.length * 3) / 4 / 1024
          if (compressedKb <= MAX_KB || quality <= 0.3) resolve(compressed)
          else { quality -= 0.1; tryEncode() }
        }
        tryEncode()
      }
      img.onerror = () => reject(new Error('Failed to decode image'))
      img.src = dataUrl
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsDataURL(file)
  })
}

interface ImageUploadProps {
  onImageSelect: (base64: string) => void
  disabled?: boolean
}

export function ImageUpload({ onImageSelect, disabled }: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const previewUrlRef = useRef<string | null>(null)

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current)
    }
  }, [])

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !file.type.startsWith('image/')) return

    // Preview uses object URL — always renders correctly, no canvas involved
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current)
    const objectUrl = URL.createObjectURL(file)
    previewUrlRef.current = objectUrl
    setPreview(objectUrl)

    // Separately compress for backend
    compressImage(file)
      .then((result) => onImageSelect(result))
      .catch(() => onImageSelect(''))
  }

  const clear = () => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = null
    }
    setPreview(null)
    onImageSelect('')
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="image-upload">
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleFile}
        disabled={disabled}
        style={{ display: 'none' }}
      />
      {preview ? (
        <div className="image-preview">
          <img src={preview} alt="Upload preview" />
          <button type="button" onClick={clear} className="clear-btn">
            Remove
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
          className="upload-btn"
        >
          Attach image
        </button>
      )}
    </div>
  )
}
