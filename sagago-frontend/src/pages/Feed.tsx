import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { storiesApi } from '../api/stories'
import BackButton from '../components/ui/BackButton'
import { 
  Loader, 
  TrendingUp, 
  Star, 
  Clock, 
  Users,
  Eye,
  Heart,
  MessageCircle
} from 'lucide-react'
import type { Story } from '../types'

const Feed = () => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'following' | 'popular' | 'latest' | 'trending'>('latest')
  const [stories, setStories] = useState<Story[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [timeframe, setTimeframe] = useState('week')

  useEffect(() => {
    fetchFeed()
  }, [activeTab, timeframe])

  const fetchFeed = async () => {
    setIsLoading(true)
    try {
      let response
      switch (activeTab) {
        case 'following':
          response = await storiesApi.getFollowingFeed(1)
          break
        case 'popular':
          response = await storiesApi.getPopularFeed(timeframe, 1)
          break
        case 'trending':
          response = await storiesApi.getFeed('trending', timeframe, 1)
          break
        default:
          response = await storiesApi.getLatestFeed(1)
      }
      setStories(response.stories)
    } catch (error) {
      console.error('Failed to fetch feed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const tabs = [
    { id: 'latest', label: 'Latest', icon: Clock },
    { id: 'popular', label: 'Popular', icon: Star },
    { id: 'trending', label: 'Trending', icon: TrendingUp },
    { id: 'following', label: 'Following', icon: Users },
  ]

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <BackButton />
        <h1 className="text-2xl font-bold text-gray-900">Story Feed</h1>
        <div className="w-20"></div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 mb-6">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Timeframe Filter (for popular/trending) */}
      {(activeTab === 'popular' || activeTab === 'trending') && (
        <div className="flex justify-end space-x-2 mb-6">
          {['today', 'week', 'month', 'all'].map(t => (
            <button
              key={t}
              onClick={() => setTimeframe(t)}
              className={`px-3 py-1 rounded-lg text-xs capitalize ${
                timeframe === t
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {/* Stories List */}
      {stories.length === 0 ? (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <p className="text-gray-500">No stories found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {stories.map(story => (
            <div
              key={story.id}
              onClick={() => navigate(`/story/${story.id}`)}
              className="bg-white rounded-lg shadow-md hover:shadow-xl transition-all cursor-pointer p-6"
            >
              <h3 className="text-xl font-semibold text-gray-900 mb-2">{story.title}</h3>
              <p className="text-gray-600 mb-4 line-clamp-2">{story.excerpt}</p>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-4 text-gray-500">
                  <span className="flex items-center">
                    <Eye className="w-4 h-4 mr-1" />
                    {story.view_count}
                  </span>
                  <span className="flex items-center">
                    <Heart className="w-4 h-4 mr-1" />
                    {story.like_count}
                  </span>
                  <span className="flex items-center">
                    <MessageCircle className="w-4 h-4 mr-1" />
                    {story.comment_count}
                  </span>
                </div>
                <span className="text-gray-400 text-xs">
                  by {story.author?.username} • {new Date(story.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Feed