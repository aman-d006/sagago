import apiClient from './client'
import type { Story, FeedResponse, JobResponse } from '../types'

export const storiesApi = {

  createJob: async (theme: string): Promise<JobResponse> => {
    const response = await apiClient.post('/jobs/', { theme })
    return response.data
  },

  getJobStatus: async (jobId: string): Promise<JobResponse> => {
    const response = await apiClient.get(`/jobs/${jobId}`)
    return response.data
  },

  generateFullStory: async (theme: string): Promise<JobResponse> => {
    const response = await apiClient.post('/stories/generate-full', { theme })
    return response.data
  },

  getStoryMetadata: async (storyId: number): Promise<{ id: number; title: string; story_type: string; has_nodes: boolean }> => {
    const response = await apiClient.get(`/stories/metadata/${storyId}`)
    return response.data
  },

  getStory: async (storyId: number): Promise<Story> => {
    const response = await apiClient.get(`/stories/${storyId}`)
    return response.data
  },

  getInteractiveStory: async (storyId: number): Promise<Story> => {
    const response = await apiClient.get(`/stories/${storyId}/complete`)
    return response.data
  },

  getFullStory: async (storyId: number): Promise<Story> => {
    const response = await apiClient.get(`/stories/${storyId}/full`)
    return response.data
  },

  getExploreFeed: async (page: number = 1, limit: number = 20, genre?: string, sort?: string): Promise<FeedResponse> => {
    let url = `/stories/explore?page=${page}&limit=${limit}`
    if (genre && genre !== 'all') {
      url += `&genre=${encodeURIComponent(genre)}`
    }
    if (sort) {
      url += `&sort=${sort}`
    }
    const response = await apiClient.get(url)
    return response.data
  },

  publishWrittenStory: async (storyData: any): Promise<JobResponse> => {
    console.log('📝 Publishing written story with data:', {
      title: storyData.title,
      content_length: storyData.content?.length,
      has_cover_image: !!storyData.cover_image,
      cover_image: storyData.cover_image
    })
    
    const payload = {
      theme: `Write a story titled "${storyData.title}" with the following content: ${storyData.content}`,
      cover_image: storyData.cover_image || undefined
    }
    
    console.log('📤 Sending payload:', payload)
    
    const response = await apiClient.post('/stories/generate-assisted', payload)
    return response.data
  },

  publishInteractiveStory: async (storyId: number) => {
    const response = await apiClient.post(`/stories/${storyId}/publish-interactive`)
    return response.data
  },

  getMyStories: async (type?: 'interactive' | 'written'): Promise<Story[]> => {
    const url = type ? `/stories/my-stories?type=${type}` : '/stories/my-stories'
    const response = await apiClient.get(url)
    return response.data
  },

  likeStory: async (storyId: number) => {
    const response = await apiClient.post(`/stories/${storyId}/like`)
    return response.data
  },

  getFeed: async (feedType: string, timeframe: string, page: number = 1): Promise<FeedResponse> => {
    const response = await apiClient.get(`/feed/?feed_type=${feedType}&timeframe=${timeframe}&page=${page}`)
    return response.data
  },

  getFollowingFeed: async (page: number = 1): Promise<FeedResponse> => {
    const response = await apiClient.get(`/feed/following?page=${page}`)
    return response.data
  },

  getPopularFeed: async (timeframe: string, page: number = 1): Promise<FeedResponse> => {
    const response = await apiClient.get(`/feed/popular?timeframe=${timeframe}&page=${page}`)
    return response.data
  },

  getLatestFeed: async (page: number = 1): Promise<FeedResponse> => {
    const response = await apiClient.get(`/feed/latest?page=${page}`)
    return response.data
  },

  updateStory: async (storyId: number, data: any) => {
    const response = await apiClient.put(`/stories/${storyId}`, data)
    return response.data
  },

  deleteStory: async (storyId: number) => {
    const response = await apiClient.delete(`/stories/${storyId}`)
    return response.data
  },

  createAssistedStory: async (prompt: string, coverImage?: string): Promise<JobResponse> => {
    const response = await apiClient.post('/stories/generate-assisted', { 
      theme: prompt,
      cover_image: coverImage 
    })
    return response.data
  },

  uploadImage: async (file: File): Promise<{ url: string; message: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post('/stories/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },
}