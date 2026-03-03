import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usersApi } from '../api/users'
import BackButton from '../components/ui/BackButton'
import FollowSuggestions from '../components/users/FollowSuggestions'
import { 
  Search, 
  UserPlus, 
  UserCheck, 
  Loader,
  Users,
  X
} from 'lucide-react'
import { toast } from 'react-toastify'

interface SearchUser {
  id: number
  username: string
  full_name?: string
  avatar_url?: string
  bio?: string
  followers_count: number
  stories_count: number
  is_following?: boolean
}

const UserSearch = () => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [users, setUsers] = useState<SearchUser[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [followingStates, setFollowingStates] = useState<Record<number, boolean>>({})

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      if (query.trim()) {
        performSearch()
      } else {
        setUsers([])
        setHasSearched(false)
      }
    }, 500)

    return () => clearTimeout(delayDebounce)
  }, [query])

  const performSearch = async () => {
    if (!query.trim()) return
    
    setIsLoading(true)
    setHasSearched(true)
    
    try {
      const results = await usersApi.searchUsers(query)
      setUsers(results)
      
      const initialFollowStates: Record<number, boolean> = {}
      results.forEach((user: SearchUser) => {
        if (user.is_following !== undefined) {
          initialFollowStates[user.id] = user.is_following
        }
      })
      setFollowingStates(initialFollowStates)
    } catch (error) {
      toast.error('Failed to search users')
      setUsers([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFollowToggle = async (targetUser: SearchUser, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      const response = await usersApi.followUser(targetUser.username)
      setFollowingStates(prev => ({
        ...prev,
        [targetUser.id]: response.is_following
      }))
      toast.success(response.message)
    } catch (error) {
      toast.error('Failed to update follow status')
    }
  }

  const handleUserClick = (username: string) => {
    navigate(`/profile/${username}`)
  }

  const clearSearch = () => {
    setQuery('')
    setUsers([])
    setHasSearched(false)
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <BackButton />
          <h1 className="text-2xl font-bold text-gray-900">Discover Users</h1>
        </div>
        <div className="w-20"></div>
      </div>

      <div className="flex gap-6">
        <div className="flex-1">
          <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by username or full name..."
                className="w-full pl-10 pr-10 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              {query && (
                <button
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              )}
            </div>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader className="w-8 h-8 text-primary-600 animate-spin" />
            </div>
          ) : hasSearched && users.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No users found</h3>
              <p className="text-gray-500">
                Try searching with a different term
              </p>
            </div>
          ) : users.length > 0 ? (
            <div className="space-y-3">
              {users.map((user) => (
                <div
                  key={user.id}
                  onClick={() => handleUserClick(user.username)}
                  className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all p-4 cursor-pointer border border-gray-100"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                        {user.avatar_url ? (
                          <img
                            src={user.avatar_url}
                            alt={user.username}
                            className="w-12 h-12 rounded-full object-cover"
                          />
                        ) : (
                          <span className="text-xl font-bold text-primary-600">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {user.full_name || user.username}
                        </h3>
                        <p className="text-sm text-gray-500">@{user.username}</p>
                        {user.bio && (
                          <p className="text-sm text-gray-600 line-clamp-1 mt-1">{user.bio}</p>
                        )}
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-400">
                          <span>{user.followers_count} followers</span>
                          <span>{user.stories_count} stories</span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={(e) => handleFollowToggle(user, e)}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                        followingStates[user.id]
                          ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          : 'bg-primary-600 text-white hover:bg-primary-700'
                      }`}
                    >
                      {followingStates[user.id] ? (
                        <>
                          <UserCheck className="w-4 h-4" />
                          <span>Following</span>
                        </>
                      ) : (
                        <>
                          <UserPlus className="w-4 h-4" />
                          <span>Follow</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div className="hidden lg:block w-80 flex-shrink-0">
          <div className="sticky top-24">
            <FollowSuggestions />
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserSearch