import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { storiesApi } from '../api/stories'
import { useAuthStore } from '../stores/authStore'
import CommentSection from '../components/comments/CommentSection'
import BookmarkButton from '../components/stories/BookmarkButton'
import { getImageUrl } from '../utils/imageHelpers'
import { 
  Loader, 
  Heart, 
  MessageCircle, 
  Eye, 
  Share2,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Clock,
  User,
  Calendar,
  AlertCircle,
  Sparkles,
  BookOpen,
  Edit2
} from 'lucide-react'
import type { Story, StoryNode } from '../types'

const StoryReader = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [story, setStory] = useState<Story | null>(null)
  const [currentNode, setCurrentNode] = useState<StoryNode | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isLiked, setIsLiked] = useState(false)
  const [likeCount, setLikeCount] = useState(0)
  const [commentCount, setCommentCount] = useState(0)
  const [showSidebar, setShowSidebar] = useState(false)
  const [readingTime, setReadingTime] = useState(0)
  const [fontSize, setFontSize] = useState(100)
  const [theme, setTheme] = useState<'light' | 'sepia' | 'dark'>('light')
  const [storyType, setStoryType] = useState<'interactive' | 'written'>('interactive')

  useEffect(() => {
    if (id) {
      fetchStory()
    } else {
      setError('No story ID provided')
      setIsLoading(false)
    }
  }, [id])

  useEffect(() => {
    if (currentNode?.content) {
      const words = currentNode.content.split(' ').length
      const minutes = Math.ceil(words / 200)
      setReadingTime(minutes)
    }
  }, [currentNode])

  const fetchStory = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const storyId = parseInt(id!)
      
      if (isNaN(storyId)) {
        throw new Error('Invalid story ID')
      }
      
      const metadata = await storiesApi.getStoryMetadata(storyId)
      
      let data
      if (metadata.story_type === 'interactive') {
        data = await storiesApi.getInteractiveStory(storyId)
      } else {
        data = await storiesApi.getFullStory(storyId)
      }
      
      if (!data) {
        throw new Error('No data received from server')
      }
      
      if (!data.author) {
        data.author = {
          id: 0,
          username: 'Unknown Author',
          full_name: 'Unknown Author'
        }
      }
      
      if (data.root_node) {
        setStoryType('interactive')
        setCurrentNode(data.root_node)
      } else {
        setStoryType('written')
      }
      
      setStory(data)
      setIsLiked(data.is_liked_by_current_user || false)
      setLikeCount(data.like_count || 0)
      setCommentCount(data.comment_count || 0)
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load story'
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleChoice = (nodeId: number) => {
    if (story?.all_nodes && story.all_nodes[nodeId]) {
      setCurrentNode(story.all_nodes[nodeId])
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const handleLike = async () => {
    if (!id) return
    try {
      const response = await storiesApi.likeStory(parseInt(id))
      setIsLiked(response.liked)
      setLikeCount(response.like_count)
      toast.success(response.message)
    } catch (error) {
      toast.error('Failed to like story')
    }
  }

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href)
    toast.success('Story link copied to clipboard!')
  }

  const handleRestart = () => {
    if (story?.root_node) {
      setCurrentNode(story.root_node)
      toast.info('Starting your journey anew...')
    }
  }

  const handleGoBack = () => {
    navigate(-1)
  }

  const handleEdit = () => {
    navigate(`/edit-story/${id}`)
  }

  const getThemeStyles = () => {
    switch (theme) {
      case 'sepia':
        return {
          bg: 'bg-amber-50',
          text: 'text-amber-900',
          card: 'bg-amber-100/50',
          border: 'border-amber-200',
          hover: 'hover:bg-amber-200',
          prose: 'prose-amber'
        }
      case 'dark':
        return {
          bg: 'bg-gray-900',
          text: 'text-gray-100',
          card: 'bg-gray-800',
          border: 'border-gray-700',
          hover: 'hover:bg-gray-700',
          prose: 'prose-invert'
        }
      default:
        return {
          bg: 'bg-white',
          text: 'text-gray-900',
          card: 'bg-gray-50',
          border: 'border-gray-200',
          hover: 'hover:bg-gray-100',
          prose: ''
        }
    }
  }

  const styles = getThemeStyles()
  const coverImageUrl = getImageUrl(story?.cover_image)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading your story...</p>
        </div>
      </div>
    )
  }

  if (error || !story) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Story Not Found</h2>
          <p className="text-gray-600 mb-6">{error || 'The story you\'re looking for doesn\'t exist or has been removed.'}</p>
          <div className="space-y-3">
            <button
              onClick={handleGoBack}
              className="btn-primary w-full"
            >
              Go Back
            </button>
            <button
              onClick={() => navigate('/')}
              className="btn-secondary w-full"
            >
              Return Home
            </button>
          </div>
        </div>
      </div>
    )
  }

  const authorUsername = story.author?.username || 'Unknown Author'
  const authorFullName = story.author?.full_name || story.author?.username || 'Unknown Author'
  const viewCount = story.view_count || 0
  const createdAt = story.created_at ? new Date(story.created_at).toLocaleDateString() : 'Unknown date'
  const isInteractive = storyType === 'interactive' && currentNode
  const isAuthor = user?.id === story.author?.id

  return (
    <div className={`min-h-screen transition-colors duration-300 ${styles.bg} ${styles.text}`}>
      <div className={`fixed top-0 left-0 right-0 backdrop-blur-md border-b z-[100] shadow-sm ${
        theme === 'dark' 
          ? 'bg-gray-800/95 border-gray-700' 
          : theme === 'sepia'
          ? 'bg-amber-100/95 border-amber-200'
          : 'bg-white/95 border-gray-200'
      }`}>
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleGoBack}
                className={`p-2 rounded-full transition-colors ${
                  theme === 'dark' 
                    ? 'hover:bg-gray-700' 
                    : theme === 'sepia'
                    ? 'hover:bg-amber-200'
                    : 'hover:bg-gray-100'
                }`}
                aria-label="Go back"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <div className="hidden sm:block">
                <h1 className="text-sm font-medium line-clamp-1">{story.title}</h1>
                <p className={`text-xs ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  by {authorUsername}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-4">
              {isInteractive && (
                <span className={`hidden sm:flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${
                  theme === 'dark'
                    ? 'bg-purple-900/30 text-purple-300'
                    : theme === 'sepia'
                    ? 'bg-purple-200 text-purple-800'
                    : 'bg-purple-100 text-purple-700'
                }`}>
                  <Sparkles className="w-3 h-3" />
                  <span>Interactive</span>
                </span>
              )}
              
              {isAuthor && (
                <button
                  onClick={handleEdit}
                  className={`p-2 rounded-full transition-colors ${
                    theme === 'dark'
                      ? 'hover:bg-gray-700 text-gray-300'
                      : theme === 'sepia'
                      ? 'hover:bg-amber-200 text-amber-800'
                      : 'hover:bg-gray-100 text-gray-600'
                  }`}
                  title="Edit Story"
                >
                  <Edit2 className="w-5 h-5" />
                </button>
              )}
              
              <div className={`hidden sm:flex items-center space-x-2 pr-4 border-r ${
                theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
              }`}>
                <button
                  onClick={() => setFontSize(Math.max(80, fontSize - 10))}
                  className={`p-1.5 rounded transition-colors ${
                    theme === 'dark' 
                      ? 'hover:bg-gray-700' 
                      : theme === 'sepia'
                      ? 'hover:bg-amber-200'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <span className="text-sm font-medium">A-</span>
                </button>
                <span className={`text-xs min-w-[40px] text-center ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  {fontSize}%
                </span>
                <button
                  onClick={() => setFontSize(Math.min(150, fontSize + 10))}
                  className={`p-1.5 rounded transition-colors ${
                    theme === 'dark' 
                      ? 'hover:bg-gray-700' 
                      : theme === 'sepia'
                      ? 'hover:bg-amber-200'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <span className="text-sm font-medium">A+</span>
                </button>
              </div>
              
              <div className={`hidden sm:flex items-center space-x-2 pr-4 border-r ${
                theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
              }`}>
                <button
                  onClick={() => setTheme('light')}
                  className={`p-2 rounded-full transition-colors ${
                    theme === 'light' 
                      ? 'bg-primary-100 text-primary-600 ring-2 ring-primary-200' 
                      : theme === 'dark'
                      ? 'hover:bg-gray-700'
                      : 'hover:bg-gray-100'
                  }`}
                  title="Light mode"
                >
                  <div className="w-4 h-4 bg-white border border-gray-300 rounded" />
                </button>
                <button
                  onClick={() => setTheme('sepia')}
                  className={`p-2 rounded-full transition-colors ${
                    theme === 'sepia' 
                      ? 'bg-primary-100 text-primary-600 ring-2 ring-primary-200' 
                      : theme === 'dark'
                      ? 'hover:bg-gray-700'
                      : 'hover:bg-gray-100'
                  }`}
                  title="Sepia mode"
                >
                  <div className="w-4 h-4 bg-amber-50 border border-amber-200 rounded" />
                </button>
                <button
                  onClick={() => setTheme('dark')}
                  className={`p-2 rounded-full transition-colors ${
                    theme === 'dark' 
                      ? 'bg-primary-900 text-primary-200 ring-2 ring-primary-700' 
                      : 'hover:bg-gray-100'
                  }`}
                  title="Dark mode"
                >
                  <div className="w-4 h-4 bg-gray-800 border border-gray-600 rounded" />
                </button>
              </div>
              
              <div className="flex items-center space-x-1 sm:space-x-2">
                <BookmarkButton storyId={parseInt(id!)} />
                <button
                  onClick={handleLike}
                  className={`p-2 rounded-full transition-colors ${
                    isLiked 
                      ? 'text-red-500' 
                      : theme === 'dark'
                      ? 'hover:bg-gray-700'
                      : theme === 'sepia'
                      ? 'hover:bg-amber-200'
                      : 'hover:bg-gray-100'
                  }`}
                  title={isLiked ? 'Unlike' : 'Like'}
                >
                  <Heart className={`w-5 h-5 ${isLiked ? 'fill-red-500' : ''}`} />
                  <span className="hidden sm:inline ml-1 text-sm">{likeCount}</span>
                </button>
                <button
                  onClick={handleShare}
                  className={`p-2 rounded-full transition-colors ${
                    theme === 'dark'
                      ? 'hover:bg-gray-700'
                      : theme === 'sepia'
                      ? 'hover:bg-amber-200'
                      : 'hover:bg-gray-100'
                  }`}
                  title="Share"
                >
                  <Share2 className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setShowSidebar(!showSidebar)}
                  className="lg:hidden p-2 rounded-full transition-colors"
                >
                  {showSidebar ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 pt-24 pb-12">
        <div className="flex gap-8">
          <div className="hidden lg:block w-64 flex-shrink-0">
            <div className="sticky top-24 space-y-6">
              <div className={`p-6 rounded-xl ${styles.card}`}>
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-xl font-bold text-primary-600">
                      {authorUsername.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <h3 className={`font-semibold ${styles.text}`}>{authorFullName}</h3>
                    <p className={`text-sm ${
                      theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      @{authorUsername}
                    </p>
                  </div>
                </div>
              </div>

              <div className={`p-6 rounded-xl ${styles.card}`}>
                <h4 className="font-semibold mb-3">Story Stats</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>Views</span>
                    <span className="font-medium">{viewCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>Likes</span>
                    <span className="font-medium">{likeCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>Comments</span>
                    <span className="font-medium">{commentCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>Published</span>
                    <span className="font-medium">{createdAt}</span>
                  </div>
                </div>
              </div>

              <div className={`p-6 rounded-xl ${styles.card}`}>
                <h4 className="font-semibold mb-3">Reading Time</h4>
                <div className="flex items-center text-sm">
                  <Clock className="w-4 h-4 mr-2 opacity-70" />
                  <span>{readingTime} min read</span>
                </div>
                {isInteractive && currentNode?.is_ending && (
                  <div className={`mt-3 pt-3 border-t ${styles.border}`}>
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                      currentNode.is_winning_ending 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-orange-100 text-orange-700'
                    }`}>
                      {currentNode.is_winning_ending ? '🏆 Victory Ending' : '📖 Story Complete'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex-1 max-w-3xl mx-auto">
            <div className="mb-8 text-center">
              <h1 className={`text-4xl md:text-5xl font-bold mb-4 ${styles.text}`}>
                {story.title}
              </h1>
              <div className="flex items-center justify-center space-x-4 text-sm">
                <span className="flex items-center">
                  <User className="w-4 h-4 mr-1 opacity-70" />
                  {authorUsername}
                </span>
                <span className="flex items-center">
                  <Calendar className="w-4 h-4 mr-1 opacity-70" />
                  {createdAt}
                </span>
                <span className="flex items-center">
                  <Clock className="w-4 h-4 mr-1 opacity-70" />
                  {readingTime} min read
                </span>
              </div>
            </div>

            {coverImageUrl && (
              <div className="mb-8 rounded-lg overflow-hidden bg-gray-100">
                <img 
                  src={coverImageUrl} 
                  alt={story.title} 
                  className="w-full h-80 object-contain mx-auto"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                    const parent = e.currentTarget.parentElement
                    if (parent) {
                      parent.innerHTML = '<div class="w-full h-80 flex items-center justify-center text-gray-400">Failed to load image</div>'
                    }
                  }}
                />
              </div>
            )}

            {isInteractive ? (
              <>
                <div 
                  className={`prose prose-lg max-w-none mb-12 ${styles.prose}`}
                  style={{ fontSize: `${fontSize}%` }}
                >
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {currentNode?.content}
                  </div>
                </div>

                {!currentNode?.is_ending ? (
                  <div className="mt-12">
                    <h3 className={`text-xl font-semibold mb-6 text-center ${styles.text}`}>
                      What happens next?
                    </h3>
                    <div className="space-y-4">
                      {currentNode?.options?.map((option, index) => (
                        <button
                          key={`${option.node_id}-${index}`}
                          onClick={() => handleChoice(option.node_id)}
                          className={`w-full p-6 text-left rounded-xl transition-all transform hover:scale-[1.02] ${
                            theme === 'dark'
                              ? 'bg-gray-800 hover:bg-gray-700 border border-gray-700'
                              : theme === 'sepia'
                              ? 'bg-amber-100 hover:bg-amber-200 border border-amber-200'
                              : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
                          }`}
                        >
                          <div className="flex items-center">
                            <span className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mr-4 font-semibold ${
                              theme === 'dark'
                                ? 'bg-gray-700 text-gray-300'
                                : theme === 'sepia'
                                ? 'bg-amber-200 text-amber-800'
                                : 'bg-gray-200 text-gray-700'
                            }`}>
                              {String.fromCharCode(65 + index)}
                            </span>
                            <span className="text-lg">{option.text}</span>
                            <ChevronRight className="w-5 h-5 ml-auto opacity-50" />
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="mt-16 text-center">
                    <div className="mb-8">
                      <span className="text-8xl">
                        {currentNode.is_winning_ending ? '🏆' : '📚'}
                      </span>
                    </div>
                    <h2 className={`text-3xl font-bold mb-4 ${
                      currentNode.is_winning_ending ? 'text-green-600' : 'text-orange-600'
                    }`}>
                      {currentNode.is_winning_ending ? 'The Victorious End' : 'The Journey Ends'}
                    </h2>
                    <p className={`text-lg mb-8 max-w-md mx-auto ${
                      theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      {currentNode.is_winning_ending
                        ? 'Your choices have led you to a triumphant conclusion. A tale well told!'
                        : 'Every story finds its ending. Thank you for reading!'}
                    </p>
                    <div className="flex items-center justify-center space-x-4">
                      <button
                        onClick={handleRestart}
                        className="btn-primary px-8 py-3 text-lg"
                      >
                        Read Again
                      </button>
                      <button
                        onClick={() => navigate('/')}
                        className="btn-secondary px-8 py-3 text-lg"
                      >
                        More Stories
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div 
                className={`prose prose-lg max-w-none ${styles.prose}`}
                style={{ fontSize: `${fontSize}%` }}
              >
                {story.content ? (
                  story.content.split('\n').map((paragraph, idx) => (
                    <p key={idx} className="mb-6 leading-relaxed">
                      {paragraph}
                    </p>
                  ))
                ) : (
                  <p className="text-gray-500 italic">No content available</p>
                )}
              </div>
            )}

            <div className="mt-12">
              <CommentSection 
                storyId={parseInt(id!)} 
                commentCount={commentCount}
                onCommentCountChange={(newCount) => {
                  setCommentCount(newCount)
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {showSidebar && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowSidebar(false)} />
          <div className={`absolute right-0 top-0 h-full w-80 p-6 overflow-y-auto ${
            theme === 'dark' ? 'bg-gray-900' : 'bg-white'
          }`}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold">Story Info</h3>
              <button
                onClick={() => setShowSidebar(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className={`p-4 rounded-xl mb-4 ${theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-lg font-bold text-primary-600">
                    {authorUsername.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <h4 className="font-medium">{authorFullName}</h4>
                  <p className="text-xs text-gray-500">@{authorUsername}</p>
                </div>
              </div>
            </div>

            <div className={`p-4 rounded-xl ${theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <h4 className="font-medium mb-3">Story Stats</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Views</span>
                  <span>{viewCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Likes</span>
                  <span>{likeCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Comments</span>
                  <span>{commentCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Published</span>
                  <span>{createdAt}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StoryReader