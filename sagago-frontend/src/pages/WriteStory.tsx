import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { storiesApi } from '../api/stories'
import BackButton from '../components/ui/BackButton'
import ImageUpload from '../components/ui/ImageUpload'
import { getImageUrl } from '../utils/imageHelpers'
import { 
  Loader, 
  Save, 
  Eye, 
  X
} from 'lucide-react'

const WriteStory = () => {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [formData, setFormData] = useState(() => {
    const saved = localStorage.getItem('writeStoryDraft')
    return saved ? JSON.parse(saved) : {
      title: '',
      content: '',
      excerpt: '',
      cover_image: ''
    }
  })
  const [jobId, setJobId] = useState<string | null>(null)
  const [showExitWarning, setShowExitWarning] = useState(false)

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (formData.title || formData.content) {
        e.preventDefault()
        e.returnValue = ''
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [formData.title, formData.content])

  useEffect(() => {
    localStorage.setItem('writeStoryDraft', JSON.stringify(formData))
  }, [formData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      console.log('Submitting story with cover image:', formData.cover_image)
      
      const response = await storiesApi.publishWrittenStory({
        title: formData.title,
        content: formData.content,
        excerpt: formData.excerpt || formData.content.substring(0, 150) + '...',
        cover_image: formData.cover_image || undefined
      })
      
      setJobId(response.job_id)
      localStorage.removeItem('writeStoryDraft')
      toast.info('Story creation started!')
      pollJobStatus(response.job_id)
      
    } catch (error) {
      console.error('Failed to publish story:', error)
      toast.error('Failed to publish story')
      setIsLoading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await storiesApi.getJobStatus(jobId)
        
        if (response.status === 'completed') {
          toast.success('Your story has been published!')
          navigate(`/story/${response.story_id}`)
        } else if (response.status === 'failed') {
          toast.error('Story creation failed. Please try again.')
          setIsLoading(false)
        } else {
          setTimeout(poll, 2000)
        }
      } catch (error) {
        setTimeout(poll, 2000)
      }
    }
    poll()
  }

  const calculateReadingTime = (text: string) => {
    const words = text.split(' ').length
    return Math.ceil(words / 200)
  }

  const handleBackClick = () => {
    if (formData.title || formData.content) {
      setShowExitWarning(true)
    } else {
      navigate(-1)
    }
  }

  const clearDraft = () => {
    localStorage.removeItem('writeStoryDraft')
    setFormData({
      title: '',
      content: '',
      excerpt: '',
      cover_image: ''
    })
    setShowExitWarning(false)
    navigate(-1)
  }

  const handleImageUploaded = (url: string) => {
    console.log('Image uploaded, URL:', url)
    setFormData({ ...formData, cover_image: url })
  }

  const handleImageRemoved = () => {
    setFormData({ ...formData, cover_image: '' })
  }

  const previewImageUrl = getImageUrl(formData.cover_image)

  return (
    <div className="max-w-4xl mx-auto">
      {showExitWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowExitWarning(false)} />
          <div className="relative bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Unsaved Changes</h3>
            <p className="text-gray-600 mb-6">
              You have unsaved changes. Do you want to save your draft before leaving?
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowExitWarning(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Continue Writing
              </button>
              <button
                onClick={clearDraft}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Discard & Leave
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-8">
        <button onClick={handleBackClick} className="flex items-center space-x-2 text-gray-600 hover:text-gray-900">
          <BackButton />
        </button>
        <div className="flex-1 text-center">
          <h1 className="text-3xl font-bold text-gray-900">Write a Story</h1>
          <p className="text-gray-600 mt-1">Share your creativity with the world</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => setShowPreview(!showPreview)}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Eye className="w-4 h-4" />
            <span>{showPreview ? 'Edit' : 'Preview'}</span>
          </button>
        </div>
      </div>

      {jobId && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div className="flex items-center space-x-3">
            <Loader className="w-5 h-5 text-blue-500 animate-spin" />
            <span className="text-blue-700">Creating your story...</span>
          </div>
        </div>
      )}

      {!showPreview ? (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Story Thumbnail (Optional)
            </label>
            <ImageUpload
              onImageUploaded={handleImageUploaded}
              onImageRemoved={handleImageRemoved}
              initialImage={formData.cover_image}
            />
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
              placeholder="Enter your story title"
              required
              disabled={isLoading}
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
              placeholder="Once upon a time..."
              required
              disabled={isLoading}
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
              disabled={isLoading}
            />
            <p className="mt-1 text-xs text-gray-500">
              If not provided, we'll use the first 150 characters of your story.
            </p>
          </div>

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={handleBackClick}
              className="btn-secondary px-8 py-3"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !formData.title || !formData.content}
              className="btn-primary px-8 py-3 flex items-center"
            >
              {isLoading ? (
                <>
                  <Loader className="w-4 h-4 mr-2 animate-spin" />
                  Publishing...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Publish Story
                </>
              )}
            </button>
          </div>
        </form>
      ) : (
        <div className="bg-white rounded-xl shadow-lg p-8">
          {previewImageUrl && (
            <div className="mb-8 rounded-lg overflow-hidden bg-gray-100">
              <img 
                src={previewImageUrl} 
                alt="Cover" 
                className="w-full h-64 object-contain mx-auto"
              />
            </div>
          )}

          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {formData.title || 'Untitled Story'}
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

          <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-700 text-center">
              This is a preview. Click "Edit" to make changes before publishing.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default WriteStory