// src/components/stories/StoryCard.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Heart, MessageCircle, User, Sparkles } from 'lucide-react'
import { getStoryCoverUrl } from '../../utils/imageHelpers'
import type { Story } from '../../types'

interface StoryCardProps {
  story: Story
  viewMode: 'grid' | 'list'
}

const StoryCard = ({ story, viewMode }: StoryCardProps) => {
  const navigate = useNavigate()
  const [imageError, setImageError] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)

  const handleClick = () => {
    navigate(`/story/${story.id}`)
  }

  const formatNumber = (num: number) => {
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  // Get the full image URL using our helper
  const imageUrl = getStoryCoverUrl(story.cover_image)
  
  // Log only in development and only once per story
  if (import.meta.env.DEV) {
    console.log(`🎨 StoryCard ${story.id}:`, {
      title: story.title,
      cover_image: story.cover_image,
      imageUrl,
      hasImage: !!imageUrl,
      storyId: story.id
    })
  }

  // Handle image load success
  const handleImageLoad = () => {
    setImageLoaded(true)
    if (import.meta.env.DEV) {
      console.log(`✅ Image loaded successfully for story ${story.id}:`, imageUrl)
    }
  }

  // Handle image load error
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    setImageError(true)
    if (import.meta.env.DEV) {
      console.error(`❌ Failed to load image for story ${story.id}:`, imageUrl)
    }
    // Hide the broken image
    e.currentTarget.style.display = 'none'
  }

  // Grid view
  if (viewMode === 'grid') {
    return (
      <div
        onClick={handleClick}
        className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all transform hover:-translate-y-1 cursor-pointer overflow-hidden group"
      >
        <div className="relative h-48 bg-gradient-to-br from-primary-500 to-primary-700">
          {imageUrl && !imageError ? (
            <>
              <img
                src={imageUrl}
                alt={story.title}
                className={`w-full h-full object-cover transition-transform duration-300 group-hover:scale-105 ${
                  imageLoaded ? 'opacity-100' : 'opacity-0'
                }`}
                onLoad={handleImageLoad}
                onError={handleImageError}
                loading="lazy"
              />
              {!imageLoaded && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-8 h-8 border-4 border-white/30 border-t-white rounded-full animate-spin" />
                </div>
              )}
            </>
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-4xl text-white opacity-50">📖</span>
            </div>
          )}
          
          {story.story_type === 'interactive' && (
            <span className="absolute top-2 right-2 px-2 py-1 bg-purple-600 text-white text-xs rounded-full flex items-center shadow-lg">
              <Sparkles className="w-3 h-3 mr-1" />
              Interactive
            </span>
          )}
        </div>

        <div className="p-4">
          <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">
            {story.title}
          </h3>
          <p className="text-sm text-gray-500 mb-3 line-clamp-2">
            {story.excerpt || 'No description available'}
          </p>
          
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center">
              <User className="w-3 h-3 mr-1" />
              {story.author?.username || 'Unknown'}
            </span>
            <div className="flex items-center space-x-2">
              <span className="flex items-center">
                <Heart className="w-3 h-3 mr-1" />
                {formatNumber(story.like_count || 0)}
              </span>
              <span className="flex items-center">
                <MessageCircle className="w-3 h-3 mr-1" />
                {formatNumber(story.comment_count || 0)}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // List view
  return (
    <div
      onClick={handleClick}
      className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all cursor-pointer p-4"
    >
      <div className="flex items-start space-x-4">
        <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex-shrink-0 overflow-hidden">
          {imageUrl && !imageError ? (
            <img
              src={imageUrl}
              alt={story.title}
              className="w-full h-full object-cover"
              onLoad={handleImageLoad}
              onError={handleImageError}
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-2xl text-white opacity-50">📖</span>
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">
                {story.title}
              </h3>
              <p className="text-sm text-gray-500 mb-2 line-clamp-2">
                {story.excerpt || 'No description available'}
              </p>
            </div>
            {story.story_type === 'interactive' && (
              <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full flex items-center ml-2">
                <Sparkles className="w-3 h-3 mr-1" />
                Interactive
              </span>
            )}
          </div>

          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center">
              <User className="w-3 h-3 mr-1" />
              {story.author?.username || 'Unknown'}
            </span>
            <div className="flex items-center space-x-3">
              <span className="flex items-center">
                <Heart className="w-3 h-3 mr-1" />
                {formatNumber(story.like_count || 0)}
              </span>
              <span className="flex items-center">
                <MessageCircle className="w-3 h-3 mr-1" />
                {formatNumber(story.comment_count || 0)}
              </span>
              <span className="flex items-center">
                {story.created_at ? new Date(story.created_at).toLocaleDateString() : 'Unknown date'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StoryCard