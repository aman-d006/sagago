import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { toast } from 'react-toastify'
import BackButton from '../components/ui/BackButton'

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
  })
  const [fieldErrors, setFieldErrors] = useState<{[key: string]: string}>({})
  const [generalError, setGeneralError] = useState('')
  const navigate = useNavigate()
  const { register, isLoading } = useAuthStore()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    // Clear field error when user starts typing
    if (fieldErrors[e.target.name]) {
      setFieldErrors({ ...fieldErrors, [e.target.name]: '' })
    }
    // Clear general error when user types
    if (generalError) {
      setGeneralError('')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFieldErrors({})
    setGeneralError('')
    
    try {
      await register(formData)
      toast.success('Registration successful! Please login.')
      navigate('/login')
    } catch (error: any) {
      console.error('Registration error:', error)
      
      // Handle different error response formats
      const errorDetail = error.response?.data?.detail
      const statusCode = error.response?.status
      
      if (statusCode === 400) {
        // Handle validation errors
        if (typeof errorDetail === 'string') {
          // Check for specific error messages and map to fields
          const lowerMsg = errorDetail.toLowerCase()
          
          if (lowerMsg.includes('username')) {
            setFieldErrors({ username: errorDetail })
          } else if (lowerMsg.includes('email')) {
            setFieldErrors({ email: errorDetail })
          } else if (lowerMsg.includes('password')) {
            setFieldErrors({ password: errorDetail })
          } else {
            setGeneralError(errorDetail)
            toast.error(errorDetail)
          }
        } else if (errorDetail?.field && errorDetail?.message) {
          // Field-specific error from backend
          setFieldErrors({ [errorDetail.field]: errorDetail.message })
          toast.error(errorDetail.message)
        } else if (Array.isArray(errorDetail)) {
          // Multiple validation errors (Pydantic format)
          const newFieldErrors: {[key: string]: string} = {}
          errorDetail.forEach((err: any) => {
            if (err.loc && err.loc[1]) {
              const field = err.loc[1]
              let message = err.msg
              
              // Clean up Pydantic error messages
              if (message.includes('Value error, ')) {
                message = message.replace('Value error, ', '')
              }
              
              newFieldErrors[field] = message
            }
          })
          setFieldErrors(newFieldErrors)
          toast.error('Please fix the errors below')
        } else {
          // Try to parse error message from response
          const errorMessage = error.response?.data?.message || 
                              error.response?.data?.error || 
                              'Validation failed'
          setGeneralError(errorMessage)
          toast.error(errorMessage)
        }
      } else if (statusCode === 422) {
        // Unprocessable Entity - validation errors
        const errors = error.response?.data?.detail
        if (Array.isArray(errors)) {
          const newFieldErrors: {[key: string]: string} = {}
          errors.forEach((err: any) => {
            if (err.loc && err.loc[1]) {
              let message = err.msg
              // Make error messages more user-friendly
              if (message.includes('at least one uppercase letter')) {
                message = 'Password must contain at least one uppercase letter'
              } else if (message.includes('at least one lowercase letter')) {
                message = 'Password must contain at least one lowercase letter'
              } else if (message.includes('at least 8 characters')) {
                message = 'Password must be at least 8 characters long'
              } else if (message.includes('at least one number')) {
                message = 'Password must contain at least one number'
              }
              newFieldErrors[err.loc[1]] = message
            }
          })
          setFieldErrors(newFieldErrors)
          toast.error('Please check your input')
        } else {
          setGeneralError('Invalid input. Please check your information.')
          toast.error('Invalid input')
        }
      } else if (statusCode === 409 || statusCode === 400) {
        // Conflict - user already exists
        if (errorDetail?.includes('username')) {
          setFieldErrors({ username: 'Username already taken' })
        } else if (errorDetail?.includes('email')) {
          setFieldErrors({ email: 'Email already registered' })
        } else {
          setGeneralError(errorDetail || 'User already exists')
        }
        toast.error(errorDetail || 'Registration failed')
      } else {
        // Generic error
        setGeneralError('Registration failed. Please try again.')
        toast.error('Registration failed. Please try again.')
      }
    }
  }

  // Password strength indicator
  const getPasswordStrength = () => {
    const password = formData.password
    if (!password) return null
    
    let strength = 0
    if (password.length >= 8) strength++
    if (/[A-Z]/.test(password)) strength++
    if (/[a-z]/.test(password)) strength++
    if (/[0-9]/.test(password)) strength++
    if (/[^A-Za-z0-9]/.test(password)) strength++
    
    const strengthText = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong']
    const strengthColor = [
      'bg-red-500',
      'bg-orange-500',
      'bg-yellow-500',
      'bg-blue-500',
      'bg-green-500'
    ]
    
    return (
      <div className="mt-2">
        <div className="flex items-center space-x-1">
          {[0,1,2,3,4].map((i) => (
            <div
              key={i}
              className={`h-1 flex-1 rounded-full ${
                i < strength ? strengthColor[strength-1] : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
        <p className={`text-xs mt-1 ${
          strength === 5 ? 'text-green-600' :
          strength === 4 ? 'text-blue-600' :
          strength === 3 ? 'text-yellow-600' :
          strength === 2 ? 'text-orange-600' :
          'text-red-600'
        }`}>
          {strengthText[strength-1] || 'Very Weak'}
        </p>
      </div>
    )
  }

  // Password requirements checklist
  const PasswordRequirements = () => {
    const password = formData.password
    const requirements = [
      { text: 'At least 8 characters', test: (p: string) => p.length >= 8 },
      { text: 'At least one uppercase letter', test: (p: string) => /[A-Z]/.test(p) },
      { text: 'At least one lowercase letter', test: (p: string) => /[a-z]/.test(p) },
      { text: 'At least one number', test: (p: string) => /[0-9]/.test(p) },
    ]
    
    if (!password) return null
    
    return (
      <div className="mt-2 text-xs space-y-1">
        {requirements.map((req, index) => {
          const met = req.test(password)
          return (
            <div key={index} className="flex items-center">
              {met ? (
                <span className="text-green-500 mr-1">✓</span>
              ) : (
                <span className="text-gray-300 mr-1">○</span>
              )}
              <span className={met ? 'text-green-600' : 'text-gray-500'}>
                {req.text}
              </span>
            </div>
          )
        })}
      </div>
    )
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
              Create your account
            </h2>
          </div>
          
          {/* General Error Message */}
          {generalError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {generalError}
            </div>
          )}
          
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              {/* Email Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  name="email"
                  required
                  className={`input-field ${fieldErrors.email ? 'border-red-500 ring-red-500' : ''}`}
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                />
                {fieldErrors.email && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.email}</p>
                )}
              </div>
              
              {/* Username Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  name="username"
                  required
                  className={`input-field ${fieldErrors.username ? 'border-red-500 ring-red-500' : ''}`}
                  placeholder="johndoe"
                  value={formData.username}
                  onChange={handleChange}
                />
                {fieldErrors.username && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.username}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  3-30 characters, letters, numbers, and underscores only
                </p>
              </div>
              
              {/* Full Name Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name (Optional)
                </label>
                <input
                  type="text"
                  name="full_name"
                  className="input-field"
                  placeholder="John Doe"
                  value={formData.full_name}
                  onChange={handleChange}
                />
              </div>
              
              {/* Password Field */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  name="password"
                  required
                  className={`input-field ${fieldErrors.password ? 'border-red-500 ring-red-500' : ''}`}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                />
                {fieldErrors.password && (
                  <p className="mt-1 text-sm text-red-600">{fieldErrors.password}</p>
                )}
                
                {/* Password strength indicator */}
                {formData.password && !fieldErrors.password && (
                  <>
                    {getPasswordStrength()}
                    <PasswordRequirements />
                  </>
                )}
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full"
              >
                {isLoading ? 'Creating account...' : 'Sign up'}
              </button>
            </div>

            <div className="text-center">
              <Link to="/login" className="text-primary-600 hover:text-primary-500 text-sm">
                Already have an account? Sign in
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Register