import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { storiesApi } from '../api/stories'
import BackButton from '../components/ui/BackButton'
import StoryCard from '../components/stories/StoryCard'
import { 
  Loader, 
  BookOpen, 
  Filter,
  TrendingUp,
  Clock,
  Star,
  Users
} from 'lucide-react'
import type { Story } from '../types'

const genreIcons: Record<string, { icon: string; color: string }> = {
  fantasy: { icon: '🧙', color: 'from-purple-500 to-indigo-500' },
  'sci-fi': { icon: '🚀', color: 'from-blue-500 to-cyan-500' },
  mystery: { icon: '🔍', color: 'from-gray-700 to-gray-900' },
  romance: { icon: '❤️', color: 'from-pink-500 to-rose-500' },
  horror: { icon: '👻', color: 'from-red-700 to-red-900' },
  adventure: { icon: '⚔️', color: 'from-green-500 to-emerald-500' },
  thriller: { icon: '🔪', color: 'from-red-600 to-orange-600' },
  comedy: { icon: '😄', color: 'from-yellow-500 to-orange-500' },
  drama: { icon: '🎭', color: 'from-amber-600 to-amber-800' },
  historical: { icon: '📜', color: 'from-amber-700 to-yellow-800' },
  poetry: { icon: '📝', color: 'from-indigo-500 to-purple-500' },
  children: { icon: '🧸', color: 'from-blue-400 to-green-400' }
}

const GenrePage = () => {
  const { genre } = useParams<{ genre: string }>()
  const navigate = useNavigate()
  const [stories, setStories] = useState<Story[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [sortBy, setSortBy] = useState<'latest' | 'popular' | 'trending'>('latest')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)

  useEffect(() => {
    if (genre) {
      fetchStories()
    }
  }, [genre, sortBy])

  const fetchStories = async (pageNum: number = 1) => {
    if (pageNum === 1) {
      setIsLoading(true)
    } else {
      setIsLoadingMore(true)
    }

    try {
      let response
      switch (sortBy) {
        case 'popular':
          response = await storiesApi.getPopularFeed('week', pageNum)
          break
        case 'trending':
          response = await storiesApi.getFeed('trending', 'week', pageNum)
          break
        default:
          response = await storiesApi.getLatestFeed(pageNum)
      }

      const genreStories = response.stories.filter((s: Story) => 
        s.genre?.toLowerCase() === genre?.toLowerCase()
      )

      if (pageNum === 1) {
        setStories(genreStories)
      } else {
        setStories(prev => [...prev, ...genreStories])
      }

      setHasMore(genreStories.length === 20)
      setPage(pageNum)
    } catch (error) {
      console.error('Failed to fetch stories:', error)
    } finally {
      setIsLoading(false)
      setIsLoadingMore(false)
    }
  }

  const loadMore = () => {
    if (hasMore && !isLoadingMore) {
      fetchStories(page + 1)
    }
  }

  const genreInfo = genreIcons[genre?.toLowerCase() || ''] || {
    icon: '📚',
    color: 'from-gray-500 to-gray-700'
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <BackButton />
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${genreInfo.color} flex items-center justify-center text-white text-xl`}>
            {genreInfo.icon}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 capitalize">{genre}</h1>
            <p className="text-gray-500">{stories.length} stories</p>
          </div>
        </div>
      </div>

      <div className="flex gap-6">
        <div className="flex-1">
          <div className="flex justify-end mb-6">
            <div className="flex space-x-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setSortBy('latest')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm transition-colors ${
                  sortBy === 'latest' ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-600'
                }`}
              >
                <Clock className="w-4 h-4" />
                <span>Latest</span>
              </button>
              <button
                onClick={() => setSortBy('popular')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm transition-colors ${
                  sortBy === 'popular' ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-600'
                }`}
              >
                <Star className="w-4 h-4" />
                <span>Popular</span>
              </button>
              <button
                onClick={() => setSortBy('trending')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm transition-colors ${
                  sortBy === 'trending' ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-600'
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                <span>Trending</span>
              </button>
            </div>
          </div>

          {stories.length === 0 ? (
            <div className="bg-white rounded-lg shadow-lg p-12 text-center">
              <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No stories found</h3>
              <p className="text-gray-500 mb-6">
                Be the first to write a {genre} story!
              </p>
              <button
                onClick={() => navigate('/create')}
                className="btn-primary px-6 py-3"
              >
                Write a Story
              </button>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {stories.map((story, index) => (
                  <div
                    key={story.id}
                    ref={index === stories.length - 1 ? loadMore : undefined}
                  >
                    <StoryCard story={story} viewMode="grid" />
                  </div>
                ))}
              </div>

              {isLoadingMore && (
                <div className="flex justify-center py-8">
                  <Loader className="w-6 h-6 text-primary-600 animate-spin" />
                </div>
              )}
            </>
          )}
        </div>

        <div className="hidden lg:block w-80 flex-shrink-0">
          <div className="sticky top-24 space-y-6">
            <div className={`bg-gradient-to-br ${genreInfo.color} rounded-xl p-6 text-white`}>
              <span className="text-6xl mb-4 block">{genreInfo.icon}</span>
              <h3 className="text-2xl font-bold capitalize mb-2">{genre}</h3>
              <p className="text-white/90">
                Explore the best {genre} stories from our community.
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6">
              <h4 className="font-semibold text-gray-900 mb-4">Popular in {genre}</h4>
              <div className="space-y-4">
                {stories.slice(0, 3).map((story) => (
                  <div
                    key={story.id}
                    onClick={() => navigate(`/story/${story.id}`)}
                    className="flex items-start space-x-3 cursor-pointer group"
                  >
                    <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-primary-600 font-bold">
                        {story.view_count}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 group-hover:text-primary-600 transition-colors line-clamp-1">
                        {story.title}
                      </p>
                      <p className="text-xs text-gray-500">
                        by {story.author?.username}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6">
              <h4 className="font-semibold text-gray-900 mb-4">Genre Stats</h4>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Total Stories</span>
                  <span className="font-medium">{stories.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Total Views</span>
                  <span className="font-medium">
                    {stories.reduce((acc, s) => acc + (s.view_count || 0), 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Total Likes</span>
                  <span className="font-medium">
                    {stories.reduce((acc, s) => acc + (s.like_count || 0), 0)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GenrePage