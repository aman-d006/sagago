import { useState, useEffect } from 'react'
import { commentsApi, type Comment } from '../../api/comments'
import { useAuthStore } from '../../stores/authStore'
import { 
  Heart, 
  MessageCircle, 
  Edit2, 
  Trash2, 
  ChevronDown, 
  ChevronUp,
  Send,
  X
} from 'lucide-react'
import { toast } from 'react-toastify'

interface CommentSectionProps {
  storyId: number
  commentCount: number
  onCommentCountChange?: (count: number) => void
}

const CommentSection = ({ storyId, commentCount, onCommentCountChange }: CommentSectionProps) => {
  const { user } = useAuthStore()
  const [comments, setComments] = useState<Comment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [newComment, setNewComment] = useState('')
  const [replyingTo, setReplyingTo] = useState<number | null>(null)
  const [replyText, setReplyText] = useState('')
  const [editingComment, setEditingComment] = useState<number | null>(null)
  const [editText, setEditText] = useState('')
  const [expandedReplies, setExpandedReplies] = useState<Set<number>>(new Set())

  useEffect(() => {
    fetchComments()
  }, [storyId])

  const fetchComments = async () => {
    try {
      const data = await commentsApi.getStoryComments(storyId)
      setComments(data)
    } catch (error) {
      toast.error('Failed to load comments')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddComment = async () => {
    if (!newComment.trim()) return
    
    try {
      const comment = await commentsApi.createComment({
        story_id: storyId,
        content: newComment
      })
      setComments([comment, ...comments])
      setNewComment('')
      onCommentCountChange?.(commentCount + 1)
      toast.success('Comment added!')
    } catch (error) {
      toast.error('Failed to add comment')
    }
  }

  const handleAddReply = async (parentId: number) => {
    if (!replyText.trim()) return
    
    try {
      const reply = await commentsApi.createComment({
        story_id: storyId,
        content: replyText,
        parent_id: parentId
      })
      
      // Add the reply to the comments list
      setComments([reply, ...comments])
      
      // Update parent reply count
      setComments(prev => prev.map(c => 
        c.id === parentId 
          ? { ...c, reply_count: c.reply_count + 1 }
          : c
      ))
      
      setReplyingTo(null)
      setReplyText('')
      onCommentCountChange?.(commentCount + 1)
      toast.success('Reply added!')
    } catch (error) {
      toast.error('Failed to add reply')
    }
  }

  const handleLikeComment = async (commentId: number) => {
    try {
      const response = await commentsApi.likeComment(commentId)
      setComments(comments.map(c => 
        c.id === commentId 
          ? { ...c, like_count: response.like_count, is_liked_by_current_user: response.liked }
          : c
      ))
    } catch (error) {
      toast.error('Failed to like comment')
    }
  }

  const handleEditComment = async (commentId: number) => {
    if (!editText.trim()) return
    
    try {
      await commentsApi.updateComment(commentId, editText)
      setComments(comments.map(c => 
        c.id === commentId 
          ? { ...c, content: editText, is_edited: true }
          : c
      ))
      setEditingComment(null)
      setEditText('')
      toast.success('Comment updated!')
    } catch (error) {
      toast.error('Failed to update comment')
    }
  }

  const handleDeleteComment = async (commentId: number) => {
    if (!window.confirm('Are you sure you want to delete this comment?')) return
    
    try {
      await commentsApi.deleteComment(commentId)
      setComments(comments.filter(c => c.id !== commentId))
      onCommentCountChange?.(commentCount - 1)
      toast.success('Comment deleted')
    } catch (error) {
      toast.error('Failed to delete comment')
    }
  }

  const toggleReplies = (commentId: number) => {
    const newExpanded = new Set(expandedReplies)
    if (newExpanded.has(commentId)) {
      newExpanded.delete(commentId)
    } else {
      newExpanded.add(commentId)
      fetchReplies(commentId)
    }
    setExpandedReplies(newExpanded)
  }

  const fetchReplies = async (commentId: number) => {
    try {
      const replies = await commentsApi.getReplies(commentId)
      // Filter out existing replies and add new ones
      setComments(prev => {
        const existingIds = new Set(prev.map(c => c.id))
        const newReplies = replies.filter(r => !existingIds.has(r.id))
        return [...prev, ...newReplies]
      })
    } catch (error) {
      toast.error('Failed to load replies')
    }
  }

  const CommentItem = ({ comment, isReply = false }: { comment: Comment; isReply?: boolean }) => (
    <div key={`comment-${comment.id}`} className={`${isReply ? 'ml-12 mt-3' : 'mt-4'}`}>
      <div className="flex space-x-3">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
            <span className="text-primary-600 font-semibold text-sm">
              {comment.username.charAt(0).toUpperCase()}
            </span>
          </div>
        </div>

        <div className="flex-1">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center space-x-2">
                <span className="font-medium text-sm">{comment.username}</span>
                <span className="text-xs text-gray-400">
                  {new Date(comment.created_at).toLocaleDateString()}
                </span>
                {comment.is_edited && (
                  <span className="text-xs text-gray-400">(edited)</span>
                )}
              </div>
              
              {user?.username === comment.username && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      setEditingComment(comment.id)
                      setEditText(comment.content)
                    }}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <Edit2 className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleDeleteComment(comment.id)}
                    className="text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>

            {editingComment === comment.id ? (
              <div className="mt-2">
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full p-2 border border-gray-200 rounded-lg text-sm"
                  rows={2}
                />
                <div className="flex justify-end space-x-2 mt-2">
                  <button
                    onClick={() => setEditingComment(null)}
                    className="px-3 py-1 text-xs bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleEditComment(comment.id)}
                    className="px-3 py-1 text-xs bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    Save
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-700">{comment.content}</p>
            )}
          </div>

          <div className="flex items-center space-x-4 mt-2 text-xs">
            <button
              onClick={() => handleLikeComment(comment.id)}
              className={`flex items-center space-x-1 transition-colors ${
                comment.is_liked_by_current_user ? 'text-red-500' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              <Heart className={`w-3 h-3 ${comment.is_liked_by_current_user ? 'fill-red-500' : ''}`} />
              <span>{comment.like_count}</span>
            </button>
            
            {!isReply && (
              <button
                onClick={() => setReplyingTo(comment.id)}
                className="flex items-center space-x-1 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <MessageCircle className="w-3 h-3" />
                <span>Reply</span>
              </button>
            )}

            {comment.reply_count > 0 && (
              <button
                onClick={() => toggleReplies(comment.id)}
                className="flex items-center space-x-1 text-gray-400 hover:text-gray-600 transition-colors"
              >
                {expandedReplies.has(comment.id) ? (
                  <ChevronUp className="w-3 h-3" />
                ) : (
                  <ChevronDown className="w-3 h-3" />
                )}
                <span>{comment.reply_count} {comment.reply_count === 1 ? 'reply' : 'replies'}</span>
              </button>
            )}
          </div>

          {replyingTo === comment.id && (
            <div className="mt-3 ml-8">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={replyText}
                  onChange={(e) => {
                    e.stopPropagation()
                    setReplyText(e.target.value)
                  }}
                  placeholder="Write a reply..."
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddReply(comment.id)
                    }
                  }}
                  autoFocus
                />
                <button
                  onClick={() => handleAddReply(comment.id)}
                  disabled={!replyText.trim()}
                  className="px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    setReplyingTo(null)
                    setReplyText('')
                  }}
                  className="px-3 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {expandedReplies.has(comment.id) && (
            <div className="mt-3 space-y-3">
              {comments
                .filter(c => c.parent_id === comment.id)
                .map(reply => (
                  <CommentItem key={`reply-${reply.id}`} comment={reply} isReply={true} />
                ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-pulse text-gray-400">Loading comments...</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <MessageCircle className="w-5 h-5 mr-2 text-primary-600" />
        Comments ({commentCount})
      </h3>

      <div className="flex space-x-3 mb-6">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
            <span className="text-primary-600 font-semibold text-sm">
              {user?.username.charAt(0).toUpperCase()}
            </span>
          </div>
        </div>
        <div className="flex-1 flex space-x-2">
          <input
            type="text"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment..."
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            onKeyPress={(e) => e.key === 'Enter' && handleAddComment()}
          />
          <button
            onClick={handleAddComment}
            disabled={!newComment.trim()}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Post
          </button>
        </div>
      </div>

      {comments.length === 0 ? (
        <p className="text-center text-gray-400 py-8">
          No comments yet. Be the first to share your thoughts!
        </p>
      ) : (
        <div className="space-y-4">
          {comments
            .filter(c => !c.parent_id)
            .map(comment => (
              <CommentItem key={`top-${comment.id}`} comment={comment} />
            ))}
        </div>
      )}
    </div>
  )
}

export default CommentSection