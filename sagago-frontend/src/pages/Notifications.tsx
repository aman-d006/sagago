import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useNotificationStore } from '../stores/notificationStore'
import { useAuthStore } from '../stores/authStore'
import BackButton from '../components/ui/BackButton'
import { 
  Loader, 
  Heart, 
  MessageCircle, 
  UserPlus,
  Bell,
  CheckCheck,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Clock
} from 'lucide-react'
import { toast } from 'react-toastify'
import type { Notification } from '../api/notifications'

const Notifications = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const {
    notifications,
    unreadCount,
    isLoading,
    total,
    page,
    pages,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    deleteAllNotifications
  } = useNotificationStore()

  const [showConfirm, setShowConfirm] = useState(false)

  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.is_read) {
      await markAsRead(notification.id)
    }

    switch (notification.notification_type) {
      case 'like':
      case 'comment':
        if (notification.story_id) {
          navigate(`/story/${notification.story_id}`)
        }
        break
      case 'follow':
        navigate(`/profile/${notification.actor_username}`)
        break
      default:
        break
    }
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'like':
        return <Heart className="w-5 h-5 text-red-500" />
      case 'comment':
      case 'reply':
        return <MessageCircle className="w-5 h-5 text-blue-500" />
      case 'follow':
        return <UserPlus className="w-5 h-5 text-green-500" />
      default:
        return <Bell className="w-5 h-5 text-gray-500" />
    }
  }

  const getNotificationMessage = (notification: Notification) => {
    switch (notification.notification_type) {
      case 'like':
        return (
          <>
            <span className="font-semibold">{notification.actor_username}</span>
            {' liked your story '}
            <span className="font-medium text-primary-600">"{notification.story_title}"</span>
          </>
        )
      case 'comment':
        return (
          <>
            <span className="font-semibold">{notification.actor_username}</span>
            {' commented on your story '}
            <span className="font-medium text-primary-600">"{notification.story_title}"</span>
            {notification.comment_preview && (
              <span className="block text-sm text-gray-500 mt-1 italic">
                "{notification.comment_preview}"
              </span>
            )}
          </>
        )
      case 'reply':
        return (
          <>
            <span className="font-semibold">{notification.actor_username}</span>
            {' replied to your comment'}
            {notification.comment_preview && (
              <span className="block text-sm text-gray-500 mt-1 italic">
                "{notification.comment_preview}"
              </span>
            )}
          </>
        )
      case 'follow':
        return (
          <>
            <span className="font-semibold">{notification.actor_username}</span>
            {' started following you'}
          </>
        )
      default:
        return notification.content
    }
  }

  const handleMarkAllAsRead = async () => {
    await markAllAsRead()
    toast.success('All notifications marked as read')
  }

  const handleDeleteAll = async () => {
    await deleteAllNotifications()
    setShowConfirm(false)
    toast.success('All notifications deleted')
  }

  const loadMore = () => {
    if (page < pages) {
      fetchNotifications(page + 1)
    }
  }

  if (isLoading && notifications.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <BackButton />
          <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
          {unreadCount > 0 && (
            <span className="px-2 py-1 bg-red-100 text-red-600 text-xs font-medium rounded-full">
              {unreadCount} new
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllAsRead}
              className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="Mark all as read"
            >
              <CheckCheck className="w-4 h-4" />
              <span className="hidden sm:inline">Mark all read</span>
            </button>
          )}
          {notifications.length > 0 && (
            <button
              onClick={() => setShowConfirm(true)}
              className="flex items-center space-x-1 px-3 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete all"
            >
              <Trash2 className="w-4 h-4" />
              <span className="hidden sm:inline">Delete all</span>
            </button>
          )}
        </div>
      </div>

      {notifications.length === 0 ? (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <Bell className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No notifications yet</h3>
          <p className="text-gray-500">
            When someone interacts with your content, you'll see it here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              onClick={() => handleNotificationClick(notification)}
              className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-all cursor-pointer ${
                !notification.is_read ? 'border-l-4 border-primary-500' : ''
              }`}
            >
              <div className="p-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    {getNotificationIcon(notification.notification_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${
                      notification.is_read ? 'text-gray-600' : 'text-gray-900 font-medium'
                    }`}>
                      {getNotificationMessage(notification)}
                    </p>
                    <div className="flex items-center space-x-2 mt-2 text-xs text-gray-400">
                      <Clock className="w-3 h-3" />
                      <span>
                        {new Date(notification.created_at).toLocaleDateString()} at{' '}
                        {new Date(notification.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    {!notification.is_read && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          markAsRead(notification.id)
                        }}
                        className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                        title="Mark as read"
                      >
                        <CheckCheck className="w-4 h-4 text-gray-400" />
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteNotification(notification.id)
                      }}
                      className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-500" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {page < pages && (
            <div className="flex justify-center mt-6">
              <button
                onClick={loadMore}
                disabled={isLoading}
                className="flex items-center space-x-2 px-6 py-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                {isLoading ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <span>Load More</span>
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowConfirm(false)} />
          <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Delete All Notifications?</h3>
            <p className="text-gray-600 mb-6">
              This action cannot be undone. All your notifications will be permanently deleted.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAll}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Notifications