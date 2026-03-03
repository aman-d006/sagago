import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usersApi } from '../../api/users'
import { X, UserPlus, UserCheck, Loader } from 'lucide-react'
import { toast } from 'react-toastify'

interface UserListModalProps {
  isOpen: boolean
  onClose: () => void
  username: string
  type: 'followers' | 'following'
  initialCount: number
}

interface UserListItem {
  id: number
  username: string
  full_name?: string
  avatar_url?: string
  bio?: string
  followed_at?: string
  is_following?: boolean
}

const UserListModal = ({ isOpen, onClose, username, type, initialCount }: UserListModalProps) => {
  const navigate = useNavigate()
  const [users, setUsers] = useState<UserListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [followingStates, setFollowingStates] = useState<Record<number, boolean>>({})

  useEffect(() => {
    if (isOpen) {
      fetchUsers(1, true)
    }
  }, [isOpen, username, type])

  const fetchUsers = async (pageNum: number, reset: boolean = false) => {
    if (pageNum === 1) setIsLoading(true)
    else setLoadingMore(true)

    try {
      const response = await (type === 'followers' 
        ? usersApi.getFollowers(username, pageNum, 20)
        : usersApi.getFollowing(username, pageNum, 20))

      const newUsers = response
      
      if (reset) {
        setUsers(newUsers)
      } else {
        setUsers(prev => [...prev, ...newUsers])
      }

      setHasMore(newUsers.length === 20)
      setPage(pageNum)
    } catch (error) {
      toast.error(`Failed to load ${type}`)
    } finally {
      setIsLoading(false)
      setLoadingMore(false)
    }
  }

  const loadMore = () => {
    if (hasMore && !loadingMore) {
      fetchUsers(page + 1)
    }
  }

  const handleFollowToggle = async (targetUsername: string, userId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      const response = await usersApi.followUser(targetUsername)
      setFollowingStates(prev => ({
        ...prev,
        [userId]: response.is_following
      }))
      toast.success(response.message)
    } catch (error) {
      toast.error('Failed to update follow status')
    }
  }

  const handleUserClick = (user: UserListItem) => {
    onClose()
    navigate(`/profile/${user.username}`)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">
            {type === 'followers' ? 'Followers' : 'Following'} • {initialCount}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader className="w-6 h-6 text-primary-600 animate-spin" />
            </div>
          ) : users.length === 0 ? (
            <p className="text-center text-gray-500 py-8">
              {type === 'followers' 
                ? 'No followers yet' 
                : 'Not following anyone yet'}
            </p>
          ) : (
            <div className="space-y-4">
              {users.map((user) => (
                <div
                  key={user.id}
                  onClick={() => handleUserClick(user)}
                  className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                      {user.avatar_url ? (
                        <img
                          src={user.avatar_url}
                          alt={user.username}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <span className="text-lg font-bold text-primary-600">
                          {user.username.charAt(0).toUpperCase()}
                        </span>
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {user.full_name || user.username}
                      </p>
                      <p className="text-sm text-gray-500">@{user.username}</p>
                      {user.bio && (
                        <p className="text-xs text-gray-400 line-clamp-1 mt-1">{user.bio}</p>
                      )}
                      {user.followed_at && (
                        <p className="text-xs text-gray-400 mt-1">
                          Followed {new Date(user.followed_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={(e) => handleFollowToggle(user.username, user.id, e)}
                    className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                      followingStates[user.id] !== undefined
                        ? followingStates[user.id]
                          ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          : 'bg-primary-600 text-white hover:bg-primary-700'
                        : 'bg-primary-600 text-white hover:bg-primary-700'
                    }`}
                  >
                    {followingStates[user.id] !== undefined
                      ? followingStates[user.id]
                        ? <UserCheck className="w-4 h-4" />
                        : <UserPlus className="w-4 h-4" />
                      : <UserPlus className="w-4 h-4" />}
                    <span>
                      {followingStates[user.id] !== undefined
                        ? followingStates[user.id]
                          ? 'Following'
                          : 'Follow'
                        : 'Follow'}
                    </span>
                  </button>
                </div>
              ))}

              {hasMore && (
                <div className="flex justify-center pt-4">
                  <button
                    onClick={loadMore}
                    disabled={loadingMore}
                    className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
                  >
                    {loadingMore ? (
                      <Loader className="w-4 h-4 animate-spin" />
                    ) : (
                      'Load More'
                    )}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default UserListModal