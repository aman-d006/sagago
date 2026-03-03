import apiClient from './client'

export const usersApi = {
  getUserByUsername: async (username: string) => {
    const response = await apiClient.get(`/users/${username}`)
    return response.data
  },

  getUserStories: async (username: string) => {
    const response = await apiClient.get(`/stories/user/${username}`)
    return response.data
  },

  followUser: async (username: string) => {
    const response = await apiClient.post(`/users/${username}/follow`)
    return response.data
  },

  checkFollowStatus: async (username: string) => {
    const response = await apiClient.get(`/users/${username}/stats`)
    return response.data
  },

  getFollowers: async (username: string, page: number = 1, limit: number = 20) => {
    const response = await apiClient.get(`/users/${username}/followers?skip=${(page-1)*limit}&limit=${limit}`)
    return response.data
  },

  getFollowing: async (username: string, page: number = 1, limit: number = 20) => {
    const response = await apiClient.get(`/users/${username}/following?skip=${(page-1)*limit}&limit=${limit}`)
    return response.data
  },

  updateProfile: async (data: { full_name?: string; bio?: string; email?: string }) => {
    const response = await apiClient.put('/users/me', data)
    return response.data
  },

  getUserCount: async (): Promise<{ total: number }> => {
    const response = await apiClient.get('/users/count')
    return response.data
  },

  getFollowSuggestions: async (limit: number = 10) => {
    const response = await apiClient.get(`/users/suggestions?limit=${limit}`)
    return response.data
  },

  searchUsers: async (query: string, limit: number = 20) => {
    const response = await apiClient.get(`/users/search?q=${encodeURIComponent(query)}&limit=${limit}`)
    return response.data
  },

  getUserById: async (userId: number) => {
    const response = await apiClient.get(`/users/id/${userId}`)
    return response.data
  },
}