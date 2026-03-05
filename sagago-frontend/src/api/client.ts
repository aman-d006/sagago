// src/api/client.ts
import axios from 'axios'

// Log the environment variables
console.log('🌍 Environment Variables:', {
  VITE_API_URL: import.meta.env.VITE_API_URL,
  VITE_IMAGE_BASE_URL: import.meta.env.VITE_IMAGE_BASE_URL,
  MODE: import.meta.env.MODE,
  DEV: import.meta.env.DEV
})

const API_URL = import.meta.env.VITE_API_URL

if (!API_URL) {
  console.error('❌ VITE_API_URL is not defined!')
} else {
  console.log('✅ Using API URL:', API_URL)
}

const apiClient = axios.create({
  baseURL: API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : ''),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Add this line to enable sending cookies/credentials
})

// Request interceptor to add token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Log requests in development
    if (import.meta.env.DEV) {
      console.log(`🔍 Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, 
        config.data || config.params || '')
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    // Log responses in development
    if (import.meta.env.DEV) {
      console.log(`🔍 Response success: ${response.status}`, response.data)
    }
    return response
  },
  (error) => {
    // Log errors in development
    if (import.meta.env.DEV) {
      console.log(`🔍 Response error:`, {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      })
    }
    
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    
    return Promise.reject(error)
  }
)

export default apiClient