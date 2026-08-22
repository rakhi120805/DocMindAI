import { useState, useRef } from 'react'
import { uploadDocument } from '../lib/api'

export default function UploadSlot({ onUploaded }) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const handleFile = async (file) => {
    if (!file) return
    setIsUploading(true)
    setError(null)
    try {
      const result = await uploadDocument(file)
      onUploaded(result)
    } catch (err) {
      setError(err.detail || err.message)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragging(false)
          handleFile(e.dataTransfer.files?.[0])
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer border-2 border-dashed rounded-sm px-4 py-6 text-center transition-colors ${
          isDragging ? 'border-manila-dark bg-paper-dim' : 'border-manila bg-paper'
        }`}
        style={{ borderColor: isDragging ? 'var(--color-manila-dark)' : 'var(--color-manila)' }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        {isUploading ? (
          <p className="font-mono text-sm" style={{ color: 'var(--color-ink-soft)' }}>
            Feeding document in&hellip;
          </p>
        ) : (
          <>
            <p className="font-sans text-sm font-medium" style={{ color: 'var(--color-ink)' }}>
              Drop a document here
            </p>
            <p className="font-mono text-xs mt-1" style={{ color: 'var(--color-ink-soft)' }}>
              or click to browse — PDF, PNG, JPG, WEBP
            </p>
          </>
        )}
      </div>
      {error && (
        <p className="mt-2 text-xs font-mono" style={{ color: 'var(--color-risk)' }}>
          {error}
        </p>
      )}
    </div>
  )
}
