import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usersApi } from '../../api/users'
import { UserPlus, UserCheck, Loader, Users } from 'lucide-react'
import { toast } from 'react-toastify'

interface SuggestionUser {
  id: number
  username: string
  full_name?: string
  avatar_url?: string
  bio?: string
  followers_count: number
  stories_count: number
}

const FollowSuggestions = () => {
  const navigate = useNavigate()
  const [suggestions, setSuggestions] = useState<SuggestionUser[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [followingStates, setFollowingStates] = useState<Record<number, boolean>>({})

  useEffect(() => {
    fetchSuggestions()
  }, [])

  const fetchSuggestions = async () => {
    try {
      const data = await usersApi.getFollowSuggestions(5)
      setSuggestions(data)
    } catch (error) {
      console.error('Failed to fetch suggestions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFollow = async (user: SuggestionUser, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      const response = await usersApi.followUser(user.username)
      setFollowingStates(prev => ({
        ...prev,
        [user.id]: response.is_following
      }))
      toast.success(response.message)
    } catch (error) {
      toast.error('Failed to follow user')
    }
  }

  const handleUserClick = (username: string) => {
    navigate(`/profile/${username}`)
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="flex items-center justify-center py-4">
          <Loader className="w-5 h-5 text-primary-600 animate-spin" />
        </div>
      </div>
    )
  }

  if (suggestions.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-4">
      <div className="flex items-center space-x-2 mb-4">
        <Users className="w-5 h-5 text-primary-600" />
        <h3 className="font-semibold text-gray-900">Who to follow</h3>
      </div>

      <div className="space-y-3">
        {suggestions.map((user) => (
          <div
            key={user.id}
            onClick={() => handleUserClick(user.username)}
            className="flex items-center justify-between group cursor-pointer"
          >
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={user.username}
                    className="w-8 h-8 rounded-full object-cover"
                  />
                ) : (
                  <span className="text-sm font-bold text-primary-600">
                    {user.username.charAt(0).toUpperCase()}
                  </span>
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 group-hover:text-primary-600 transition-colors">
                  {user.full_name || user.username}
                </p>
                <p className="text-xs text-gray-500">@{user.username}</p>
              </div>
            </div>

            <button
              onClick={(e) => handleFollow(user, e)}
              className={`p-1.5 rounded-full transition-colors ${
                followingStates[user.id]
                  ? 'text-green-600 hover:bg-green-50'
                  : 'text-primary-600 hover:bg-primary-50'
              }`}
              title={followingStates[user.id] ? 'Following' : 'Follow'}
            >
              {followingStates[user.id] ? (
                <UserCheck className="w-4 h-4" />
              ) : (
                <UserPlus className="w-4 h-4" />
              )}
            </button>
          </div>
        ))}
      </div>

      <button
        onClick={() => navigate('/search/users')}
        className="w-full mt-3 text-sm text-primary-600 hover:text-primary-700 font-medium text-center"
      >
        View more suggestions
      </button>
    </div>
  )
}

export default FollowSuggestions