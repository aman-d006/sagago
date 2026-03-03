import { useState, useEffect } from 'react'
import { Bookmark, BookmarkCheck } from 'lucide-react'
import { bookmarksApi } from '../../api/bookmarks'
import { toast } from 'react-toastify'

interface BookmarkButtonProps {
  storyId: number
  className?: string
}

const BookmarkButton = ({ storyId, className = '' }: BookmarkButtonProps) => {
  const [isBookmarked, setIsBookmarked] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    checkBookmarkStatus()
  }, [storyId])

  const checkBookmarkStatus = async () => {
    try {
      const response = await bookmarksApi.checkBookmark(storyId)
      setIsBookmarked(response.is_bookmarked)
    } catch (error) {
      console.error('Failed to check bookmark status:', error)
    }
  }

  const handleToggleBookmark = async () => {
    setIsLoading(true)
    try {
      if (isBookmarked) {
        await bookmarksApi.removeBookmark(storyId)
        setIsBookmarked(false)
        toast.success('Removed from reading list')
      } else {
        await bookmarksApi.addBookmark(storyId)
        setIsBookmarked(true)
        toast.success('Added to reading list')
      }
    } catch (error) {
      toast.error('Failed to update bookmark')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <button
      onClick={handleToggleBookmark}
      disabled={isLoading}
      className={`p-2 rounded-full transition-colors ${
        isBookmarked 
          ? 'text-primary-600 bg-primary-50 hover:bg-primary-100' 
          : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
      } ${className}`}
      title={isBookmarked ? 'Remove from reading list' : 'Add to reading list'}
    >
      {isBookmarked ? (
        <BookmarkCheck className="w-5 h-5 fill-primary-600" />
      ) : (
        <Bookmark className="w-5 h-5" />
      )}
    </button>
  )
}

export default BookmarkButton