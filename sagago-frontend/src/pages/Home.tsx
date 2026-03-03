import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { storiesApi } from '../api/stories'
import { usersApi } from '../api/users'
import { getImageUrl } from '../utils/imageHelpers'
import { 
  Sparkles, 
  TrendingUp, 
  Users, 
  BookOpen, 
  Heart,
  MessageCircle,
  ChevronRight,
  Wand2,
  FileText,
  Flame,
  User,
  Calendar,
  Eye,
  Award,
  Zap,
  Feather,
  Layers,
  Compass,
  Clock,
  Star
} from 'lucide-react'
import type { Story } from '../types'

const Home = () => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'for-you' | 'following' | 'trending'>('for-you')
  const [stories, setStories] = useState<Story[]>([])
  const [trendingStories, setTrendingStories] = useState<Story[]>([])
  const [recommendedStories, setRecommendedStories] = useState<Story[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [userStats, setUserStats] = useState({
    totalStories: 0,
    totalViews: 0,
    totalLikes: 0,
    followersCount: 0,
    followingCount: 0,
    joinDate: '',
    readingStreak: 7
  })

  useEffect(() => {
    fetchInitialData()
  }, [])

  useEffect(() => {
    fetchFeed()
  }, [activeTab])

  const fetchInitialData = async () => {
    try {
      const [myStories, trending, userProfile] = await Promise.all([
        storiesApi.getMyStories(),
        storiesApi.getFeed('trending', 'week', 1),
        usersApi.getUserByUsername(user?.username || '')
      ])

      const totalViews = myStories.reduce((acc, s) => acc + (s.view_count || 0), 0)
      const totalLikes = myStories.reduce((acc, s) => acc + (s.like_count || 0), 0)

      setUserStats({
        totalStories: myStories.length,
        totalViews,
        totalLikes,
        followersCount: userProfile.followers_count || 0,
        followingCount: userProfile.following_count || 0,
        joinDate: userProfile.created_at || new Date().toISOString(),
        readingStreak: Math.floor(Math.random() * 30) + 1
      })

      setTrendingStories(trending.stories.slice(0, 5))
      setRecommendedStories(trending.stories.slice(0, 3))
    } catch (error) {
      console.error('Failed to fetch initial data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchFeed = async () => {
    try {
      let response
      switch (activeTab) {
        case 'following':
          response = await storiesApi.getFollowingFeed(1)
          break
        case 'trending':
          response = await storiesApi.getFeed('trending', 'week', 1)
          break
        default:
          response = await storiesApi.getLatestFeed(1)
      }
      setStories(response.stories.slice(0, 6))
    } catch (error) {
      console.error('Failed to fetch feed:', error)
    }
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  const QuickActionCard = ({ to, icon: Icon, title, description, color }: any) => (
    <Link
      to={to}
      className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all p-4 border border-gray-100 group"
    >
      <div className={`w-10 h-10 ${color} rounded-lg flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-xs text-gray-500">{description}</p>
    </Link>
  )

  const StoryCard = ({ story, variant = 'default' }: { story: Story; variant?: 'default' | 'compact' }) => {
    const imageUrl = getImageUrl(story.cover_image)
    
    if (variant === 'compact') {
      return (
        <div 
          onClick={() => navigate(`/story/${story.id}`)}
          className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors group"
        >
          <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-purple-100 rounded-lg flex-shrink-0 overflow-hidden">
            {imageUrl ? (
              <img src={imageUrl} alt={story.title} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-primary-400" />
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate group-hover:text-primary-600 transition-colors">
              {story.title}
            </p>
            <p className="text-xs text-gray-500">by {story.author?.username}</p>
          </div>
        </div>
      )
    }

    return (
      <div 
        onClick={() => navigate(`/story/${story.id}`)}
        className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-all cursor-pointer border border-gray-100 overflow-hidden group"
      >
        <div className="relative h-48 bg-gradient-to-br from-primary-500 to-primary-700">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={story.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              onError={(e) => {
                e.currentTarget.style.display = 'none'
                e.currentTarget.parentElement!.innerHTML = '<div class="w-full h-full flex items-center justify-center"><span class="text-4xl text-white opacity-50">📖</span></div>'
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-4xl text-white opacity-50">📖</span>
            </div>
          )}
          
          {story.story_type === 'interactive' && (
            <span className="absolute top-3 right-3 px-2 py-1 bg-purple-600/90 backdrop-blur-sm text-white text-xs rounded-full flex items-center">
              <Sparkles className="w-3 h-3 mr-1" />
              Interactive
            </span>
          )}
        </div>

        <div className="p-4">
          <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1 group-hover:text-primary-600 transition-colors">
            {story.title}
          </h3>
          <p className="text-sm text-gray-500 mb-3 line-clamp-2">{story.excerpt}</p>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-xs font-bold text-primary-600">
                  {story.author?.username?.charAt(0).toUpperCase()}
                </span>
              </div>
              <span className="text-xs text-gray-500">{story.author?.username}</span>
            </div>
            
            <div className="flex items-center space-x-2 text-xs text-gray-400">
              <span className="flex items-center">
                <Heart className="w-3 h-3 mr-1" />
                {formatNumber(story.like_count || 0)}
              </span>
              <span className="flex items-center">
                <MessageCircle className="w-3 h-3 mr-1" />
                {formatNumber(story.comment_count || 0)}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your creative space...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
        {/* Welcome Header - Simplified */}
        <div className="mb-8">
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">
            Welcome back, <span className="text-primary-600">{user?.username}</span>!
          </h1>
          <p className="text-gray-500 mt-1 flex items-center">
            <Calendar className="w-4 h-4 mr-2" />
            {new Date().toLocaleDateString('en-US', { 
              weekday: 'long', 
              month: 'long', 
              day: 'numeric', 
              year: 'numeric' 
            })}
          </p>
        </div>

        {/* Top Row - Create Box + Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
          {/* Create Story Box - Center Stage */}
          <div className="lg:col-span-7">
            <div className="bg-gradient-to-r from-primary-600 via-purple-600 to-indigo-600 rounded-2xl shadow-lg p-6 text-white h-full">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold">What will you create today?</h2>
                  <p className="text-white/80 text-sm">Choose your adventure</p>
                </div>
                <Feather className="w-8 h-8 text-white/60" />
              </div>
              
              <div className="grid grid-cols-3 gap-3">
                <Link
                  to="/create"
                  className="bg-white/10 hover:bg-white/20 backdrop-blur-sm rounded-xl p-4 transition-all text-center group"
                >
                  <Sparkles className="w-6 h-6 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium">AI Game</span>
                  <span className="text-xs text-white/70 block">Interactive</span>
                </Link>
                <Link
                  to="/assisted"
                  className="bg-white/10 hover:bg-white/20 backdrop-blur-sm rounded-xl p-4 transition-all text-center group"
                >
                  <Wand2 className="w-6 h-6 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium">AI Assist</span>
                  <span className="text-xs text-white/70 block">Full story</span>
                </Link>
                <Link
                  to="/write"
                  className="bg-white/10 hover:bg-white/20 backdrop-blur-sm rounded-xl p-4 transition-all text-center group"
                >
                  <FileText className="w-6 h-6 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium">Write Own</span>
                  <span className="text-xs text-white/70 block">Manual</span>
                </Link>
              </div>
            </div>
          </div>

          {/* Quick Actions - Right Side */}
          <div className="lg:col-span-5">
            <div className="grid grid-cols-2 gap-4 h-full">
              <QuickActionCard
                to="/templates"
                icon={Layers}
                title="Templates"
                description="Pre-built story structures"
                color="bg-purple-500"
              />
              <QuickActionCard
                to="/reading-list"
                icon={BookOpen}
                title="Reading List"
                description="Saved for later"
                color="bg-blue-500"
              />
              <QuickActionCard
                to="/analytics"
                icon={TrendingUp}
                title="Analytics"
                description="Track your performance"
                color="bg-green-500"
              />
              <QuickActionCard
                to="/explore"
                icon={Compass}
                title="Explore"
                description="Discover new stories"
                color="bg-orange-500"
              />
            </div>
          </div>
        </div>

        {/* Second Row - Discovery & Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
          {/* Left - User Stats Card */}
          <div className="lg:col-span-4">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 h-full">
              <div className="flex items-center space-x-4 mb-4">
                <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-purple-100 rounded-2xl flex items-center justify-center">
                  {user?.avatar_url ? (
                    <img src={user.avatar_url} alt={user.username} className="w-16 h-16 rounded-2xl object-cover" />
                  ) : (
                    <span className="text-2xl font-bold text-primary-600">
                      {user?.username.charAt(0).toUpperCase()}
                    </span>
                  )}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{user?.full_name || user?.username}</h2>
                  <p className="text-sm text-gray-500">@{user?.username}</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center py-4 border-t border-gray-100">
                <div>
                  <div className="text-xl font-bold text-gray-900">{userStats.totalStories}</div>
                  <div className="text-xs text-gray-500">Stories</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-gray-900">{formatNumber(userStats.followersCount)}</div>
                  <div className="text-xs text-gray-500">Followers</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-gray-900">{formatNumber(userStats.followingCount)}</div>
                  <div className="text-xs text-gray-500">Following</div>
                </div>
              </div>

              <div className="space-y-2 mt-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 flex items-center">
                    <Eye className="w-4 h-4 mr-2" /> Total Views
                  </span>
                  <span className="font-semibold text-gray-900">{formatNumber(userStats.totalViews)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 flex items-center">
                    <Heart className="w-4 h-4 mr-2" /> Total Likes
                  </span>
                  <span className="font-semibold text-gray-900">{formatNumber(userStats.totalLikes)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 flex items-center">
                    <Flame className="w-4 h-4 mr-2 text-orange-500" /> Reading Streak
                  </span>
                  <span className="font-semibold text-orange-500">{userStats.readingStreak} days</span>
                </div>
              </div>

              <Link
                to={`/profile/${user?.username}`}
                className="block text-center text-sm bg-primary-50 text-primary-600 hover:bg-primary-100 rounded-xl py-2.5 mt-4 transition-colors font-medium"
              >
                View Full Profile
              </Link>
            </div>
          </div>

          {/* Center - Recommended Stories */}
          <div className="lg:col-span-4">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 h-full">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                <Award className="w-5 h-5 mr-2 text-yellow-500" />
                Recommended for You
              </h3>
              <div className="space-y-3">
                {recommendedStories.length > 0 ? (
                  recommendedStories.map(story => (
                    <StoryCard key={story.id} story={story} variant="compact" />
                  ))
                ) : (
                  <p className="text-gray-500 text-sm text-center py-8">No recommendations yet</p>
                )}
              </div>
            </div>
          </div>

          {/* Right - Trending Now */}
          <div className="lg:col-span-4">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 h-full">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                <Flame className="w-5 h-5 mr-2 text-orange-500" />
                Trending Now
              </h3>
              <div className="space-y-2">
                {trendingStories.map((story, index) => (
                  <div
                    key={story.id}
                    onClick={() => navigate(`/story/${story.id}`)}
                    className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded-lg cursor-pointer group"
                  >
                    <div className="w-6 h-6 bg-gradient-to-br from-orange-100 to-orange-200 rounded-full flex items-center justify-center text-xs font-bold text-orange-600">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 group-hover:text-primary-600 transition-colors truncate">
                        {story.title}
                      </p>
                      <p className="text-xs text-gray-500">by {story.author?.username}</p>
                    </div>
                  </div>
                ))}
              </div>
              <Link
                to="/explore?sort=trending"
                className="block text-center text-sm text-primary-600 hover:text-primary-700 mt-4 pt-4 border-t border-gray-100"
              >
                View all trending
              </Link>
            </div>
          </div>
        </div>

        {/* Feed Section */}
        <div className="space-y-6">
          {/* Feed Tabs */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-1">
            <div className="flex">
              <button
                onClick={() => setActiveTab('for-you')}
                className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all ${
                  activeTab === 'for-you' 
                    ? 'bg-primary-600 text-white shadow-md' 
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Sparkles className="w-4 h-4 inline mr-2" />
                For You
              </button>
              <button
                onClick={() => setActiveTab('following')}
                className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all ${
                  activeTab === 'following' 
                    ? 'bg-primary-600 text-white shadow-md' 
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Users className="w-4 h-4 inline mr-2" />
                Following
              </button>
              <button
                onClick={() => setActiveTab('trending')}
                className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all ${
                  activeTab === 'trending' 
                    ? 'bg-primary-600 text-white shadow-md' 
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Flame className="w-4 h-4 inline mr-2" />
                Trending
              </button>
            </div>
          </div>

          {/* Stories Grid */}
          {stories.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {stories.map(story => (
                <StoryCard key={story.id} story={story} />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No stories yet</h3>
              <p className="text-gray-500 mb-6">
                {activeTab === 'following' 
                  ? 'Follow writers to see their stories here'
                  : 'Be the first to share a story!'}
              </p>
              {activeTab === 'following' ? (
                <Link
                  to="/search/users"
                  className="inline-flex items-center px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors"
                >
                  <Users className="w-4 h-4 mr-2" />
                  Find Writers
                </Link>
              ) : (
                <Link
                  to="/create"
                  className="inline-flex items-center px-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition-colors"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Create Story
                </Link>
              )}
            </div>
          )}

          {/* View All Link */}
          <div className="text-center">
            <Link
              to="/explore"
              className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium group"
            >
              Explore all stories
              <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home