import apiClient from './client'

export interface Notification {
  id: number
  notification_type: 'like' | 'comment' | 'reply' | 'follow'
  actor_username: string
  actor_avatar?: string
  story_title?: string
  story_id?: number
  comment_preview?: string
  content?: string
  is_read: boolean
  created_at: string
}

export interface NotificationsResponse {
  notifications: Notification[]
  total: number
  unread_count: number
  page: number
  pages: number
}

export const notificationsApi = {
  getNotifications: async (page: number = 1): Promise<NotificationsResponse> => {
    const response = await apiClient.get(`/notifications/?page=${page}`)
    return response.data
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await apiClient.get('/notifications/unread/count')
    return response.data
  },

  markAsRead: async (notificationId: number): Promise<{ message: string }> => {
    const response = await apiClient.post(`/notifications/${notificationId}/read`)
    return response.data
  },

  markAllAsRead: async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/notifications/read-all')
    return response.data
  },

  deleteNotification: async (notificationId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/notifications/${notificationId}`)
    return response.data
  },

  deleteAllNotifications: async (): Promise<{ message: string }> => {
    const response = await apiClient.delete('/notifications/')
    return response.data
  }
}