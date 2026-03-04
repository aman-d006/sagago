import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import { useAuthStore } from './stores/authStore'
import { useEffect, useState } from 'react'
import { Loader } from 'lucide-react'
import './testEnv'

import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Home from './pages/Home'
import CreateStory from './pages/CreateStory'
import WriteStory from './pages/WriteStory'
import AssistedStory from './pages/AssistedStory'
import StoryReader from './pages/StoryReader'
import Profile from './pages/Profile'
import Notifications from './pages/Notifications'
import Explore from './pages/Explore'
import Feed from './pages/Feed'
import UserSearch from './pages/UserSearch'
import Navbar from './components/layout/Navbar'
import GenrePage from './pages/GenrePage'
import EditStory from './pages/EditStory'
import ReadingList from './pages/ReadingList'
import AnalyticsDashboard from './pages/AnalyticsDashboard'
import Messages from './pages/Messages'
import Templates from './pages/Templates'
import './App.css'

function App() {
  const { token, user, fetchCurrentUser } = useAuthStore()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('token')
      console.log('🔍 App init - stored token:', storedToken)
      
      if (storedToken && !user) {
        try {
          await fetchCurrentUser()
        } catch (error) {
          console.error('Failed to fetch user on init:', error)
        }
      }
      setIsLoading(false)
    }
    
    initAuth()
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  console.log('🔍 App render - token:', token, 'user:', user)

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        {token && <Navbar />}
        
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={!token ? <Landing /> : <Navigate to="/home" />} />
            <Route path="/login" element={!token ? <Login /> : <Navigate to="/home" />} />
            <Route path="/register" element={!token ? <Register /> : <Navigate to="/home" />} />
            <Route path="/genre/:genre" element={token ? <GenrePage /> : <Navigate to="/" />} />
            <Route path="/home" element={token ? <Home /> : <Navigate to="/" />} />
            <Route path="/create" element={token ? <CreateStory /> : <Navigate to="/" />} />
            <Route path="/write" element={token ? <WriteStory /> : <Navigate to="/" />} />
            <Route path="/assisted" element={token ? <AssistedStory /> : <Navigate to="/" />} />
            <Route path="/story/:id" element={token ? <StoryReader /> : <Navigate to="/" />} />
            <Route path="/profile/:username" element={token ? <Profile /> : <Navigate to="/" />} />
            <Route path="/notifications" element={token ? <Notifications /> : <Navigate to="/" />} />
            <Route path="/explore" element={token ? <Explore /> : <Navigate to="/" />} />
            <Route path="/feed" element={token ? <Feed /> : <Navigate to="/" />} />
            <Route path="/search/users" element={token ? <UserSearch /> : <Navigate to="/" />} />
            <Route path="/edit-story/:id" element={token ? <EditStory /> : <Navigate to="/" />} />
            <Route path="/reading-list" element={token ? <ReadingList /> : <Navigate to="/" />} />
            <Route path="/analytics" element={token ? <AnalyticsDashboard /> : <Navigate to="/" />} />
            <Route path="/messages" element={token ? <Messages /> : <Navigate to="/" />} />
            <Route path="/templates" element={token ? <Templates /> : <Navigate to="/" />} />
          </Routes>
        </main>
        <ToastContainer position="top-right" />
      </div>
    </BrowserRouter>
  )
}

export default App