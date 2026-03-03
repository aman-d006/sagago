import apiClient from './client'

export interface Template {
  id: number
  title: string
  description?: string
  genre?: string
  content_structure: {
    outline: string[]
    characters?: Array<{ role: string; description: string }>
    settings?: string[]
    plot_points?: string[]
  }
  prompt?: string
  cover_image?: string
  is_premium: boolean
  usage_count: number
  created_at: string
  creator_username?: string
  is_favorite: boolean
}

export interface TemplateListResponse {
  templates: Template[]
  total: number
  page: number
  pages: number
}

export interface WritingPrompt {
  id: number
  prompt: string
  genre?: string
  difficulty: string
  created_at: string
}

export interface UseTemplateRequest {
  custom_title?: string
}

export interface UseTemplateResponse {
  story_id: number
  title: string
  message: string
}

export const templatesApi = {
  getTemplates: async (page: number = 1, genre?: string, search?: string, sort: string = 'popular') => {
    let url = `/templates/?page=${page}&sort=${sort}`
    if (genre) url += `&genre=${genre}`
    if (search) url += `&search=${encodeURIComponent(search)}`
    const response = await apiClient.get(url)
    return response.data
  },

  getTemplate: async (templateId: number) => {
    const response = await apiClient.get(`/templates/${templateId}`)
    return response.data
  },

  useTemplate: async (templateId: number, customTitle?: string) => {
    const response = await apiClient.post(`/templates/${templateId}/use`, {
      custom_title: customTitle
    })
    return response.data
  },

  toggleFavorite: async (templateId: number) => {
    const response = await apiClient.post(`/templates/${templateId}/favorite`)
    return response.data
  },

  getFavorites: async () => {
    const response = await apiClient.get('/templates/favorites')
    return response.data
  },

  getDailyPrompt: async () => {
    const response = await apiClient.get('/templates/prompts/daily')
    return response.data
  },

  createTemplate: async (templateData: any) => {
    const response = await apiClient.post('/templates/', templateData)
    return response.data
  }
}