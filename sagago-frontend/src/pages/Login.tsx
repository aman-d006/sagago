import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { toast } from 'react-toastify'
import BackButton from '../components/ui/BackButton'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<{[key: string]: string}>({})
  const navigate = useNavigate()
  const { login, isLoading } = useAuthStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFieldErrors({})
    
    try {
      await login(username, password)
      toast.success('Login successful!')
      navigate('/')
    } catch (error: any) {
      console.error('Login error:', error)
      
      const errorDetail = error.response?.data?.detail
      
      if (typeof errorDetail === 'string') {
        toast.error(errorDetail)
      } else if (errorDetail?.field && errorDetail?.message) {
        setFieldErrors({ [errorDetail.field]: errorDetail.message })
        toast.error(errorDetail.message)
      } else {
        toast.error('Login failed. Check your credentials.')
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <div className="mb-4">
          <BackButton to="/" label="Back to Home" />
        </div>
        <div className="space-y-8">
          <div>
            <h2 className="text-center text-3xl font-extrabold text-gray-900">
              Sign in to SagaGo
            </h2>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <input
                  type="text"
                  required
                  className={`input-field rounded-t-md ${fieldErrors.username ? 'border-red-500' : ''}`}
                  placeholder="Username or Email"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value)
                    setFieldErrors({})
                  }}
                />
                {fieldErrors.username && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.username}</p>
                )}
              </div>
              <div>
                <input
                  type="password"
                  required
                  className={`input-field rounded-b-md ${fieldErrors.password ? 'border-red-500' : ''}`}
                  placeholder="Password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    setFieldErrors({})
                  }}
                />
                {fieldErrors.password && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.password}</p>
                )}
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full"
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>

            <div className="text-center">
              <Link to="/register" className="text-primary-600 hover:text-primary-500">
                Don't have an account? Sign up
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Login