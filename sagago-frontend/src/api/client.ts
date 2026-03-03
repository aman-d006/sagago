import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
console.log('🔍 API URL:', API_URL)

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, 
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  console.log('🔍 Request:', config.method?.toUpperCase(), config.url)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    console.log('🔍 Token found:', token.substring(0, 20) + '...')
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => {
    console.log('🔍 Response success:', response.status)
    return response
  },
  (error) => {
    console.log('🔍 Response error:', error.response?.status, error.response?.data)
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient