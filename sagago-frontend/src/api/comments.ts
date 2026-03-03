import apiClient from './client'

export interface Comment {
  id: number
  content: string
  user_id: number
  username: string
  user_avatar?: string
  story_id: number
  parent_id?: number
  like_count: number
  reply_count: number
  is_edited: boolean
  created_at: string
  is_liked_by_current_user: boolean
}

export interface CommentCreate {
  content: string
  story_id: number
  parent_id?: number
}

export const commentsApi = {
  // Get comments for a story
  getStoryComments: async (storyId: number): Promise<Comment[]> => {
    const response = await apiClient.get(`/comments/story/${storyId}`)
    return response.data
  },

  // Get replies for a comment
  getReplies: async (commentId: number): Promise<Comment[]> => {
    const response = await apiClient.get(`/comments/${commentId}/replies`)
    return response.data
  },

  // Create a new comment
  createComment: async (data: CommentCreate): Promise<Comment> => {
    const response = await apiClient.post('/comments/', data)
    return response.data
  },

  // Update a comment
  updateComment: async (commentId: number, content: string): Promise<{ message: string }> => {
    const response = await apiClient.put(`/comments/${commentId}`, { content })
    return response.data
  },

  // Delete a comment
  deleteComment: async (commentId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/comments/${commentId}`)
    return response.data
  },

  // Like/unlike a comment
  likeComment: async (commentId: number): Promise<{ message: string; liked: boolean; like_count: number }> => {
    const response = await apiClient.post(`/comments/${commentId}/like`)
    return response.data
  }
}