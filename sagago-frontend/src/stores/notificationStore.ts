import { create } from 'zustand'
import { notificationsApi, type Notification } from '../api/notifications'

interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  isLoading: boolean
  total: number
  page: number
  pages: number
  fetchNotifications: (page?: number) => Promise<void>
  fetchUnreadCount: () => Promise<void>
  markAsRead: (id: number) => Promise<void>
  markAllAsRead: () => Promise<void>
  deleteNotification: (id: number) => Promise<void>
  deleteAllNotifications: () => Promise<void>
  addNotification: (notification: Notification) => void
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  total: 0,
  page: 1,
  pages: 1,

  fetchNotifications: async (page = 1) => {
    set({ isLoading: true })
    try {
      const response = await notificationsApi.getNotifications(page)
      set({
        notifications: response.notifications,
        total: response.total,
        page: response.page,
        pages: response.pages,
        unreadCount: response.unread_count
      })
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      set({ isLoading: false })
    }
  },

  fetchUnreadCount: async () => {
    try {
      const response = await notificationsApi.getUnreadCount()
      set({ unreadCount: response.unread_count })
    } catch (error) {
      console.error('Failed to fetch unread count:', error)
    }
  },

  markAsRead: async (id) => {
    try {
      await notificationsApi.markAsRead(id)
      const { notifications, unreadCount } = get()
      const updated = notifications.map(n => 
        n.id === id ? { ...n, is_read: true } : n
      )
      set({
        notifications: updated,
        unreadCount: Math.max(0, unreadCount - 1)
      })
    } catch (error) {
      console.error('Failed to mark as read:', error)
    }
  },

  markAllAsRead: async () => {
    try {
      await notificationsApi.markAllAsRead()
      const { notifications } = get()
      const updated = notifications.map(n => ({ ...n, is_read: true }))
      set({ notifications: updated, unreadCount: 0 })
    } catch (error) {
      console.error('Failed to mark all as read:', error)
    }
  },

  deleteNotification: async (id) => {
    try {
      await notificationsApi.deleteNotification(id)
      const { notifications, unreadCount } = get()
      const deleted = notifications.find(n => n.id === id)
      set({
        notifications: notifications.filter(n => n.id !== id),
        unreadCount: deleted && !deleted.is_read ? unreadCount - 1 : unreadCount
      })
    } catch (error) {
      console.error('Failed to delete notification:', error)
    }
  },

  deleteAllNotifications: async () => {
    try {
      await notificationsApi.deleteAllNotifications()
      set({ notifications: [], unreadCount: 0 })
    } catch (error) {
      console.error('Failed to delete all notifications:', error)
    }
  },

  addNotification: (notification) => {
    const { notifications } = get()
    set({
      notifications: [notification, ...notifications],
      unreadCount: get().unreadCount + 1
    })
  }
}))