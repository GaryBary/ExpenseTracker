import { useState, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function Capture() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [cameraActive, setCameraActive] = useState(false)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setCameraActive(true)
      }
    } catch (err) {
      setMessage('Camera access denied or not available')
    }
  }

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream
      stream.getTracks().forEach(track => track.stop())
      videoRef.current.srcObject = null
      setCameraActive(false)
    }
  }

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current
      const video = videoRef.current
      
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      
      const ctx = canvas.getContext('2d')
      ctx?.drawImage(video, 0, 0)
      
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], 'receipt.jpg', { type: 'image/jpeg' })
          setSelectedFile(file)
          setPreview(canvas.toDataURL())
          stopCamera()
        }
      }, 'image/jpeg', 0.8)
    }
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    
    if (!selectedFile) {
      setMessage('Please select or capture an image')
      return
    }

    setUploading(true)
    setMessage(null)

    try {
      const formData = new FormData()
      formData.append('image', selectedFile)

      const response = await fetch(`${API_BASE}/expenses`, {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const result = await response.json()
        setMessage(`✅ Expense created successfully! ID: ${result.id}`)
        setSelectedFile(null)
        setPreview(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      } else {
        const error = await response.text()
        setMessage(`❌ Upload failed: ${error}`)
      }
    } catch (err) {
      setMessage(`❌ Upload failed: ${err}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="page">
      <h1 className="page-title">Add Expense</h1>
      
      <div className="capture-container">
        <div className="camera-section">
          <h2 className="section-title">Take Photo</h2>
          
          {!cameraActive ? (
            <button 
              type="button" 
              onClick={startCamera}
              className="btn camera-btn"
            >
              📷 Open Camera
            </button>
          ) : (
            <div className="camera-view">
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline
                className="camera-video"
              />
              <div className="camera-controls">
                <button 
                  type="button" 
                  onClick={capturePhoto}
                  className="btn"
                >
                  📸 Capture
                </button>
                <button 
                  type="button" 
                  onClick={stopCamera}
                  className="btn btn-secondary"
                >
                  ❌ Cancel
                </button>
              </div>
            </div>
          )}
          
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>

        <div className="divider">or</div>

        <div className="upload-section">
          <h2 className="section-title">Upload Image</h2>
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="file-input"
          />
        </div>
      </div>

      {preview && (
        <div className="preview-section">
          <h3 className="section-title">Preview</h3>
          <img src={preview} alt="Receipt preview" className="preview-image" />
        </div>
      )}

      <form onSubmit={handleSubmit} className="submit-form">
        <button 
          type="submit" 
          disabled={!selectedFile || uploading}
          className="btn submit-btn"
        >
          {uploading ? '⏳ Processing...' : '💾 Save Expense'}
        </button>
      </form>

      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      <style jsx>{`
        .capture-container {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          gap: 2rem;
          align-items: start;
          margin-bottom: 2rem;
        }
        
        .section-title {
          font-size: 1.125rem;
          font-weight: 600;
          margin-bottom: 1rem;
          color: #374151;
        }
        
        .camera-btn {
          width: 100%;
          font-size: 1.125rem;
          padding: 1rem;
        }
        
        .camera-view {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        
        .camera-video {
          width: 100%;
          max-width: 300px;
          border-radius: 8px;
          background: #000;
        }
        
        .camera-controls {
          display: flex;
          gap: 0.5rem;
        }
        
        .divider {
          display: flex;
          align-items: center;
          justify-content: center;
          color: #6b7280;
          font-weight: 500;
          position: relative;
        }
        
        .divider::before,
        .divider::after {
          content: '';
          position: absolute;
          top: 50%;
          width: 20px;
          height: 1px;
          background: #d1d5db;
        }
        
        .divider::before {
          left: -30px;
        }
        
        .divider::after {
          right: -30px;
        }
        
        .file-input {
          width: 100%;
          padding: 0.75rem;
          border: 2px dashed #d1d5db;
          border-radius: 6px;
          background: #f9fafb;
          cursor: pointer;
        }
        
        .file-input:hover {
          border-color: #2563eb;
          background: #eff6ff;
        }
        
        .preview-section {
          margin-bottom: 2rem;
        }
        
        .preview-image {
          max-width: 300px;
          max-height: 400px;
          border-radius: 8px;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .submit-form {
          margin-bottom: 2rem;
        }
        
        .submit-btn {
          width: 100%;
          font-size: 1.125rem;
          padding: 1rem;
        }
        
        .submit-btn:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }
        
        .message {
          padding: 1rem;
          border-radius: 6px;
          font-weight: 500;
        }
        
        .message.success {
          background: #d1fae5;
          color: #065f46;
          border: 1px solid #a7f3d0;
        }
        
        .message.error {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fca5a5;
        }
        
        @media (max-width: 768px) {
          .capture-container {
            grid-template-columns: 1fr;
            gap: 1.5rem;
          }
          
          .divider::before,
          .divider::after {
            display: none;
          }
        }
      `}</style>
    </div>
  )
}

export default Capture
