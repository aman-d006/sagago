import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { analyticsApi } from '../api/analytics'
import BackButton from '../components/ui/BackButton'
import {
  Loader,
  Eye,
  Heart,
  MessageCircle,
  Users,
  BookOpen,
  TrendingUp,
  Clock,
  Calendar,
  BarChart3,
  Activity,
  Award,
  ChevronRight,
  Sparkles,
  PenTool
} from 'lucide-react'

interface DashboardData {
  user: {
    username: string
    full_name: string
    avatar_url?: string
    joined: string
    followers: number
    following: number
    total_stories: number
  }
  overview: {
    total_views: number
    total_likes: number
    total_comments: number
    total_read_time: number
    avg_views_per_story: number
    avg_likes_per_view: number
    avg_comments_per_view: number
  }
  recent_activity: {
    views_last_7_days: number
    likes_last_7_days: number
    comments_last_7_days: number
    new_followers_last_7_days: number
  }
  time_series: {
    labels: string[]
    views: number[]
    likes: number[]
    followers: number[]
  }
  top_stories: Array<{
    id: number
    title: string
    views: number
    likes: number
    comments: number
    story_type: string
    engagement_rate: number
  }>
  story_stats: Array<{
    id: number
    title: string
    views: number
    likes: number
    comments: number
    story_type: string
    created_at: string
  }>
}

const AnalyticsDashboard = () => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedTimeframe, setSelectedTimeframe] = useState<'week' | 'month' | 'year'>('month')
  const [selectedStory, setSelectedStory] = useState<number | null>(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const data = await analyticsApi.getMyDashboard()
      setDashboardData(data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900">No data available</h2>
        <button onClick={() => navigate('/')} className="btn-primary mt-4">
          Return Home
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <BackButton />
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
        </div>
      </div>

      {/* Welcome Card */}
      <div className="bg-gradient-to-r from-primary-600 to-purple-600 rounded-xl shadow-lg p-6 text-white mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Your Story Analytics</h2>
            <p className="text-white/90">
              Track your performance and grow your audience
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{dashboardData.user.total_stories}</div>
            <div className="text-white/80">Total Stories</div>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-gray-500">Total Views</div>
            <Eye className="w-5 h-5 text-primary-600" />
          </div>
          <div className="text-3xl font-bold text-gray-900">{formatNumber(dashboardData.overview.total_views)}</div>
          <div className="text-sm text-green-600 mt-2">
            ↑ {dashboardData.recent_activity.views_last_7_days} in last 7 days
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-gray-500">Total Likes</div>
            <Heart className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-3xl font-bold text-gray-900">{formatNumber(dashboardData.overview.total_likes)}</div>
          <div className="text-sm text-green-600 mt-2">
            ↑ {dashboardData.recent_activity.likes_last_7_days} in last 7 days
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-gray-500">Total Comments</div>
            <MessageCircle className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-3xl font-bold text-gray-900">{formatNumber(dashboardData.overview.total_comments)}</div>
          <div className="text-sm text-green-600 mt-2">
            ↑ {dashboardData.recent_activity.comments_last_7_days} in last 7 days
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-gray-500">New Followers</div>
            <Users className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-3xl font-bold text-gray-900">{formatNumber(dashboardData.user.followers)}</div>
          <div className="text-sm text-green-600 mt-2">
            ↑ {dashboardData.recent_activity.new_followers_last_7_days} in last 7 days
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Views Over Time Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-primary-600" />
            Views Over Time
          </h3>
          <div className="h-64 flex items-end space-x-2">
            {dashboardData.time_series.views.slice(-14).map((value, index) => {
              const max = Math.max(...dashboardData.time_series.views)
              const height = max > 0 ? (value / max) * 100 : 0
              return (
                <div key={index} className="flex-1 flex flex-col items-center group">
                  <div className="relative w-full">
                    <div 
                      className="bg-primary-500 rounded-t hover:bg-primary-600 transition-all cursor-pointer"
                      style={{ height: `${height}%`, minHeight: '4px' }}
                    >
                      <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                        {value} views
                      </div>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 mt-2 rotate-45 origin-left">
                    {dashboardData.time_series.labels.slice(-14)[index]?.slice(5)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Engagement Metrics */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-primary-600" />
            Engagement Metrics
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Avg. Views per Story</span>
                <span className="font-semibold text-gray-900">{dashboardData.overview.avg_views_per_story}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 rounded-full h-2"
                  style={{ width: `${Math.min(100, (dashboardData.overview.avg_views_per_story / 100) * 100)}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Likes per View</span>
                <span className="font-semibold text-gray-900">{dashboardData.overview.avg_likes_per_view}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-red-500 rounded-full h-2"
                  style={{ width: `${dashboardData.overview.avg_likes_per_view}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Comments per View</span>
                <span className="font-semibold text-gray-900">{dashboardData.overview.avg_comments_per_view}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 rounded-full h-2"
                  style={{ width: `${dashboardData.overview.avg_comments_per_view}%` }}
                />
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Total Reading Time</span>
              <span className="text-xl font-bold text-gray-900">{formatTime(dashboardData.overview.total_read_time)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Top Stories */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
          <Award className="w-5 h-5 mr-2 text-yellow-500" />
          Top Performing Stories
        </h3>
        <div className="space-y-4">
          {dashboardData.top_stories.map((story, index) => (
            <div
              key={story.id}
              onClick={() => navigate(`/story/${story.id}`)}
              className="flex items-center justify-between p-4 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors border border-gray-100"
            >
              <div className="flex items-center space-x-4">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center font-bold text-primary-600">
                  {index + 1}
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{story.title}</h4>
                  <div className="flex items-center space-x-3 text-xs text-gray-500 mt-1">
                    <span className="flex items-center">
                      {story.story_type === 'interactive' ? (
                        <Sparkles className="w-3 h-3 mr-1 text-purple-500" />
                      ) : (
                        <PenTool className="w-3 h-3 mr-1 text-blue-500" />
                      )}
                      {story.story_type === 'interactive' ? 'Interactive' : 'Written'}
                    </span>
                    <span className="flex items-center">
                      <Eye className="w-3 h-3 mr-1" />
                      {story.views} views
                    </span>
                    <span className="flex items-center">
                      <Heart className="w-3 h-3 mr-1" />
                      {story.likes} likes
                    </span>
                    <span className="flex items-center">
                      <MessageCircle className="w-3 h-3 mr-1" />
                      {story.comments} comments
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-green-600">{story.engagement_rate}%</div>
                <div className="text-xs text-gray-500">engagement</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* All Stories Stats */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">All Stories</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Title</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Type</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Views</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Likes</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Comments</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Published</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600"></th>
              </tr>
            </thead>
            <tbody>
              {dashboardData.story_stats.map((story) => (
                <tr 
                  key={story.id} 
                  className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/story/${story.id}`)}
                >
                  <td className="py-3 px-4 text-sm text-gray-900">{story.title}</td>
                  <td className="py-3 px-4">
                    {story.story_type === 'interactive' ? (
                      <span className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                        <Sparkles className="w-3 h-3 mr-1" />
                        Interactive
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                        <PenTool className="w-3 h-3 mr-1" />
                        Written
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-900">{formatNumber(story.views)}</td>
                  <td className="py-3 px-4 text-sm text-gray-900">{formatNumber(story.likes)}</td>
                  <td className="py-3 px-4 text-sm text-gray-900">{formatNumber(story.comments)}</td>
                  <td className="py-3 px-4 text-sm text-gray-500">
                    {new Date(story.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AnalyticsDashboard