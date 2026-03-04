// src/config/api.ts
interface ApiConfig {
  baseURL: string
  imageBaseURL: string
  timeout: number
}

const getConfig = (): ApiConfig => {
  // For Vite, use import.meta.env
  const baseURL = import.meta.env.VITE_API_URL
  const imageBaseURL = import.meta.env.VITE_IMAGE_BASE_URL || baseURL

  if (!baseURL) {
    console.error('VITE_API_URL is not defined in environment variables!')
    console.error('Please create .env.development or .env.production file')
    
    // Development fallback
    if (import.meta.env.DEV) {
      console.warn('Using development fallback: http://localhost:8000')
      return {
        baseURL: 'http://localhost:8000',
        imageBaseURL: 'http://localhost:8000',
        timeout: 30000
      }
    }
    throw new Error('VITE_API_URL must be defined in production')
  }

  return {
    baseURL,
    imageBaseURL: imageBaseURL || baseURL,
    timeout: 30000
  }
}

export const API_CONFIG = getConfig()