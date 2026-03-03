import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { storiesApi } from '../api/stories'
import { useAuthStore } from '../stores/authStore'
import BackButton from '../components/ui/BackButton'
import CreateStoryModal from '../components/stories/CreateStoryModal'
import StoryCard from '../components/stories/StoryCard'
import { 
  Loader, 
  Search, 
  Filter,
  Grid,
  List,
  Sparkles,
  PenTool,
  ChevronDown,
  BookOpen
} from 'lucide-react'
import type { Story } from '../types'

const Explore = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [stories, setStories] = useState<Story[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [total, setTotal] = useState(0)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedGenre, setSelectedGenre] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'latest' | 'popular' | 'trending'>('latest')
  
  const observer = useRef<IntersectionObserver>()
  const lastStoryRef = useCallback((node: HTMLDivElement) => {
    if (isLoadingMore) return
    if (observer.current) observer.current.disconnect()
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        loadMoreStories()
      }
    })
    
    if (node) observer.current.observe(node)
  }, [isLoadingMore, hasMore])

  useEffect(() => {
    fetchStories(true)
  }, [selectedGenre, sortBy])

  const fetchStories = async (reset: boolean = true) => {
    if (reset) {
      setIsLoading(true)
      setPage(1)
    } else {
      setIsLoadingMore(true)
    }
    
    try {
      const currentPage = reset ? 1 : page + 1
      const response = await storiesApi.getExploreFeed(currentPage, 20, selectedGenre, sortBy)
      
      if (reset) {
        setStories(response.stories)
        setTotal(response.total)
      } else {
        setStories(prev => [...prev, ...response.stories])
      }
      
      setPage(currentPage)
      setHasMore(response.has_next)
    } catch (error) {
      console.error('Failed to fetch stories:', error)
    } finally {
      setIsLoading(false)
      setIsLoadingMore(false)
    }
  }

  const loadMoreStories = () => {
    if (!isLoadingMore && hasMore) {
      fetchStories(false)
    }
  }

  const genres = [
    'all', 'fantasy', 'sci-fi', 'mystery', 'romance', 
    'horror', 'adventure', 'drama', 'comedy', 'thriller'
  ]

  const filteredStories = stories.filter(story => {
    if (searchQuery) {
      return story.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
             story.author?.username.toLowerCase().includes(searchQuery.toLowerCase())
    }
    return true
  })

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
          <h1 className="text-2xl font-bold text-gray-900">Explore Stories</h1>
          <span className="text-sm text-gray-500">{total} stories</span>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-lg transition-colors ${
              viewMode === 'grid' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title="Grid view"
          >
            <Grid className="w-5 h-5" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-lg transition-colors ${
              viewMode === 'list' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title="List view"
          >
            <List className="w-5 h-5" />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            <span>Create Story</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search stories by title or author..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div className="relative">
            <select
              value={selectedGenre}
              onChange={(e) => setSelectedGenre(e.target.value)}
              className="appearance-none px-4 py-2 pr-10 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              {genres.map(genre => (
                <option key={genre} value={genre}>
                  {genre === 'all' ? 'All Genres' : genre.charAt(0).toUpperCase() + genre.slice(1)}
                </option>
              ))}
            </select>
            <Filter className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>

          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="appearance-none px-4 py-2 pr-10 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="latest">Latest</option>
              <option value="popular">Most Popular</option>
              <option value="trending">Trending</option>
            </select>
            <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>

      {filteredStories.length === 0 ? (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No stories found</h3>
          <p className="text-gray-500 mb-6">
            {searchQuery ? 'Try a different search term' : 'Be the first to share a story!'}
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary px-6 py-3"
          >
            Create Your First Story
          </button>
        </div>
      ) : (
        <>
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredStories.map((story, index) => (
                <div
                  key={story.id}
                  ref={index === filteredStories.length - 1 ? lastStoryRef : undefined}
                >
                  <StoryCard story={story} viewMode="grid" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredStories.map((story, index) => (
                <div
                  key={story.id}
                  ref={index === filteredStories.length - 1 ? lastStoryRef : undefined}
                >
                  <StoryCard story={story} viewMode="list" />
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {isLoadingMore && (
        <div className="flex justify-center py-8">
          <Loader className="w-6 h-6 text-primary-600 animate-spin" />
        </div>
      )}

      {showCreateModal && (
        <CreateStoryModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={(storyId) => {
            setShowCreateModal(false)
            navigate(`/story/${storyId}`)
          }}
        />
      )}
    </div>
  )
}

export default Explore