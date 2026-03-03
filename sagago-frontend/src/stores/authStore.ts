import { create } from 'zustand'
import apiClient from '../api/client'

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  avatar_url?: string
  bio?: string
  followers_count: number
  following_count: number
  stories_count: number
  created_at?: string
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (data: any) => Promise<void>
  logout: () => void
  fetchCurrentUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isLoading: false,

  login: async (username, password) => {
    set({ isLoading: true })
    try {
      console.log('🔍 Attempting login with:', { username, password })
      
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)
      
      const response = await apiClient.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      
      console.log('🔍 Login response:', response.data)
      
      const { access_token } = response.data
      localStorage.setItem('token', access_token)
      console.log('🔍 Token saved to localStorage:', access_token)
      
      set({ token: access_token })
      
      await useAuthStore.getState().fetchCurrentUser()
    } catch (error: any) {
      console.error('🔍 Login error:', error.response?.data || error.message)
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  register: async (data) => {
    set({ isLoading: true })
    try {
      console.log('🔍 Attempting registration:', data)
      await apiClient.post('/auth/register', data)
      await useAuthStore.getState().login(data.username, data.password)
    } catch (error: any) {
      console.error('🔍 Registration error:', error.response?.data || error.message)
      throw error
    } finally {
      set({ isLoading: false })
    }
  },

  logout: () => {
    console.log('🔍 Logging out, removing token')
    localStorage.removeItem('token')
    set({ user: null, token: null })
  },

  fetchCurrentUser: async () => {
    try {
      console.log('🔍 Fetching current user with token:', localStorage.getItem('token'))
      const response = await apiClient.get('/auth/me')
      console.log('🔍 User data received:', response.data)
      set({ user: response.data })
    } catch (error) {
      console.error('❌ Failed to fetch user:', error)
 
      localStorage.removeItem('token')
      set({ token: null, user: null })
    }
  },
}))

const token = localStorage.getItem('token')
console.log('🔍 Initial token check:', token)
if (token) {
  useAuthStore.getState().fetchCurrentUser()
}