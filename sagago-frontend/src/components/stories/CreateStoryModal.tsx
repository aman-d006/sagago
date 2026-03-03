import { useState } from 'react'
import { storiesApi } from '../../api/stories'
import { Loader, Sparkles, PenTool, X, AlertCircle } from 'lucide-react'
import { toast } from 'react-toastify'

interface CreateStoryModalProps {
  onClose: () => void
  onSuccess: (storyId: number) => void
}

const CreateStoryModal = ({ onClose, onSuccess }: CreateStoryModalProps) => {
  const [storyType, setStoryType] = useState<'ai' | 'write'>('ai')
  const [theme, setTheme] = useState('')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)

  const handleAIGenerate = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      const response = await storiesApi.generateFullStory(theme)
      setJobId(response.job_id)
      setStatus('pending')
      toast.info('Story generation started!')
      pollJobStatus(response.job_id)
    } catch (error) {
      toast.error('Failed to start story generation')
      setIsLoading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await storiesApi.getJobStatus(jobId)
        setStatus(response.status)
        
        if (response.status === 'completed') {
          toast.success('Your story has been created!')
          onSuccess(response.story_id)
        } else if (response.status === 'failed') {
          toast.error('Story generation failed. Please try again.')
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

  const handleWriteSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    
    try {
      const response = await storiesApi.publishStory({
        title,
        content,
        excerpt: content.substring(0, 150) + '...'
      })
      toast.success('Your story has been published!')
      onSuccess(response.id)
    } catch (error) {
      toast.error('Failed to publish story')
      setIsLoading(false)
    }
  }

  const popularThemes = [
    { emoji: '🐉', name: 'Dragon Adventure', prompt: 'An epic tale of dragons and ancient magic' },
    { emoji: '🚀', name: 'Space Opera', prompt: 'A grand space adventure across galaxies' },
    { emoji: '🏰', name: 'Medieval Quest', prompt: 'A knight\'s journey to save the kingdom' },
    { emoji: '🔮', name: 'Magical Academy', prompt: 'Young mages discover their powers' },
    { emoji: '🌊', name: 'Ocean Mystery', prompt: 'Secrets hidden beneath the waves' },
    { emoji: '🤖', name: 'Cyberpunk', prompt: 'A futuristic tale of technology and rebellion' },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Create New Story</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Story Type Tabs */}
        <div className="px-6 pt-6">
          <div className="flex space-x-2 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setStoryType('ai')}
              className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                storyType === 'ai'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>Generate with AI</span>
            </button>
            <button
              onClick={() => setStoryType('write')}
              className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                storyType === 'write'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <PenTool className="w-4 h-4" />
              <span>Write Your Own</span>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {storyType === 'ai' ? (
            <form onSubmit={handleAIGenerate} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Story Theme
                </label>
                <input
                  type="text"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  placeholder="e.g., a dragon's revenge, love in space, etc."
                  className="input-field"
                  required
                  disabled={isLoading}
                />
                <p className="mt-2 text-sm text-gray-500">
                  Our AI will generate a complete story based on your theme.
                </p>
              </div>

              {/* Popular Themes */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-3">Popular Themes</p>
                <div className="grid grid-cols-2 gap-3">
                  {popularThemes.map((item) => (
                    <button
                      key={item.name}
                      type="button"
                      onClick={() => setTheme(item.prompt)}
                      className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left"
                      disabled={isLoading}
                    >
                      <span className="text-2xl">{item.emoji}</span>
                      <div>
                        <div className="text-sm font-medium">{item.name}</div>
                        <div className="text-xs text-gray-500">Click to use</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {jobId && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center space-x-3">
                    <Loader className="w-5 h-5 text-blue-500 animate-spin" />
                    <span className="text-blue-700 text-sm">
                      {status === 'pending' ? 'Queued...' : 'Writing your story...'}
                    </span>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || !theme.trim()}
                className="w-full btn-primary py-3"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <Loader className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate Story
                  </span>
                )}
              </button>
            </form>
          ) : (
            <form onSubmit={handleWriteSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Story Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter your story title"
                  className="input-field"
                  required
                  disabled={isLoading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Story Content
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={10}
                  placeholder="Once upon a time..."
                  className="input-field font-serif"
                  required
                  disabled={isLoading}
                />
                <p className="mt-2 text-sm text-gray-500">
                  Write your story in paragraphs. Make it engaging!
                </p>
              </div>

              <button
                type="submit"
                disabled={isLoading || !title.trim() || !content.trim()}
                className="w-full btn-primary py-3"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <Loader className="w-4 h-4 mr-2 animate-spin" />
                    Publishing...
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <PenTool className="w-4 h-4 mr-2" />
                    Publish Story
                  </span>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

export default CreateStoryModal