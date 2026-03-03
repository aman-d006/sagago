import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { bookmarksApi, type Bookmark } from '../api/bookmarks'
import BackButton from '../components/ui/BackButton'
import { getImageUrl } from '../utils/imageHelpers'
import { 
  Loader, 
  BookOpen, 
  CheckCircle, 
  Circle,
  Eye,
  Heart,
  MessageCircle,
  Filter,
  ChevronRight
} from 'lucide-react'
import { toast } from 'react-toastify'

const ReadingList = () => {
  const navigate = useNavigate()
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    fetchBookmarks(1, true)
  }, [filter])

  const fetchBookmarks = async (pageNum: number, reset: boolean = false) => {
    if (reset) setIsLoading(true)
    
    try {
      const readStatus = filter === 'all' ? undefined : filter === 'read'
      const response = await bookmarksApi.getBookmarks(pageNum, readStatus)
      
      if (reset) {
        setBookmarks(response.bookmarks)
      } else {
        setBookmarks(prev => [...prev, ...response.bookmarks])
      }
      
      setTotal(response.total)
      setPage(response.page)
      setHasMore(response.has_next)
    } catch (error) {
      toast.error('Failed to load reading list')
    } finally {
      setIsLoading(false)
    }
  }

  const loadMore = () => {
    if (hasMore && !isLoading) {
      fetchBookmarks(page + 1)
    }
  }

  const handleMarkAsRead = async (storyId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await bookmarksApi.markAsRead(storyId)
      setBookmarks(prev => 
        prev.map(b => 
          b.story_id === storyId ? { ...b, is_read: true } : b
        )
      )
      toast.success('Marked as read')
    } catch (error) {
      toast.error('Failed to mark as read')
    }
  }

  const handleRemove = async (storyId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await bookmarksApi.removeBookmark(storyId)
      setBookmarks(prev => prev.filter(b => b.story_id !== storyId))
      setTotal(prev => prev - 1)
      toast.success('Removed from reading list')
    } catch (error) {
      toast.error('Failed to remove')
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    return date.toLocaleDateString()
  }

  if (isLoading && bookmarks.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <BackButton />
          <h1 className="text-2xl font-bold text-gray-900">Reading List</h1>
          <span className="text-sm text-gray-500">{total} stories</span>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex items-center space-x-4">
          <Filter className="w-5 h-5 text-gray-400" />
          <div className="flex space-x-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'all' 
                  ? 'bg-primary-600 text-white' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'unread' 
                  ? 'bg-primary-600 text-white' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Unread
            </button>
            <button
              onClick={() => setFilter('read')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'read' 
                  ? 'bg-primary-600 text-white' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Read
            </button>
          </div>
        </div>
      </div>

      {bookmarks.length === 0 ? (
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Your reading list is empty</h3>
          <p className="text-gray-500 mb-6">
            {filter === 'all' 
              ? 'Save stories to read them later'
              : filter === 'unread'
              ? 'No unread stories in your list'
              : 'No read stories in your list'}
          </p>
          <button
            onClick={() => navigate('/explore')}
            className="btn-primary px-6 py-3"
          >
            Explore Stories
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {bookmarks.map((bookmark) => {
            const imageUrl = getImageUrl(bookmark.story_cover)
            
            return (
              <div
                key={bookmark.id}
                onClick={() => navigate(`/story/${bookmark.story_id}`)}
                className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all cursor-pointer border border-gray-100 overflow-hidden"
              >
                <div className="flex">
                  {imageUrl ? (
                    <div className="w-24 h-24 bg-gray-100 flex-shrink-0">
                      <img 
                        src={imageUrl} 
                        alt={bookmark.story_title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                          e.currentTarget.parentElement!.innerHTML = '<div class="w-24 h-24 bg-gradient-to-br from-primary-100 to-purple-100 flex items-center justify-center"><svg class="w-8 h-8 text-primary-400" ... /></div>'
                        }}
                      />
                    </div>
                  ) : (
                    <div className="w-24 h-24 bg-gradient-to-br from-primary-100 to-purple-100 flex items-center justify-center flex-shrink-0">
                      <BookOpen className="w-8 h-8 text-primary-400" />
                    </div>
                  )}
                  
                  <div className="flex-1 p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-1">
                          {bookmark.story_title}
                        </h3>
                        <p className="text-sm text-gray-500 mb-2 line-clamp-1">
                          by {bookmark.story_author}
                        </p>
                        {bookmark.story_excerpt && (
                          <p className="text-xs text-gray-400 line-clamp-1 mb-2">
                            {bookmark.story_excerpt}
                          </p>
                        )}
                        <div className="flex items-center space-x-3 text-xs text-gray-400">
                          <span>Saved {formatDate(bookmark.created_at)}</span>
                          {bookmark.is_read ? (
                            <span className="flex items-center text-green-600">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Read
                            </span>
                          ) : (
                            <span className="flex items-center text-amber-600">
                              <Circle className="w-3 h-3 mr-1" />
                              Unread
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        {!bookmark.is_read && (
                          <button
                            onClick={(e) => handleMarkAsRead(bookmark.story_id, e)}
                            className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-full transition-colors"
                            title="Mark as read"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={(e) => handleRemove(bookmark.story_id, e)}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
                          title="Remove"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}

          {hasMore && (
            <div className="flex justify-center pt-4">
              <button
                onClick={loadMore}
                disabled={isLoading}
                className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ReadingList