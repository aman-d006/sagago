import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { toast } from 'react-toastify'
import { storiesApi } from '../api/stories'
import { Loader, Sparkles, AlertCircle, RefreshCw } from 'lucide-react'
import BackButton from '../components/ui/BackButton'

const CreateStory = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const [theme, setTheme] = useState(() => {
    return location.state?.theme || ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [suggestedThemes, setSuggestedThemes] = useState<string[]>([])

  useEffect(() => {
    // Auto-submit if theme is provided from templates
    if (location.state?.theme && !isLoading && !jobId) {
      handleAutoSubmit()
    }
  }, [location.state?.theme])

  const handleAutoSubmit = async () => {
    setIsLoading(true)
    setError(null)
    setRetryCount(0)
    
    try {
      const response = await storiesApi.createJob(theme)
      setJobId(response.job_id)
      setStatus('pending')
      toast.info('Story generation initiated!')
      
      pollJobStatus(response.job_id)
    } catch (error) {
      toast.error('Failed to start story generation')
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setRetryCount(0)
    
    try {
      const response = await storiesApi.createJob(theme)
      setJobId(response.job_id)
      setStatus('pending')
      toast.info('Story generation initiated!')
      
      pollJobStatus(response.job_id)
    } catch (error) {
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
          toast.success('Your interactive story has been created!')
          
          try {
            await storiesApi.publishInteractiveStory(response.story_id!)
            toast.success('Story published successfully!')
          } catch (publishError) {
            console.error('Publishing error:', publishError)
          }
          
          setIsLoading(false)
          navigate(`/story/${response.story_id}`)
        } else if (response.status === 'failed') {
          if (response.error?.includes('Expecting') || 
              response.error?.includes('JSON') || 
              response.error?.includes('delimiter')) {
            
            if (retries < maxRetries) {
              retries++
              setRetryCount(retries)
              
              const messages = [
                'Adjusting the narrative...',
                'Trying a different approach...',
                'One more attempt...'
              ]
              toast.info(`${messages[retries-1]} Attempt ${retries}/${maxRetries}`)
              
              const waitTime = retries * 2000
              setTimeout(poll, waitTime)
            } else {
              generateSuggestions(theme)
              setError('Story generation failed due to format issues. Try one of these themes instead:')
              toast.error('Generation failed after multiple attempts. Please try a different theme.')
              setIsLoading(false)
            }
          } else {
            setError(`Generation failed: ${response.error}`)
            toast.error(`Generation failed: ${response.error}`)
            setIsLoading(false)
          }
        } else {
          setTimeout(poll, 2000)
        }
      } catch (error) {
        console.error('Polling error:', error)
        setTimeout(poll, 2000)
      }
    }

    poll()
  }

  const generateSuggestions = (originalTheme: string) => {
    const suggestions = [
      `${originalTheme} with a magical twist`,
      `The secret of ${originalTheme}`,
      `${originalTheme}: A new beginning`,
      `Legend of the ${originalTheme}`,
      `${originalTheme} and the ancient prophecy`,
    ]
    setSuggestedThemes(suggestions)
  }

  const trySuggestion = (suggestion: string) => {
    setTheme(suggestion)
    setError(null)
    setSuggestedThemes([])
    setJobId(null)
    setStatus(null)
    setRetryCount(0)
  }

  const resetForm = () => {
    setError(null)
    setJobId(null)
    setStatus(null)
    setRetryCount(0)
    setSuggestedThemes([])
    setIsLoading(false)
  }

  const popularThemes = [
    { emoji: '🐉', name: 'Dragon Adventure', prompt: 'an epic fantasy tale with dragons and ancient magic' },
    { emoji: '🚀', name: 'Space Mystery', prompt: 'a sci-fi mystery aboard a derelict spaceship' },
    { emoji: '🏰', name: 'Haunted Castle', prompt: 'a gothic horror story in an ancient castle' },
    { emoji: '🌊', name: 'Underwater Kingdom', prompt: 'an underwater adventure in a lost kingdom' },
    { emoji: '⏰', name: 'Time Travel', prompt: 'a time travel adventure with paradoxes' },
    { emoji: '🦸', name: 'Superhero Origin', prompt: 'an origin story of a new superhero' },
    { emoji: '🔮', name: 'Magical Academy', prompt: 'a story about students in a magic school' },
    { emoji: '🤖', name: 'Cyberpunk', prompt: 'a futuristic cyberpunk thriller' },
    { emoji: '🔍', name: 'Detective Noir', prompt: 'a hard-boiled detective mystery in 1940s New York' },
    { emoji: '🧙', name: 'Wizard\'s Quest', prompt: 'a wizard searching for a lost artifact' },
  ]
  
  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <BackButton />
        <div className="flex-1 text-center">
          <h1 className="text-3xl font-bold text-gray-900">Craft a New Interactive Story</h1>
        </div>
        <div className="w-20"></div>
      </div>

      <p className="text-lg text-gray-600 text-center mb-12">
        Enter a theme and watch as AI weaves an interactive tale just for you
      </p>

      <div className="bg-white rounded-2xl shadow-xl p-8 mb-12">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="theme" className="block text-sm font-medium text-gray-700 mb-2">
              Story Theme
            </label>
            <div className="relative">
              <input
                type="text"
                id="theme"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                placeholder="e.g., a detective solving a murder in Victorian London"
                className="input-field pr-12 py-4 text-lg"
                disabled={isLoading}
                required
              />
              <Sparkles className="absolute right-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Be specific for better results! Include genre, setting, and key elements.
            </p>
          </div>

          {jobId && !error && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {status === 'pending' || status === 'processing' ? (
                    <>
                      <Loader className="w-5 h-5 text-blue-500 animate-spin" />
                      <span className="text-blue-700 font-medium">
                        {status === 'pending' ? 'Queued for creation...' : 'Weaving your interactive narrative...'}
                      </span>
                    </>
                  ) : null}
                </div>
                {retryCount > 0 && (
                  <span className="text-sm text-blue-600">
                    Attempt {retryCount}/3
                  </span>
                )}
              </div>
              
              <div className="w-full h-2 bg-blue-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-600 transition-all duration-500"
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
                  
                  {suggestedThemes.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-red-700 mb-2">Try these variations:</p>
                      <div className="flex flex-wrap gap-2">
                        {suggestedThemes.map((suggestion, index) => (
                          <button
                            key={index}
                            onClick={() => trySuggestion(suggestion)}
                            className="px-3 py-1.5 bg-white border border-red-200 rounded-lg text-sm text-red-700 hover:bg-red-50 transition-colors"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center space-x-3">
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
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !theme.trim()}
            className="btn-primary w-full py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <Loader className="w-5 h-5 mr-2 animate-spin" />
                {retryCount > 0 ? `Retrying... (${retryCount}/3)` : 'Crafting Your Interactive Story...'}
              </span>
            ) : (
              <span className="flex items-center justify-center">
                <Sparkles className="w-5 h-5 mr-2" />
                Generate Interactive Story
              </span>
            )}
          </button>
        </form>
      </div>

      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Need Inspiration?
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {popularThemes.map((item) => (
            <button
              key={item.name}
              onClick={() => setTheme(item.prompt)}
              className="group p-4 bg-white rounded-xl shadow-md hover:shadow-xl transition-all transform hover:-translate-y-1 text-center"
              disabled={isLoading}
            >
              <span className="text-3xl mb-2 block group-hover:scale-110 transition-transform">
                {item.emoji}
              </span>
              <span className="text-xs font-medium text-gray-700">
                {item.name}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl p-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Sparkles className="w-5 h-5 mr-2 text-primary-600" />
          Pro Tips for Better Interactive Stories
        </h3>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="text-primary-600 font-bold mr-2">✓</span>
              <span className="text-gray-700"><span className="font-medium">Be specific:</span> "a dragon" → "an ancient ice dragon guarding a frozen temple"</span>
            </div>
            <div className="flex items-start">
              <span className="text-primary-600 font-bold mr-2">✓</span>
              <span className="text-gray-700"><span className="font-medium">Include genre:</span> fantasy, sci-fi, mystery, romance, horror</span>
            </div>
            <div className="flex items-start">
              <span className="text-primary-600 font-bold mr-2">✓</span>
              <span className="text-gray-700"><span className="font-medium">Add setting:</span> Victorian London, cyberpunk Tokyo, magical academy</span>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="text-primary-600 font-bold mr-2">✓</span>
              <span className="text-gray-700"><span className="font-medium">Mention mood:</span> dark and gritty, light-hearted, suspenseful</span>
            </div>
            <div className="flex items-start">
              <span className="text-primary-600 font-bold mr-2">✓</span>
              <span className="text-gray-700"><span className="font-medium">Add characters:</span> a reluctant hero, a mysterious villain</span>
            </div>
            <div className="flex items-start">
              <span className="text-primary-600 font-bold mr-2">✓</span>
              <span className="text-gray-700"><span className="font-medium">Include conflict:</span> man vs nature, good vs evil, internal struggle</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CreateStory