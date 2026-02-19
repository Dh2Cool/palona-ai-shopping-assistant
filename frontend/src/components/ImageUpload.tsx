import { useRef, useState } from 'react'

const MAX_SIZE = 800
const MAX_KB = 400

function compressImage(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      const canvas = document.createElement('canvas')
      let { width, height } = img
      if (width > MAX_SIZE || height > MAX_SIZE) {
        if (width > height) {
          height = (height / width) * MAX_SIZE
          width = MAX_SIZE
        } else {
          width = (width / height) * MAX_SIZE
          height = MAX_SIZE
        }
      }
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      if (!ctx) return reject(new Error('Canvas error'))
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, 0, width, height)
      let quality = 0.9
      const tryEncode = () => {
        const dataUrl = canvas.toDataURL('image/jpeg', quality)
        const kb = (dataUrl.length * 3) / 4 / 1024
        if (kb <= MAX_KB || quality <= 0.3) resolve(dataUrl)
        else {
          quality -= 0.1
          tryEncode()
        }
      }
      tryEncode()
    }
    img.onerror = () => reject(new Error('Failed to load image'))
    img.src = url
  })
}

interface ImageUploadProps {
  onImageSelect: (base64: string) => void
  disabled?: boolean
}

export function ImageUpload({ onImageSelect, disabled }: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !file.type.startsWith('image/')) return

    compressImage(file).then((result) => {
      setPreview(result)
      onImageSelect(result)
    }).catch(() => onImageSelect(''))
  }

  const clear = () => {
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
