import { create } from 'zustand'
import { messagesApi } from '../api/messages'

interface MessageState {
  unreadCount: number
  isLoading: boolean
  fetchUnreadCount: () => Promise<void>
  incrementUnread: () => void
  decrementUnread: (count: number) => void
}

export const useMessageStore = create<MessageState>((set, get) => ({
  unreadCount: 0,
  isLoading: false,

  fetchUnreadCount: async () => {
    set({ isLoading: true })
    try {
      const response = await messagesApi.getUnreadCount()
      set({ unreadCount: response.total_unread })
    } catch (error) {
      console.error('Failed to fetch unread count:', error)
    } finally {
      set({ isLoading: false })
    }
  },

  incrementUnread: () => {
    set({ unreadCount: get().unreadCount + 1 })
  },

  decrementUnread: (count: number) => {
    set({ unreadCount: Math.max(0, get().unreadCount - count) })
  }
}))