import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell } from 'lucide-react'
import { useNotificationStore } from '../../stores/notificationStore'

const NotificationBell = () => {
  const { unreadCount, fetchUnreadCount } = useNotificationStore()
  const [isAnimating, setIsAnimating] = useState(false)

  useEffect(() => {
    fetchUnreadCount()
    const interval = setInterval(fetchUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [fetchUnreadCount])

  useEffect(() => {
    if (unreadCount > 0) {
      setIsAnimating(true)
      const timer = setTimeout(() => setIsAnimating(false), 1000)
      return () => clearTimeout(timer)
    }
  }, [unreadCount])

  return (
    <Link
      to="/notifications"
      className="relative p-2 hover:bg-gray-100 rounded-full transition-colors group"
      title="Notifications"
    >
      <Bell className={`w-5 h-5 text-gray-600 group-hover:text-gray-900 transition-colors ${
        isAnimating ? 'animate-bounce' : ''
      }`} />
      {unreadCount > 0 && (
        <>
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-ping" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        </>
      )}
    </Link>
  )
}

export default NotificationBell