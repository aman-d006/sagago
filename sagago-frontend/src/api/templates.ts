// api/templates.ts
import apiClient from './client'
import { DEFAULT_TEMPLATES, DAILY_PROMPTS, type Template } from '../data/templates'

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

export interface UseTemplateResponse {
  story_id: number
  title: string
  message: string
}

// Helper to get a random daily prompt
const getRandomPrompt = (): WritingPrompt => {
  const randomIndex = Math.floor(Math.random() * DAILY_PROMPTS.length);
  return DAILY_PROMPTS[randomIndex];
};

// Helper to filter and paginate templates
const getLocalTemplates = (
  page: number = 1,
  genre?: string,
  search?: string,
  sort: string = 'popular'
) => {
  console.log('📋 Using local templates with params:', { page, genre, search, sort });
  
  // Filter
  let filtered = [...DEFAULT_TEMPLATES]
  
  if (genre && genre !== 'all') {
    filtered = filtered.filter(t => t.genre === genre)
  }
  
  if (search) {
    const searchLower = search.toLowerCase()
    filtered = filtered.filter(t => 
      t.title.toLowerCase().includes(searchLower) ||
      t.description?.toLowerCase().includes(searchLower)
    )
  }
  
  // Sort
  if (sort === 'popular') {
    filtered.sort((a, b) => b.usage_count - a.usage_count)
  } else if (sort === 'newest') {
    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  } else { // title
    filtered.sort((a, b) => a.title.localeCompare(b.title))
  }
  
  // Paginate
  const perPage = 20
  const start = (page - 1) * perPage
  const paginatedTemplates = filtered.slice(start, start + perPage)
  
  const result = {
    templates: paginatedTemplates,
    total: filtered.length,
    page: page,
    pages: Math.ceil(filtered.length / perPage)
  }
  
  console.log('📋 Local templates result:', result);
  return result;
};

export const templatesApi = {
  getTemplates: async (page: number = 1, genre?: string, search?: string, sort: string = 'popular'): Promise<TemplateListResponse> => {
    try {
      // Try to fetch from API first
      let url = `/templates/?page=${page}&sort=${sort}`
      if (genre) url += `&genre=${genre}`
      if (search) url += `&search=${encodeURIComponent(search)}`
      
      const response = await apiClient.get(url)
      console.log('📡 Templates from API:', response.data)
      
      // Check if API returned empty templates
      if (!response.data.templates || response.data.templates.length === 0) {
        console.log('⚠️ API returned empty templates, using local templates instead')
        return getLocalTemplates(page, genre, search, sort)
      }
      
      return response.data
    } catch (error) {
      console.log('⚠️ API failed, using local templates:', error)
      // Return local templates as fallback
      return getLocalTemplates(page, genre, search, sort)
    }
  },

  getTemplate: async (templateId: number): Promise<Template> => {
    try {
      const response = await apiClient.get(`/templates/${templateId}`)
      return response.data
    } catch (error) {
      console.log('⚠️ API failed, using local template:', error)
      const template = DEFAULT_TEMPLATES.find(t => t.id === templateId)
      if (!template) throw new Error('Template not found')
      return template
    }
  },

  getDailyPrompt: async (): Promise<WritingPrompt> => {
    try {
      const response = await apiClient.get('/templates/prompts/daily')
      console.log('📡 Daily prompt from API:', response.data)
      return response.data
    } catch (error) {
      console.log('⚠️ API failed, using local prompt:', error)
      return getRandomPrompt()
    }
  },

  getFavorites: async (): Promise<Template[]> => {
    try {
      const response = await apiClient.get('/templates/favorites')
      console.log('📡 Favorites from API:', response.data)
      return response.data
    } catch (error) {
      console.log('⚠️ API failed, returning empty favorites:', error)
      return [] // Return empty array when API fails
    }
  },

  useTemplate: async (templateId: number, customTitle?: string): Promise<UseTemplateResponse> => {
    try {
      const response = await apiClient.post(`/templates/${templateId}/use`, {
        custom_title: customTitle
      })
      return response.data
    } catch (error) {
      console.error('❌ Failed to use template:', error)
      
      // Fallback for local templates
      const template = DEFAULT_TEMPLATES.find(t => t.id === templateId)
      if (template) {
        console.log('📝 Using local template fallback for story creation')
        return {
          story_id: Date.now(),
          title: customTitle || template.title,
          message: `Story created from template "${template.title}" (local)`
        }
      }
      throw error
    }
  },

  toggleFavorite: async (templateId: number): Promise<{ message: string }> => {
    try {
      const response = await apiClient.post(`/templates/${templateId}/favorite`)
      return response.data
    } catch (error) {
      console.error('❌ Failed to toggle favorite:', error)
      // You could add localStorage for favorites here if needed
      throw error
    }
  },

  createTemplate: async (templateData: any): Promise<Template> => {
    try {
      const response = await apiClient.post('/templates/', templateData)
      return response.data
    } catch (error) {
      console.error('❌ Failed to create template:', error)
      throw error
    }
  }
}