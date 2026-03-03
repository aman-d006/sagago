import apiClient from './client'

export interface Message {
  id: number
  sender_id: number
  receiver_id: number
  content: string
  is_read: boolean
  created_at: string
  sender_username: string
  sender_avatar?: string
  receiver_username: string
  receiver_avatar?: string
}

export interface Conversation {
  id: number
  user_id: number
  username: string
  avatar_url?: string
  last_message: string
  last_message_at: string
  unread_count: number
  is_online: boolean
}

export interface ConversationDetail {
  id: number
  user: {
    id: number
    username: string
    full_name?: string
    avatar_url?: string
    is_online: boolean
  }
  messages: Message[]
  total: number
  page: number
  pages: number
}

export interface UnreadCount {
  total_unread: number
  conversations: Array<{
    user_id: number
    username: string
    unread_count: number
  }>
}

export const messagesApi = {
  sendMessage: async (receiverId: number, content: string) => {
    const response = await apiClient.post('/messages/send', {
      receiver_id: receiverId,
      content
    })
    return response.data
  },

  getConversations: async () => {
    const response = await apiClient.get('/messages/conversations')
    return response.data
  },

  getConversation: async (userId: number, page: number = 1) => {
    const response = await apiClient.get(`/messages/conversation/${userId}?page=${page}`)
    return response.data
  },

  getUnreadCount: async () => {
    const response = await apiClient.get('/messages/unread/count')
    return response.data
  },

  markAllRead: async () => {
    const response = await apiClient.post('/messages/read/all')
    return response.data
  },

  markConversationRead: async (userId: number) => {
    const response = await apiClient.post(`/messages/read/${userId}`)
    return response.data
  }
}