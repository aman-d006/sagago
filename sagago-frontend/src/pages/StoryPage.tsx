import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { storiesApi } from '../api/stories'
import { commentsApi } from '../api/comments'
import { 
  Loader, 
  Heart, 
  MessageCircle, 
  Eye, 
  BookOpen, 
  RotateCcw,
  Share2,
  Bookmark,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import type { Story, StoryNode } from '../types'

const StoryPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [story, setStory] = useState<Story | null>(null)
  const [currentNode, setCurrentNode] = useState<StoryNode | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLiked, setIsLiked] = useState(false)
  const [likeCount, setLikeCount] = useState(0)
  const [showComments, setShowComments] = useState(false)
  const [comments, setComments] = useState<any[]>([])
  const [commentText, setCommentText] = useState('')
  const [pathHistory, setPathHistory] = useState<number[]>([])
  const [achievements, setAchievements] = useState<string[]>([])

  useEffect(() => {
    if (id) {
      fetchStory()
      fetchComments()
    }
  }, [id])

  const fetchStory = async () => {
    try {
      const data = await storiesApi.getStory(parseInt(id!))
      setStory(data)
      setCurrentNode(data.root_node || null)
      setIsLiked(data.is_liked_by_current_user || false)
      setLikeCount(data.like_count || 0)
      setPathHistory([data.root_node?.id || 0])
    } catch (error) {
      toast.error('Failed to load story')
      navigate('/')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchComments = async () => {
    try {
      const data = await commentsApi.getStoryComments(parseInt(id!))
      setComments(data)
    } catch (error) {
      console.error('Failed to load comments:', error)
    }
  }

  const handleChoice = (nodeId: number) => {
    if (story?.all_nodes && story.all_nodes[nodeId]) {
      setCurrentNode(story.all_nodes[nodeId])
      setPathHistory([...pathHistory, nodeId])
      
      // Check for achievements
      if (story.all_nodes[nodeId].is_winning_ending) {
        setAchievements([...achievements, '🏆 Victory!'])
        toast.success('🏆 Achievement Unlocked: Victorious Tale!')
      }
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

  const handleRestart = () => {
    if (story?.root_node) {
      setCurrentNode(story.root_node)
      setPathHistory([story.root_node.id])
      toast.info('Starting your journey anew...')
    }
  }

  const handleGoBack = () => {
    if (pathHistory.length > 1) {
      const newHistory = [...pathHistory]
      newHistory.pop()
      const previousNodeId = newHistory[newHistory.length - 1]
      if (story?.all_nodes && story.all_nodes[previousNodeId]) {
        setCurrentNode(story.all_nodes[previousNodeId])
        setPathHistory(newHistory)
      }
    }
  }

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href)
    toast.success('Story link copied to clipboard!')
  }

  const handleComment = async () => {
    if (!commentText.trim()) return
    try {
      await commentsApi.createComment(parseInt(id!), commentText)
      setCommentText('')
      fetchComments()
      toast.success('Comment added!')
    } catch (error) {
      toast.error('Failed to add comment')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  if (!story || !currentNode) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900">Story not found</h2>
        <button onClick={() => navigate('/')} className="btn-primary mt-4">
          Return Home
        </button>
      </div>
    )
  }

  const authorUsername = story.author?.username || 'Unknown Author'
  const viewCount = story.view_count || 0
  const commentCount = story.comment_count || 0
  const progress = Math.round((pathHistory.length / Object.keys(story.all_nodes || {}).length) * 100)

  return (
    <div className="max-w-4xl mx-auto">
      {/* Story Header */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-gray-900">{story.title}</h1>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleShare}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              title="Share story"
            >
              <Share2 className="w-5 h-5 text-gray-600" />
            </button>
            <button
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              title="Save for later"
            >
              <Bookmark className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-primary-600 font-semibold">
                  {authorUsername.charAt(0).toUpperCase()}
                </span>
              </div>
              <span className="text-sm text-gray-600">by {authorUsername}</span>
            </div>
            
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span className="flex items-center">
                <Eye className="w-4 h-4 mr-1" />
                {viewCount}
              </span>
              <button
                onClick={handleLike}
                className="flex items-center hover:text-primary-600 transition-colors"
              >
                <Heart
                  className={`w-4 h-4 mr-1 ${
                    isLiked ? 'fill-red-500 text-red-500' : ''
                  }`}
                />
                {likeCount}
              </button>
              <button
                onClick={() => setShowComments(!showComments)}
                className="flex items-center hover:text-primary-600 transition-colors"
              >
                <MessageCircle className="w-4 h-4 mr-1" />
                {commentCount}
              </button>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {pathHistory.length > 1 && (
              <button
                onClick={handleGoBack}
                className="flex items-center space-x-1 px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
            )}
            <button
              onClick={handleRestart}
              className="flex items-center space-x-1 px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Restart</span>
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        {!currentNode.is_ending && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>Story Progress</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary-600 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Achievements */}
        {achievements.length > 0 && (
          <div className="mt-4 flex items-center space-x-2">
            {achievements.map((achievement, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full"
              >
                {achievement}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Story Content */}
      <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
        <div className="prose prose-lg max-w-none mb-8">
          <p className="text-gray-700 leading-relaxed text-lg">{currentNode.content}</p>
        </div>

        {!currentNode.is_ending ? (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <BookOpen className="w-5 h-5 mr-2 text-primary-600" />
              Where will your journey lead?
            </h3>
            <div className="grid gap-3">
              {currentNode.options?.map((option, index) => (
                <button
                  key={option.node_id}
                  onClick={() => handleChoice(option.node_id)}
                  className="group relative p-5 text-left bg-gradient-to-r from-gray-50 to-white 
                           hover:from-primary-50 hover:to-white rounded-xl transition-all 
                           border-2 border-gray-200 hover:border-primary-300 shadow-sm 
                           hover:shadow-md transform hover:-translate-y-0.5"
                >
                  <div className="flex items-start">
                    <span className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary-700 
                                   rounded-full flex items-center justify-center font-semibold mr-4
                                   group-hover:bg-primary-200 transition-colors">
                      {String.fromCharCode(65 + index)}
                    </span>
                    <span className="text-gray-700 group-hover:text-primary-700 font-medium">
                      {option.text}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="mb-6">
              <span className="text-7xl">
                {currentNode.is_winning_ending ? '🏆' : '📖'}
              </span>
            </div>
            <h2
              className={`text-3xl font-bold mb-4 ${
                currentNode.is_winning_ending
                  ? 'text-green-600'
                  : 'text-orange-600'
              }`}
            >
              {currentNode.is_winning_ending ? 'Victory!' : 'The End'}
            </h2>
            <p className="text-gray-600 text-lg mb-8 max-w-md mx-auto">
              {currentNode.is_winning_ending
                ? 'You have navigated the tale with wisdom and courage, reaching a triumphant conclusion.'
                : 'Your journey has reached its destination. Every end is a new beginning.'}
            </p>
            <div className="flex items-center justify-center space-x-4">
              <button
                onClick={handleRestart}
                className="btn-primary px-8 py-3 text-lg"
              >
                Begin Anew
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
      </div>

      {/* Comments Section */}
      {showComments && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <MessageCircle className="w-5 h-5 mr-2 text-primary-600" />
            Comments ({commentCount})
          </h3>
          
          {/* Add Comment */}
          <div className="flex space-x-3 mb-6">
            <input
              type="text"
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="Share your thoughts..."
              className="input-field flex-1"
              onKeyPress={(e) => e.key === 'Enter' && handleComment()}
            />
            <button
              onClick={handleComment}
              disabled={!commentText.trim()}
              className="btn-primary px-6"
            >
              Post
            </button>
          </div>

          {/* Comments List */}
          <div className="space-y-4">
            {comments.length === 0 ? (
              <p className="text-gray-500 text-center py-4">
                No comments yet. Be the first to share your thoughts!
              </p>
            ) : (
              comments.map((comment) => (
                <div key={comment.id} className="border-b border-gray-100 pb-4 last:border-0">
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-medium text-gray-600">
                        {comment.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-medium text-gray-900">{comment.username}</span>
                        <span className="text-xs text-gray-400">
                          {new Date(comment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-gray-700">{comment.content}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default StoryPage