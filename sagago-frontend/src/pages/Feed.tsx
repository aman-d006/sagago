import { useState, useEffect, useRef } from 'react'
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
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const [timeframe, setTimeframe] = useState('week')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const loaderRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const cachedFeed = localStorage.getItem(`feed_cache_${activeTab}_${timeframe}`)
    if (cachedFeed) {
      try {
        const { data, timestamp } = JSON.parse(cachedFeed)
        if (Date.now() - timestamp < 60000) {
          setStories(data)
          setIsLoading(false)
          setIsInitialLoad(false)
        }
      } catch (e) {
        console.error('Error parsing cached feed:', e)
      }
    }
    fetchFeed(true)
  }, [activeTab, timeframe])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && !isLoading) {
          fetchMore()
        }
      },
      { threshold: 0.5 }
    )

    if (loaderRef.current) {
      observer.observe(loaderRef.current)
    }

    return () => observer.disconnect()
  }, [hasMore, loadingMore, isLoading])

  const fetchFeed = async (reset = true) => {
    if (reset) {
      setIsLoading(true)
      setPage(1)
    } else {
      setLoadingMore(true)
    }
    
    try {
      let response
      const currentPage = reset ? 1 : page + 1
      
      switch (activeTab) {
        case 'following':
          response = await storiesApi.getFollowingFeed(currentPage)
          break
        case 'popular':
          response = await storiesApi.getPopularFeed(timeframe, currentPage)
          break
        case 'trending':
          response = await storiesApi.getFeed('trending', timeframe, currentPage)
          break
        default:
          response = await storiesApi.getLatestFeed(currentPage)
      }
      
      if (response) {
        if (reset) {
          setStories(response.stories || [])
          localStorage.setItem(`feed_cache_${activeTab}_${timeframe}`, JSON.stringify({
            data: response.stories || [],
            timestamp: Date.now()
          }))
        } else {
          setStories(prev => [...prev, ...(response.stories || [])])
        }
        setPage(response.page || 1)
        setHasMore(response.page < response.pages)
      }
    } catch (error) {
      console.error('Failed to fetch feed:', error)
    } finally {
      setIsLoading(false)
      setIsInitialLoad(false)
      setLoadingMore(false)
    }
  }

  const fetchMore = () => {
    if (!loadingMore && hasMore) {
      fetchFeed(false)
    }
  }

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab)
    setPage(1)
    setHasMore(false)
  }

  const tabs = [
    { id: 'latest', label: 'Latest', icon: Clock },
    { id: 'popular', label: 'Popular', icon: Star },
    { id: 'trending', label: 'Trending', icon: TrendingUp },
    { id: 'following', label: 'Following', icon: Users },
  ]

  if (isInitialLoad && isLoading) {
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

      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 mb-6">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id as any)}
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

      {stories.length === 0 && !isLoading ? (
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
                    {story.view_count || 0}
                  </span>
                  <span className="flex items-center">
                    <Heart className="w-4 h-4 mr-1" />
                    {story.like_count || 0}
                  </span>
                  <span className="flex items-center">
                    <MessageCircle className="w-4 h-4 mr-1" />
                    {story.comment_count || 0}
                  </span>
                </div>
                <span className="text-gray-400 text-xs">
                  by {story.author?.username || 'Unknown'} • {story.created_at ? new Date(story.created_at).toLocaleDateString() : 'Unknown date'}
                </span>
              </div>
            </div>
          ))}
          
          {hasMore && (
            <div ref={loaderRef} className="flex justify-center py-4">
              {loadingMore ? (
                <Loader className="w-5 h-5 text-primary-600 animate-spin" />
              ) : (
                <div className="h-10"></div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Feed