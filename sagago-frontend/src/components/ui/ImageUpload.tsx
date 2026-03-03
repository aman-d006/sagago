import { useState, useRef } from 'react'
import { Upload, X, Image as ImageIcon, Loader } from 'lucide-react'
import { storiesApi } from '../../api/stories'
import { toast } from 'react-toastify'

interface ImageUploadProps {
  onImageUploaded: (url: string) => void
  onImageRemoved?: () => void
  initialImage?: string
  className?: string
}

const ImageUpload = ({ onImageUploaded, onImageRemoved, initialImage, className = '' }: ImageUploadProps) => {
  const [imageUrl, setImageUrl] = useState<string | null>(initialImage || null)
  const [isUploading, setIsUploading] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(initialImage || null)
  const [loadError, setLoadError] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    console.log('Selected file:', file.name, file.type, file.size)

    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file')
      return
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be less than 5MB')
      return
    }

    const reader = new FileReader()
    reader.onloadend = () => {
      setPreviewUrl(reader.result as string)
      setLoadError(false)
    }
    reader.readAsDataURL(file)

    setIsUploading(true)
    try {
      console.log('Uploading file...')
      const response = await storiesApi.uploadImage(file)
      console.log('Upload response:', response)
      
      const fullUrl = response.url.startsWith('http') 
        ? response.url 
        : `http://localhost:8000${response.url}`
      
      console.log('Full image URL:', fullUrl)
      
      setImageUrl(response.url)
      onImageUploaded(response.url)
      toast.success('Image uploaded successfully')
    } catch (error: any) {
      console.error('Upload failed:', error)
      console.error('Error response:', error.response?.data)
      toast.error(error.response?.data?.detail || 'Failed to upload image')
      setPreviewUrl(null)
    } finally {
      setIsUploading(false)
    }
  }

  const handleRemove = () => {
    setImageUrl(null)
    setPreviewUrl(null)
    setLoadError(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    if (onImageRemoved) {
      onImageRemoved()
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleImageError = () => {
    console.error('Failed to load image from URL:', previewUrl)
    setLoadError(true)
  }

  const getFullImageUrl = (url: string) => {
    if (url.startsWith('data:')) return url
    if (url.startsWith('http')) return url
    if (url.startsWith('/uploads')) return `http://localhost:8000${url}`
    return `http://localhost:8000/uploads/stories/${url.split('/').pop()}`
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept="image/jpeg,image/png,image/gif,image/webp"
        className="hidden"
      />

      {previewUrl ? (
        <div className="relative group">
          {loadError ? (
            <div className="w-full h-48 bg-red-50 rounded-lg border-2 border-red-200 flex items-center justify-center">
              <p className="text-sm text-red-600">Failed to load image</p>
            </div>
          ) : (
            <img
              src={getFullImageUrl(previewUrl)}
              alt="Story thumbnail"
              className="w-full h-48 object-cover rounded-lg border-2 border-gray-200"
              onError={handleImageError}
            />
          )}
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center space-x-2">
            <button
              onClick={handleClick}
              disabled={isUploading}
              className="p-2 bg-white rounded-full hover:bg-gray-100 transition-colors"
              title="Change image"
            >
              <Upload className="w-4 h-4 text-gray-700" />
            </button>
            <button
              onClick={handleRemove}
              disabled={isUploading}
              className="p-2 bg-white rounded-full hover:bg-gray-100 transition-colors"
              title="Remove image"
            >
              <X className="w-4 h-4 text-red-500" />
            </button>
          </div>
          {isUploading && (
            <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center">
              <Loader className="w-8 h-8 text-white animate-spin" />
            </div>
          )}
        </div>
      ) : (
        <div
          onClick={handleClick}
          className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-primary-500 hover:bg-gray-50 transition-colors group"
        >
          <div className="flex flex-col items-center">
            {isUploading ? (
              <Loader className="w-8 h-8 text-primary-500 animate-spin mb-2" />
            ) : (
              <>
                <ImageIcon className="w-8 h-8 text-gray-400 group-hover:text-primary-500 mb-2" />
                <p className="text-sm text-gray-500 group-hover:text-primary-600">
                  Click to upload thumbnail
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  PNG, JPG, GIF up to 5MB
                </p>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ImageUpload