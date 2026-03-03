import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { storiesApi } from '../api/stories'
import { usersApi } from '../api/users'
import { getImageUrl } from '../utils/imageHelpers'
import { toast } from 'react-toastify'
import BackButton from '../components/ui/BackButton'
import UserListModal from '../components/users/UserListModal'
import { 
  Loader, 
  User as UserIcon, 
  Mail, 
  Calendar, 
  BookOpen, 
  Heart, 
  MessageCircle, 
  Eye,
  Edit2,
  LogOut,
  Sparkles,
  PenTool,
  Filter,
  Users,
  Send
} from 'lucide-react'

interface ProfileUser {
  id: number
  username: string
  email: string
  full_name?: string
  avatar_url?: string
  bio?: string
  followers_count: number
  following_count: number
  stories_count: number
  created_at: string
}

interface Story {
  id: number
  title: string
  excerpt: string
  cover_image?: string
  created_at: string
  like_count: number
  comment_count: number
  view_count: number
  story_type?: 'interactive' | 'written'
}

const Profile = () => {
  const { username } = useParams<{ username: string }>()
  const navigate = useNavigate()
  const { user: currentUser, logout } = useAuthStore()
  
  const [profileUser, setProfileUser] = useState<ProfileUser | null>(null)
  const [userStories, setUserStories] = useState<Story[]>([])
  const [filteredStories, setFilteredStories] = useState<Story[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isFollowing, setIsFollowing] = useState(false)
  const [followerCount, setFollowerCount] = useState(0)
  const [followingCount, setFollowingCount] = useState(0)
  const [activeTab, setActiveTab] = useState<'stories' | 'about' | 'settings'>('stories')
  const [storyFilter, setStoryFilter] = useState<'all' | 'interactive' | 'written'>('all')
  const [showFollowersModal, setShowFollowersModal] = useState(false)
  const [showFollowingModal, setShowFollowingModal] = useState(false)
  
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    full_name: '',
    bio: '',
    email: ''
  })

  useEffect(() => {
    if (username) {
      fetchProfileData()
    }
  }, [username])

  useEffect(() => {
    if (userStories.length > 0) {
      filterStories()
    }
  }, [storyFilter, userStories])

  const fetchProfileData = async () => {
    setIsLoading(true)
    try {
      const userData = await usersApi.getUserByUsername(username!)
      setProfileUser(userData)
      setFollowerCount(userData.followers_count)
      setFollowingCount(userData.following_count)
      setEditForm({
        full_name: userData.full_name || '',
        bio: userData.bio || '',
        email: userData.email
      })

      await fetchUserStories()

      if (currentUser && currentUser.username !== username) {
        const followStatus = await usersApi.checkFollowStatus(username!)
        setIsFollowing(followStatus.is_following)
      }
    } catch (error) {
      console.error('Failed to load profile:', error)
      toast.error('Failed to load profile')
      navigate('/')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchUserStories = async () => {
    try {
      const stories = await usersApi.getUserStories(username!)
      setUserStories(stories)
    } catch (error) {
      console.error('Failed to fetch user stories:', error)
    }
  }

  const filterStories = () => {
    if (storyFilter === 'all') {
      setFilteredStories(userStories)
    } else {
      const filtered = userStories.filter(story => {
        let effectiveType = story.story_type
        if (!effectiveType) {
          effectiveType = 'written'
        }
        return effectiveType === storyFilter
      })
      setFilteredStories(filtered)
    }
  }

  const handleFollow = async () => {
    if (!currentUser) {
      toast.error('Please login to follow users')
      return
    }
    
    try {
      const response = await usersApi.followUser(username!)
      setIsFollowing(response.is_following)
      setFollowerCount(prev => response.is_following ? prev + 1 : prev - 1)
      toast.success(response.message)
    } catch (error) {
      toast.error('Failed to follow user')
    }
  }

  const handleMessage = () => {
    if (!currentUser) {
      toast.error('Please login to send messages')
      return
    }
    navigate(`/messages?start=${profileUser?.id}`)
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const updatedUser = await usersApi.updateProfile(editForm)
      setProfileUser(updatedUser)
      setIsEditing(false)
      toast.success('Profile updated successfully')
    } catch (error) {
      toast.error('Failed to update profile')
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const formatNumber = (num: number) => {
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  if (!profileUser) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900">User not found</h2>
        <button onClick={() => navigate('/')} className="btn-primary mt-4">
          Return Home
        </button>
      </div>
    )
  }

  const isOwnProfile = currentUser?.username === profileUser.username

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-4">
        <BackButton />
      </div>

      <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-6">
            <div className="w-24 h-24 bg-primary-100 rounded-full flex items-center justify-center">
              {profileUser.avatar_url ? (
                <img 
                  src={profileUser.avatar_url} 
                  alt={profileUser.username}
                  className="w-24 h-24 rounded-full object-cover"
                />
              ) : (
                <span className="text-4xl font-bold text-primary-600">
                  {profileUser.username.charAt(0).toUpperCase()}
                </span>
              )}
            </div>
            
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {profileUser.full_name || profileUser.username}
              </h1>
              <p className="text-gray-500">@{profileUser.username}</p>
              {profileUser.bio && (
                <p className="mt-2 text-gray-700 max-w-md">{profileUser.bio}</p>
              )}
            </div>
          </div>

          <div className="flex space-x-3">
            {isOwnProfile ? (
              <>
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                  <span>{isEditing ? 'Cancel' : 'Edit Profile'}</span>
                </button>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </>
            ) : (
              <div className="flex space-x-2">
                <button
                  onClick={handleMessage}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Send className="w-4 h-4" />
                  <span>Message</span>
                </button>
                <button
                  onClick={handleFollow}
                  className={`px-6 py-2 rounded-lg transition-colors ${
                    isFollowing
                      ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      : 'bg-primary-600 text-white hover:bg-primary-700'
                  }`}
                >
                  {isFollowing ? 'Following' : 'Follow'}
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="flex space-x-8 mt-6 pt-6 border-t border-gray-200">
          <button
            onClick={() => setShowFollowersModal(true)}
            className="text-center hover:opacity-80 transition-opacity"
          >
            <div className="text-2xl font-bold text-gray-900">{followerCount}</div>
            <div className="text-sm text-gray-500">Followers</div>
          </button>
          <button
            onClick={() => setShowFollowingModal(true)}
            className="text-center hover:opacity-80 transition-opacity"
          >
            <div className="text-2xl font-bold text-gray-900">{followingCount}</div>
            <div className="text-sm text-gray-500">Following</div>
          </button>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{profileUser.stories_count}</div>
            <div className="text-sm text-gray-500">Stories</div>
          </div>
        </div>
      </div>

      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setActiveTab('stories')}
          className={`px-4 py-2 font-medium rounded-lg transition-colors ${
            activeTab === 'stories'
              ? 'bg-primary-600 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          Stories
        </button>
        <button
          onClick={() => setActiveTab('about')}
          className={`px-4 py-2 font-medium rounded-lg transition-colors ${
            activeTab === 'about'
              ? 'bg-primary-600 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          About
        </button>
        {isOwnProfile && (
          <button
            onClick={() => setActiveTab('settings')}
            className={`px-4 py-2 font-medium rounded-lg transition-colors ${
              activeTab === 'settings'
                ? 'bg-primary-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Settings
          </button>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        {activeTab === 'stories' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-900">Stories</h2>
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setStoryFilter('all')}
                    className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                      storyFilter === 'all' ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-600'
                    }`}
                  >
                    All
                  </button>
                  <button
                    onClick={() => setStoryFilter('written')}
                    className={`px-3 py-1 rounded-lg text-sm transition-colors flex items-center space-x-1 ${
                      storyFilter === 'written' ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-600'
                    }`}
                  >
                    <PenTool className="w-3 h-3" />
                    <span>Written</span>
                  </button>
                  <button
                    onClick={() => setStoryFilter('interactive')}
                    className={`px-3 py-1 rounded-lg text-sm transition-colors flex items-center space-x-1 ${
                      storyFilter === 'interactive' ? 'bg-white text-primary-600 shadow-sm' : 'text-gray-600'
                    }`}
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Interactive</span>
                  </button>
                </div>
              </div>
            </div>

            {filteredStories.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                {isOwnProfile 
                  ? storyFilter === 'all' 
                    ? "You haven't created any stories yet." 
                    : storyFilter === 'written'
                    ? "You haven't written any stories yet."
                    : "You haven't created any interactive stories yet."
                  : storyFilter === 'all'
                  ? "This user hasn't created any stories yet."
                  : storyFilter === 'written'
                  ? "This user hasn't written any stories yet."
                  : "This user hasn't created any interactive stories yet."}
              </p>
            ) : (
              <div className="space-y-4">
                {filteredStories.map((story) => {
                  const imageUrl = getImageUrl(story.cover_image)
                  
                  return (
                    <div
                      key={story.id}
                      onClick={() => navigate(`/story/${story.id}`)}
                      className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-gray-50 cursor-pointer transition-all transform hover:-translate-y-0.5"
                    >
                      <div className="flex items-start space-x-4">
                        {imageUrl ? (
                          <img 
                            src={imageUrl} 
                            alt={story.title}
                            className="w-20 h-20 object-cover rounded-lg"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none'
                              e.currentTarget.parentElement!.innerHTML = `
                                <div class="w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex items-center justify-center">
                                  ${story.story_type === 'interactive' 
                                    ? '<svg class="w-8 h-8 text-primary-600" ...></svg>' 
                                    : '<svg class="w-8 h-8 text-primary-600" ...></svg>'
                                  }
                                </div>
                              `
                            }}
                          />
                        ) : (
                          <div className="w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex items-center justify-center">
                            {story.story_type === 'interactive' ? (
                              <Sparkles className="w-8 h-8 text-primary-600" />
                            ) : (
                              <BookOpen className="w-8 h-8 text-primary-600" />
                            )}
                          </div>
                        )}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <h3 className="text-lg font-semibold text-gray-900">{story.title}</h3>
                            {story.story_type === 'interactive' ? (
                              <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs flex items-center space-x-1">
                                <Sparkles className="w-3 h-3" />
                                <span>Interactive</span>
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs flex items-center space-x-1">
                                <PenTool className="w-3 h-3" />
                                <span>Written</span>
                              </span>
                            )}
                          </div>
                          <p className="text-gray-600 text-sm line-clamp-2">{story.excerpt}</p>
                          <div className="flex items-center space-x-4 mt-3 text-xs text-gray-500">
                            <span className="flex items-center">
                              <Eye className="w-3 h-3 mr-1" />
                              {story.view_count}
                            </span>
                            <span className="flex items-center">
                              <Heart className="w-3 h-3 mr-1" />
                              {story.like_count}
                            </span>
                            <span className="flex items-center">
                              <MessageCircle className="w-3 h-3 mr-1" />
                              {story.comment_count}
                            </span>
                            <span>{new Date(story.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {activeTab === 'about' && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">About</h2>
            <div className="space-y-4">
              <div className="flex items-center space-x-3 text-gray-700">
                <UserIcon className="w-5 h-5 text-gray-400" />
                <span>{profileUser.full_name || 'No full name provided'}</span>
              </div>
              <div className="flex items-center space-x-3 text-gray-700">
                <Mail className="w-5 h-5 text-gray-400" />
                <span>{profileUser.email}</span>
              </div>
              <div className="flex items-center space-x-3 text-gray-700">
                <Calendar className="w-5 h-5 text-gray-400" />
                <span>Joined {new Date(profileUser.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center space-x-3 text-gray-700">
                <BookOpen className="w-5 h-5 text-gray-400" />
                <span>{profileUser.stories_count} stories written</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'settings' && isOwnProfile && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Profile Settings</h2>
            <form onSubmit={handleEditSubmit} className="space-y-4 max-w-md">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  className="input-field"
                  placeholder="Your full name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="input-field"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bio
                </label>
                <textarea
                  value={editForm.bio}
                  onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                  className="input-field"
                  rows={4}
                  placeholder="Tell us about yourself..."
                />
              </div>
              
              <div className="flex space-x-3">
                <button type="submit" className="btn-primary">
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      <UserListModal
        isOpen={showFollowersModal}
        onClose={() => setShowFollowersModal(false)}
        username={profileUser.username}
        type="followers"
        initialCount={followerCount}
      />

      <UserListModal
        isOpen={showFollowingModal}
        onClose={() => setShowFollowingModal(false)}
        username={profileUser.username}
        type="following"
        initialCount={followingCount}
      />
    </div>
  )
}

export default Profile