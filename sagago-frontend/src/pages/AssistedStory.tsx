import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { toast } from 'react-toastify'
import { storiesApi } from '../api/stories'
import BackButton from '../components/ui/BackButton'
import ImageUpload from '../components/ui/ImageUpload'
import { 
  Loader, 
  Sparkles, 
  Wand2,
  AlertCircle,
  RefreshCw,
  HelpCircle,
  BookOpen
} from 'lucide-react'

const AssistedStory = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState('')
  const [coverImage, setCoverImage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    if (location.state?.prompt) {
      setPrompt(location.state.prompt)
    }
  }, [location.state])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setRetryCount(0)
    
    try {
      console.log('🔍 Creating assisted story with prompt:', prompt)
      const response = await storiesApi.createAssistedStory(prompt, coverImage)
      console.log('🔍 Job created:', response)
      setJobId(response.job_id)
      setStatus('pending')
      toast.info('Story generation started!')
      
      pollJobStatus(response.job_id)
    } catch (error: any) {
      console.error('❌ Failed to start story generation:', error)
      toast.error('Failed to start story generation')
      setIsLoading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const maxRetries = 3
    let retries = 0

    const poll = async () => {
      try {
        const response = await storiesApi.getJobStatus(jobId)
        setStatus(response.status)
        
        if (response.status === 'completed') {
          toast.success('Your story has been crafted!')
          setIsLoading(false)
          navigate(`/story/${response.story_id}`)
        } else if (response.status === 'failed') {
          if (retries < maxRetries) {
            retries++
            setRetryCount(retries)
            
            const waitTime = retries * 2000
            toast.info(`Retrying... (${retries}/${maxRetries})`)
            setTimeout(poll, waitTime)
          } else {
            setError('Story generation failed. Please try a different prompt.')
            toast.error('Generation failed. Please try again.')
            setIsLoading(false)
          }
        } else {
          setTimeout(poll, 2000)
        }
      } catch (error) {
        setTimeout(poll, 2000)
      }
    }
    poll()
  }

  const resetForm = () => {
    setError(null)
    setJobId(null)
    setStatus(null)
    setRetryCount(0)
    setIsLoading(false)
  }

  const examplePrompts = [
    {
      icon: '🏰',
      title: 'Fantasy Adventure',
      prompt: 'A young orphan discovers they are the last of an ancient lineage of mages and must learn to control their powers before an evil sorcerer finds them.'
    },
    {
      icon: '🚀',
      title: 'Sci-Fi Mystery',
      prompt: 'On a distant space station, the chief engineer discovers a hidden message in the ship\'s core that reveals a conspiracy threatening the entire galaxy.'
    },
    {
      icon: '💔',
      title: 'Romantic Drama',
      prompt: 'Two rival coffee shop owners in a small town slowly fall in love while competing for "Best Coffee in Town" award.'
    },
    {
      icon: '🔍',
      title: 'Detective Noir',
      prompt: 'A private investigator in 1940s Chicago takes on a case involving a missing heiress, but nothing is as it seems.'
    },
    {
      icon: '👻',
      title: 'Ghost Story',
      prompt: 'A family moves into an old Victorian house and discovers it\'s haunted by the ghost of a previous owner who has unfinished business.'
    },
    {
      icon: '🧙',
      title: 'Epic Fantasy',
      prompt: 'A group of unlikely heroes must band together to find a legendary artifact before an dark lord can use it to conquer the world.'
    }
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <BackButton />
        <div className="flex-1 text-center">
          <h1 className="text-3xl font-bold text-gray-900">AI-Assisted Story Writer</h1>
        </div>
        <div className="w-20"></div>
      </div>

      <p className="text-lg text-gray-600 text-center mb-8">
        Enter a detailed prompt and let AI craft a complete story with introduction, plot, and ending
      </p>

      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-2xl p-1 mb-8">
        <div className="bg-white rounded-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
                Your Story Prompt
              </label>
              <div className="relative">
                <textarea
                  id="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Write a story about a young wizard who discovers a hidden library filled with ancient secrets. Include elements of mystery, friendship, and a surprising twist ending."
                  rows={5}
                  className="input-field pr-12 py-4 text-lg resize-none"
                  disabled={isLoading}
                  required
                />
                <Wand2 className="absolute right-4 top-4 w-6 h-6 text-purple-400" />
              </div>
              <p className="mt-2 text-sm text-gray-500">
                Be specific! Include genre, characters, setting, and desired tone.
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-100">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Story Thumbnail (Optional)
              </label>
              <ImageUpload
                onImageUploaded={setCoverImage}
                initialImage={coverImage}
              />
            </div>

            {jobId && !error && (
              <div className="bg-purple-50 border border-purple-200 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <Loader className="w-5 h-5 text-purple-500 animate-spin" />
                    <span className="text-purple-700 font-medium">
                      {status === 'pending' ? 'Queued...' : 'Writing your story...'}
                    </span>
                  </div>
                  {retryCount > 0 && (
                    <span className="text-sm text-purple-600">
                      Attempt {retryCount}/3
                    </span>
                  )}
                </div>
                
                <div className="w-full h-2 bg-purple-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-purple-600 transition-all duration-500"
                    style={{ 
                      width: status === 'pending' ? '25%' 
                            : status === 'processing' ? '75%' 
                            : '0%' 
                    }}
                  />
                </div>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-red-800 mb-2">Generation Failed</h4>
                    <p className="text-sm text-red-600 mb-4">{error}</p>
                    <button
                      onClick={resetForm}
                      className="flex items-center space-x-2 px-4 py-2 bg-white border border-red-200 rounded-lg text-sm text-red-700 hover:bg-red-50 transition-colors"
                    >
                      <RefreshCw className="w-4 h-4" />
                      <span>Try Again</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !prompt.trim()}
              className="btn-primary w-full py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <Loader className="w-5 h-5 mr-2 animate-spin" />
                  {retryCount > 0 ? `Retrying... (${retryCount}/3)` : 'Crafting Your Story...'}
                </span>
              ) : (
                <span className="flex items-center justify-center">
                  <Wand2 className="w-5 h-5 mr-2" />
                  Generate Story
                </span>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Tips Section */}
      <div className="bg-gradient-to-r from-purple-100 to-indigo-100 rounded-xl p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <HelpCircle className="w-5 h-5 mr-2 text-purple-600" />
          Tips for Great Story Prompts
        </h3>
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          <div className="flex items-start space-x-2">
            <span className="text-purple-600 font-bold">•</span>
            <span><span className="font-medium">Genre:</span> fantasy, sci-fi, romance, mystery, horror</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-purple-600 font-bold">•</span>
            <span><span className="font-medium">Setting:</span> Victorian London, space station, magical academy</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-purple-600 font-bold">•</span>
            <span><span className="font-medium">Characters:</span> hero, villain, mentor, sidekick</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-purple-600 font-bold">•</span>
            <span><span className="font-medium">Tone:</span> dark and gritty, light-hearted, suspenseful</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-purple-600 font-bold">•</span>
            <span><span className="font-medium">Plot elements:</span> twist ending, redemption arc, mystery</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-purple-600 font-bold">•</span>
            <span><span className="font-medium">Conflict:</span> man vs nature, good vs evil, internal struggle</span>
          </div>
        </div>
      </div>

      {/* Example Prompts */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Need Inspiration? Try These Prompts
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {examplePrompts.map((item) => (
            <button
              key={item.title}
              onClick={() => setPrompt(item.prompt)}
              className="group p-6 bg-white rounded-xl shadow-md hover:shadow-xl transition-all transform hover:-translate-y-1 text-left border-2 border-transparent hover:border-purple-300"
              disabled={isLoading}
            >
              <span className="text-4xl mb-3 block">{item.icon}</span>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
              <p className="text-sm text-gray-600 line-clamp-3">{item.prompt}</p>
              <div className="mt-3 text-xs text-purple-600 group-hover:text-purple-700">
                Click to use this prompt →
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6">
        <div className="flex items-start space-x-4">
          <BookOpen className="w-8 h-8 text-blue-600 flex-shrink-0" />
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">How It Works</h4>
            <p className="text-gray-700 mb-3">
              This AI-assisted story generator creates complete narratives with proper structure:
            </p>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <span className="text-blue-600 font-bold mr-2">1️⃣</span>
                <span><span className="font-medium">Introduction:</span> Sets the scene and introduces characters</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 font-bold mr-2">2️⃣</span>
                <span><span className="font-medium">Body:</span> Develops the plot with conflicts and character growth</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 font-bold mr-2">3️⃣</span>
                <span><span className="font-medium">Conclusion:</span> Provides a satisfying ending</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AssistedStory