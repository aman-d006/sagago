import apiClient from './client'

export const analyticsApi = {
  getMyDashboard: async () => {
    const response = await apiClient.get('/analytics/dashboard/me')
    return response.data
  },

  getStoryAnalytics: async (storyId: number) => {
    const response = await apiClient.get(`/analytics/story/${storyId}`)
    return response.data
  },

  getTrendingStories: async (days: number = 7, limit: number = 10) => {
    const response = await apiClient.get(`/analytics/trending?days=${days}&limit=${limit}`)
    return response.data
  }
}