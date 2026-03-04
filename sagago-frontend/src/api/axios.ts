import axios from 'axios'
import { API_CONFIG } from '../config/api'

const axiosInstance = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
})

axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    if (import.meta.env.DEV) {
      console.log(`🔍 Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, config.data || '')
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

axiosInstance.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`🔍 Response success: ${response.status}`, response.data)
    }
    return response
  },
  (error) => {
    if (import.meta.env.DEV) {
      console.log(`🔍 Response error:`, error.response?.status || error.message)
    }
    
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default axiosInstance