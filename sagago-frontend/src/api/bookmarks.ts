import apiClient from './client'

export interface Bookmark {
  id: number
  user_id: number
  story_id: number
  created_at: string
  is_read: boolean
  story_title: string
  story_excerpt?: string
  story_author: string
  story_cover?: string
}

export interface BookmarkListResponse {
  bookmarks: Bookmark[]
  total: number
  page: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export const bookmarksApi = {
  addBookmark: async (storyId: number) => {
    const response = await apiClient.post('/bookmarks/', { story_id: storyId })
    return response.data
  },

  removeBookmark: async (storyId: number) => {
    const response = await apiClient.delete(`/bookmarks/${storyId}`)
    return response.data
  },

  getBookmarks: async (page: number = 1, readStatus?: boolean) => {
    let url = `/bookmarks/?page=${page}`
    if (readStatus !== undefined) {
      url += `&read_status=${readStatus}`
    }
    const response = await apiClient.get(url)
    return response.data
  },

  markAsRead: async (storyId: number) => {
    const response = await apiClient.put(`/bookmarks/${storyId}/read`)
    return response.data
  },

  checkBookmark: async (storyId: number) => {
    const response = await apiClient.get(`/bookmarks/check/${storyId}`)
    return response.data
  }
}