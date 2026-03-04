// src/utils/imageHelpers.ts
import { API_CONFIG } from '../config/api'

export const getImageUrl = (url?: string | null): string | null => {
  if (!url) {
    if (import.meta.env.DEV) {
      console.log('getImageUrl: No URL provided')
    }
    return null
  }
  
  if (import.meta.env.DEV) {
    console.log('getImageUrl: Original URL:', url)
  }
  
  // If it's already a full URL, return as is
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url
  }
  
  // Remove trailing slash from image base URL
  const baseUrl = API_CONFIG.imageBaseURL.replace(/\/$/, '')
  
  // Ensure URL starts with /
  const path = url.startsWith('/') ? url : `/${url}`
  
  // Construct full URL
  const fullUrl = `${baseUrl}${path}`
  
  if (import.meta.env.DEV) {
    console.log('getImageUrl: Constructed full URL:', fullUrl)
  }
  
  return fullUrl
}

// Helper for story cover images
export const getStoryCoverUrl = (coverPath?: string | null): string | null => {
  return getImageUrl(coverPath)
}

// Helper for avatar images
export const getAvatarUrl = (avatarPath?: string | null): string | null => {
  return getImageUrl(avatarPath)
}

// Helper to check if an image exists
export const checkImageExists = (url: string): Promise<boolean> => {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve(true)
    img.onerror = () => resolve(false)
    img.src = url
  })
}