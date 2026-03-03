import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { storiesApi } from '../api/stories'
import { 
  Loader, 
  Heart, 
  MessageCircle, 
  Eye, 
  Share2,
  Bookmark,
  Clock,
  User,
  Calendar,
  Tags,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import type { Story } from '../types'

const FullStoryReader = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [story, setStory] = useState<Story | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLiked, setIsLiked] = useState(false)
  const [likeCount, setLikeCount] = useState(0)
  const [fontSize, setFontSize] = useState(100)
  const [theme, setTheme] = useState<'light' | 'sepia' | 'dark'>('light')

  useEffect(() => {
    if (id) {
      fetchStory()
    }
  }, [id])

  const fetchStory = async () => {
    try {
      const data = await storiesApi.getStory(parseInt(id!))
      setStory(data)
      setIsLiked(data.is_liked_by_current_user || false)
      setLikeCount(data.like_count || 0)
    } catch (error) {
      toast.error('Failed to load story')
      navigate('/')
    } finally {
      setIsLoading(false)
    }
  }

  const handleLike = async () => {
    try {
      const response = await storiesApi.likeStory(parseInt(id!))
      setIsLiked(response.liked)
      setLikeCount(response.like_count)
    } catch (error) {
      toast.error('Failed to like story')
    }
  }

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href)
    toast.success('Story link copied to clipboard!')
  }

  const getThemeStyles = () => {
    switch (theme) {
      case 'sepia':
        return 'bg-amber-50 text-amber-900'
      case 'dark':
        return 'bg-gray-900 text-gray-100'
      default:
        return 'bg-white text-gray-900'
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  if (!story) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900">Story not found</h2>
        <button onClick={() => navigate('/')} className="btn-primary mt-4">
          Return Home
        </button>
      </div>
    )
  }

  const authorName = story.author?.full_name || story.author?.username || 'Unknown Author'
  const readingTime = story.reading_time || Math.ceil((story.content?.split(' ').length || 0) / 200)

  return (
    <div className={`min-h-screen transition-colors duration-300 ${getThemeStyles()}`}>
      {/* Reading Controls */}
      <div className="fixed top-0 left-0 right-0 bg-white/95 dark:bg-gray-800/95 backdrop-blur-md border-b border-gray-200 dark:border-gray-700 z-50">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-4">
              {/* Font Size */}
              <div className="hidden sm:flex items-center space-x-2">
                <button
                  onClick={() => setFontSize(Math.max(80, fontSize - 10))}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  A-
                </button>
                <span className="text-sm">{fontSize}%</span>
                <button
                  onClick={() => setFontSize(Math.min(150, fontSize + 10))}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  A+
                </button>
              </div>

              {/* Theme */}
              <div className="hidden sm:flex items-center space-x-2">
                <button
                  onClick={() => setTheme('light')}
                  className={`p-2 rounded-full ${theme === 'light' ? 'bg-primary-100' : 'hover:bg-gray-100'}`}
                >
                  <div className="w-4 h-4 bg-white border rounded" />
                </button>
                <button
                  onClick={() => setTheme('sepia')}
                  className={`p-2 rounded-full ${theme === 'sepia' ? 'bg-primary-100' : 'hover:bg-gray-100'}`}
                >
                  <div className="w-4 h-4 bg-amber-50 border border-amber-200 rounded" />
                </button>
                <button
                  onClick={() => setTheme('dark')}
                  className={`p-2 rounded-full ${theme === 'dark' ? 'bg-primary-100' : 'hover:bg-gray-100'}`}
                >
                  <div className="w-4 h-4 bg-gray-800 border border-gray-600 rounded" />
                </button>
              </div>

              {/* Actions */}
              <button
                onClick={handleLike}
                className={`p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 ${
                  isLiked ? 'text-red-500' : ''
                }`}
              >
                <Heart className={`w-5 h-5 ${isLiked ? 'fill-red-500' : ''}`} />
              </button>
              <button
                onClick={handleShare}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full"
              >
                <Share2 className="w-5 h-5" />
              </button>
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full">
                <Bookmark className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 pt-20 pb-12">
        <div className="max-w-3xl mx-auto">
          {/* Cover Image */}
          {story.cover_image && (
            <div className="mb-8 rounded-xl overflow-hidden shadow-lg">
              <img src={story.cover_image} alt={story.title} className="w-full h-80 object-cover" />
            </div>
          )}

          {/* Title Section */}
          <div className="text-center mb-8">
            <h1 className={`text-4xl md:text-5xl font-bold mb-4 ${
              theme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              {story.title}
            </h1>
            
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
              <span className="flex items-center">
                <User className="w-4 h-4 mr-1" />
                {authorName}
              </span>
              <span className="flex items-center">
                <Calendar className="w-4 h-4 mr-1" />
                {new Date(story.created_at).toLocaleDateString()}
              </span>
              <span className="flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                {readingTime} min read
              </span>
            </div>

            {/* Stats */}
            <div className="flex items-center justify-center space-x-6 mt-4 text-sm">
              <span className="flex items-center text-gray-500">
                <Eye className="w-4 h-4 mr-1" />
                {story.view_count} views
              </span>
              <button
                onClick={handleLike}
                className={`flex items-center ${
                  isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
                } transition-colors`}
              >
                <Heart className={`w-4 h-4 mr-1 ${isLiked ? 'fill-red-500' : ''}`} />
                {likeCount} likes
              </button>
              <span className="flex items-center text-gray-500">
                <MessageCircle className="w-4 h-4 mr-1" />
                {story.comment_count} comments
              </span>
            </div>

            {/* Tags */}
            {story.tags && story.tags.length > 0 && (
              <div className="flex items-center justify-center space-x-2 mt-4">
                <Tags className="w-4 h-4 text-gray-400" />
                {story.tags.map(tag => (
                  <span key={tag} className="text-sm text-primary-600">#{tag}</span>
                ))}
              </div>
            )}
          </div>

          {/* Story Content */}
          <div 
            className={`prose prose-lg max-w-none ${
              theme === 'dark' ? 'prose-invert' : ''
            }`}
            style={{ fontSize: `${fontSize}%` }}
          >
            {story.content.split('\n').map((paragraph, idx) => (
              <p key={idx} className="mb-6 leading-relaxed">
                {paragraph}
              </p>
            ))}
          </div>

          {/* Footer */}
          <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <button
                onClick={() => navigate(-1)}
                className="text-gray-500 hover:text-gray-700 flex items-center"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Back
              </button>
              <span className="text-sm text-gray-400">
                Published by {authorName}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FullStoryReader