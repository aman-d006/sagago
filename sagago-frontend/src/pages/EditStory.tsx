import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { storiesApi } from '../api/stories'
import BackButton from '../components/ui/BackButton'
import { 
  Loader, 
  Save, 
  Eye, 
  Image as ImageIcon,
  Trash2,
  AlertCircle,
  ArrowLeft
} from 'lucide-react'
import type { Story } from '../types'

const EditStory = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    excerpt: '',
    cover_image: ''
  })
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    if (id) {
      fetchStory()
    }
  }, [id])

  const fetchStory = async () => {
    setIsLoading(true)
    try {
      console.log('Fetching story with ID:', id)
      const story = await storiesApi.getStory(parseInt(id!))
      console.log('Fetched story data:', story)
      
      setFormData({
        title: story.title || '',
        content: story.content || '',
        excerpt: story.excerpt || '',
        cover_image: story.cover_image || ''
      })
      
      console.log('Form data set:', {
        title: story.title,
        content: story.content ? story.content.substring(0, 50) + '...' : 'empty',
        excerpt: story.excerpt,
        cover_image: story.cover_image
      })
    } catch (error) {
      console.error('Failed to load story:', error)
      toast.error('Failed to load story')
      navigate('/')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)

    try {
      await storiesApi.updateStory(parseInt(id!), {
        title: formData.title,
        content: formData.content,
        excerpt: formData.excerpt || formData.content.substring(0, 150) + '...',
        cover_image: formData.cover_image || undefined
      })
      
      toast.success('Story updated successfully!')
      navigate(`/story/${id}`)
      
    } catch (error: any) {
      console.error('Update error:', error)
      toast.error(error.response?.data?.detail || 'Failed to update story')
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await storiesApi.deleteStory(parseInt(id!))
      toast.success('Story deleted successfully!')
      navigate('/')
    } catch (error: any) {
      console.error('Delete error:', error)
      toast.error(error.response?.data?.detail || 'Failed to delete story')
      setIsDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  const calculateReadingTime = (text: string) => {
    const words = text.split(' ').length
    return Math.ceil(words / 200)
  }

  const handleImageError = () => {
    setImageError(true)
  }

  const handleImageLoad = () => {
    setImageError(false)
  }

  const handleCancel = () => {
    navigate(`/story/${id}`)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowDeleteConfirm(false)} />
          <div className="relative bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Delete Story</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete "{formData.title}"? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center"
              >
                {isDeleting ? (
                  <>
                    <Loader className="w-4 h-4 mr-2 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  'Delete'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-8">
        <button
          onClick={handleCancel}
          className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Story</span>
        </button>
        <div className="flex-1 text-center">
          <h1 className="text-3xl font-bold text-gray-900">Edit Story</h1>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
            disabled={isSaving}
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete</span>
          </button>
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            disabled={isSaving}
          >
            <Eye className="w-4 h-4" />
            <span>{showPreview ? 'Edit' : 'Preview'}</span>
          </button>
        </div>
      </div>

      {!showPreview ? (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cover Image URL (Optional)
            </label>
            <div className="flex space-x-3">
              <input
                type="url"
                value={formData.cover_image}
                onChange={(e) => {
                  setFormData({ ...formData, cover_image: e.target.value })
                  setImageError(false)
                }}
                placeholder="https://example.com/image.jpg"
                className="input-field flex-1"
                disabled={isSaving}
              />
              <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden">
                {formData.cover_image && !imageError ? (
                  <img 
                    src={formData.cover_image} 
                    alt="Cover preview" 
                    className="w-full h-full object-cover rounded-lg"
                    onError={handleImageError}
                    onLoad={handleImageLoad}
                    crossOrigin="anonymous"
                  />
                ) : (
                  <ImageIcon className="w-8 h-8 text-gray-400" />
                )}
              </div>
            </div>
            {imageError && formData.cover_image && (
              <div className="mt-2 flex items-center space-x-2 text-xs text-red-500">
                <AlertCircle className="w-3 h-3" />
                <span>Failed to load image. Please check the URL.</span>
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Story Title *
            </label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="input-field text-2xl font-bold"
              required
              disabled={isSaving}
            />
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="content" className="block text-sm font-medium text-gray-700">
                Story Content *
              </label>
              <span className="text-sm text-gray-500">
                {calculateReadingTime(formData.content)} min read
              </span>
            </div>
            <textarea
              id="content"
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              rows={15}
              className="input-field font-serif leading-relaxed"
              required
              disabled={isSaving}
            />
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <label htmlFor="excerpt" className="block text-sm font-medium text-gray-700 mb-2">
              Excerpt (Optional)
            </label>
            <textarea
              id="excerpt"
              value={formData.excerpt}
              onChange={(e) => setFormData({ ...formData, excerpt: e.target.value })}
              rows={3}
              className="input-field"
              placeholder="A brief summary of your story..."
              disabled={isSaving}
            />
            <p className="mt-1 text-xs text-gray-500">
              If not provided, the first 150 characters will be used.
            </p>
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={handleCancel}
              className="btn-secondary px-8 py-3"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving || !formData.title || !formData.content}
              className="btn-primary px-8 py-3 flex items-center"
            >
              {isSaving ? (
                <>
                  <Loader className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </form>
      ) : (
        <div className="bg-white rounded-xl shadow-lg p-8">
          {formData.cover_image && (
            <div className="mb-8 rounded-lg overflow-hidden bg-gray-100">
              <img 
                src={formData.cover_image} 
                alt="Cover" 
                className="w-full h-64 object-contain mx-auto"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none'
                  const parent = e.currentTarget.parentElement
                  if (parent) {
                    parent.innerHTML = '<div class="w-full h-64 flex items-center justify-center text-gray-400">Failed to load image</div>'
                  }
                }}
                crossOrigin="anonymous"
              />
            </div>
          )}

          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {formData.title}
          </h1>

          <div className="flex items-center space-x-4 text-sm text-gray-500 mb-8">
            <span>{calculateReadingTime(formData.content)} min read</span>
          </div>

          <div className="prose prose-lg max-w-none">
            {formData.content.split('\n').map((paragraph, idx) => (
              <p key={idx} className="mb-4 leading-relaxed">
                {paragraph}
              </p>
            ))}
          </div>

          <div className="mt-8 flex justify-end space-x-4">
            <button
              onClick={() => setShowPreview(false)}
              className="btn-secondary px-6 py-2"
            >
              Back to Edit
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default EditStory