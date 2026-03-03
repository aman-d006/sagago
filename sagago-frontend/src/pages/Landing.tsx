import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, useScroll, useTransform } from 'framer-motion'
import { 
  Sparkles, 
  PenTool, 
  Users, 
  BookOpen, 
  Heart, 
  MessageCircle,
  Eye,
  ChevronRight,
  Menu,
  X,
  Layers,
  TrendingUp,
  Clock,
  Star,
  Zap,
  Shield,
  Infinity,
  Feather,
  Compass
} from 'lucide-react'
import { storiesApi } from '../api/stories'
import { usersApi } from '../api/users'
import { useAuthStore } from '../stores/authStore'
import type { Story } from '../types'

const GENRES = [
  { id: 'fantasy', name: 'Fantasy', icon: '🧙', color: 'from-purple-500 to-indigo-500', description: 'Magic, dragons, and epic quests' },
  { id: 'sci-fi', name: 'Sci-Fi', icon: '🚀', color: 'from-blue-500 to-cyan-500', description: 'Future worlds and technology' },
  { id: 'mystery', name: 'Mystery', icon: '🔍', color: 'from-gray-700 to-gray-900', description: 'Crime, suspense, and puzzles' },
  { id: 'romance', name: 'Romance', icon: '❤️', color: 'from-pink-500 to-rose-500', description: 'Love stories and relationships' },
  { id: 'horror', name: 'Horror', icon: '👻', color: 'from-red-700 to-red-900', description: 'Terrifying tales and suspense' },
  { id: 'adventure', name: 'Adventure', icon: '⚔️', color: 'from-green-500 to-emerald-500', description: 'Journeys and exploration' }
]

const PLATFORM_FEATURES = [
  {
    icon: <Infinity className="w-6 h-6" />,
    title: 'Branching Narratives',
    description: 'Stories with 8-10 levels and 30-50 unique nodes. Every choice creates a new path.'
  },
  {
    icon: <Zap className="w-6 h-6" />,
    title: 'AI-Powered Writing',
    description: 'Generate full paragraphs, get writing suggestions, and overcome writer\'s block.'
  },
  {
    icon: <Users className="w-6 h-6" />,
    title: 'Active Community',
    description: 'Real writers and readers sharing feedback, likes, and comments daily.'
  },
  {
    icon: <Feather className="w-6 h-6" />,
    title: 'Multiple Writing Modes',
    description: 'Choose between AI-assisted, manual writing, or interactive storytelling.'
  }
]

const STORY_EXAMPLES = [
  {
    title: 'The Crystal Cave',
    genre: 'Fantasy',
    choices: '12 possible endings',
    readTime: '25 min'
  },
  {
    title: 'Neon Detective',
    genre: 'Sci-Fi',
    choices: '8 branching paths',
    readTime: '18 min'
  },
  {
    title: 'Whispers in the Dark',
    genre: 'Mystery',
    choices: '6 unique conclusions',
    readTime: '22 min'
  }
]

const Landing = () => {
  const navigate = useNavigate()
  const { token } = useAuthStore()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [featuredStories, setFeaturedStories] = useState<Story[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState({
    totalStories: 0,
    totalUsers: 0,
    totalReads: 0,
    activeToday: 0
  })
  
  const { scrollYProgress } = useScroll()
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0.8])
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.95])

  useEffect(() => {
    fetchRealData()
  }, [])

  const fetchRealData = async () => {
    try {
      const storiesResponse = await storiesApi.getExploreFeed(1, 3)
      setFeaturedStories(storiesResponse.stories)
      
      setStats({
        totalStories: storiesResponse.total || 0,
        totalUsers: 0,
        totalReads: 0,
        activeToday: 0
      })
      
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenreClick = (genreId: string) => {
    if (token) {
      navigate(`/genre/${genreId}`)
    } else {
      navigate('/register', { 
        state: { selectedGenre: genreId } 
      })
    }
  }

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
    setIsMenuOpen(false)
  }

  return (
    <div className="min-h-screen bg-white">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center"
            >
              <span className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
                SagaGo
              </span>
            </motion.div>

            <div className="hidden md:flex items-center space-x-8">
              <button onClick={() => scrollToSection('features')} className="text-gray-600 hover:text-gray-900 transition-colors">Features</button>
              <button onClick={() => scrollToSection('genres')} className="text-gray-600 hover:text-gray-900 transition-colors">Genres</button>
              <button onClick={() => scrollToSection('how-it-works')} className="text-gray-600 hover:text-gray-900 transition-colors">How It Works</button>
              <button onClick={() => scrollToSection('examples')} className="text-gray-600 hover:text-gray-900 transition-colors">Examples</button>
            </div>

            <div className="hidden md:flex items-center space-x-4">
              <Link
                to="/login"
                className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg hover:from-primary-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-md"
              >
                Get Started
              </Link>
            </div>

            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {isMenuOpen && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="md:hidden bg-white border-b border-gray-100"
          >
            <div className="container mx-auto px-4 py-4">
              <div className="flex flex-col space-y-4">
                <button onClick={() => scrollToSection('features')} className="text-gray-600 hover:text-gray-900 py-2 text-left">Features</button>
                <button onClick={() => scrollToSection('genres')} className="text-gray-600 hover:text-gray-900 py-2 text-left">Genres</button>
                <button onClick={() => scrollToSection('how-it-works')} className="text-gray-600 hover:text-gray-900 py-2 text-left">How It Works</button>
                <button onClick={() => scrollToSection('examples')} className="text-gray-600 hover:text-gray-900 py-2 text-left">Examples</button>
                <div className="pt-4 border-t border-gray-100 flex flex-col space-y-3">
                  <Link
                    to="/login"
                    className="w-full px-4 py-2 text-center text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    className="w-full px-4 py-2 text-center bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg"
                  >
                    Get Started
                  </Link>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </nav>

      <motion.section 
        style={{ opacity, scale }}
        className="relative pt-32 pb-20 overflow-hidden bg-gradient-to-br from-primary-50 via-white to-purple-50"
      >
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6">
                <span className="bg-gradient-to-r from-primary-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
                  Where Stories
                </span>
                <br />
                <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Choose Their Own Path
                </span>
              </h1>
              <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
                Create interactive stories with branching narratives. Write your way, 
                with AI assistance when you need it.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
            >
              <Link
                to="/register"
                className="group px-8 py-4 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-xl font-semibold hover:from-primary-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg flex items-center"
              >
                Start Writing Free
                <ChevronRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
              <button
                onClick={() => scrollToSection('examples')}
                className="px-8 py-4 bg-white text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition-all border border-gray-200 shadow-md flex items-center"
              >
                See Examples
              </button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="flex flex-wrap justify-center gap-6 text-sm"
            >
              {stats.totalStories > 0 && (
                <div className="flex items-center space-x-2 text-gray-600">
                  <BookOpen className="w-4 h-4 text-primary-500" />
                  <span>{stats.totalStories} stories published</span>
                </div>
              )}
              {stats.activeToday > 0 && (
                <div className="flex items-center space-x-2 text-gray-600">
                  <Users className="w-4 h-4 text-primary-500" />
                  <span>{stats.activeToday} reading now</span>
                </div>
              )}
              <div className="flex items-center space-x-2 text-gray-600">
                <Zap className="w-4 h-4 text-primary-500" />
                <span>8-10 levels per story</span>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.section>

      <section id="features" className="py-20 bg-gray-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Built for Modern Storytelling
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to create immersive, interactive narratives.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {PLATFORM_FEATURES.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-purple-100 rounded-xl flex items-center justify-center text-primary-600 mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section id="genres" className="py-20 bg-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Explore by Genre
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Find your next story in any genre. Click to start writing.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {GENRES.map((genre) => (
              <motion.button
                key={genre.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleGenreClick(genre.id)}
                className="relative group overflow-hidden rounded-2xl p-6 text-left transition-all hover:shadow-md"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${genre.color} opacity-10 group-hover:opacity-15 transition-opacity`} />
                <div className="relative text-center">
                  <span className="text-4xl mb-2 block">{genre.icon}</span>
                  <h3 className="text-lg font-semibold text-gray-900">{genre.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">{genre.description}</p>
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </section>

      <section id="examples" className="py-20 bg-gray-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Stories You Can Create
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Real examples of interactive narratives from our platform.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {STORY_EXAMPLES.map((example, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-xl p-6 shadow-md border border-gray-100"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{example.title}</h3>
                  <span className="text-xs px-2 py-1 bg-primary-50 text-primary-600 rounded-full">
                    {example.genre}
                  </span>
                </div>
                <div className="space-y-2 text-sm text-gray-500">
                  <div className="flex items-center">
                    <Compass className="w-4 h-4 mr-2 text-gray-400" />
                    <span>{example.choices}</span>
                  </div>
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-2 text-gray-400" />
                    <span>{example.readTime} average read</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="py-20 bg-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Start in Three Steps
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-3xl mx-auto">
            {[
              { step: '1', title: 'Create Account', desc: 'Free signup, no credit card' },
              { step: '2', title: 'Choose Genre', desc: 'Pick what you want to write' },
              { step: '3', title: 'Start Writing', desc: 'Use AI or write manually' }
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.2 }}
                className="text-center"
              >
                <div className="w-12 h-12 bg-gradient-to-r from-primary-600 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-gray-500 text-sm">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-r from-primary-600 to-purple-600">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="max-w-3xl mx-auto"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Your Story Awaits
            </h2>
            <p className="text-xl text-white/90 mb-8">
              Join writers creating interactive narratives today.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center px-8 py-4 bg-white text-primary-600 rounded-xl font-semibold hover:bg-gray-100 transition-all transform hover:scale-105 shadow-xl"
            >
              Create Free Account
              <ChevronRight className="w-5 h-5 ml-2" />
            </Link>
          </motion.div>
        </div>
      </section>

      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-6 md:mb-0">
              <span className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-purple-400 bg-clip-text text-transparent">
                SagaGo
              </span>
              <p className="text-sm mt-2 max-w-md">
                Create interactive stories with branching narratives. 
                Where every choice matters.
              </p>
            </div>
            
            <div className="flex space-x-6">
              <button onClick={() => scrollToSection('features')} className="hover:text-white transition-colors text-sm">Features</button>
              <button onClick={() => scrollToSection('genres')} className="hover:text-white transition-colors text-sm">Genres</button>
              <button onClick={() => scrollToSection('how-it-works')} className="hover:text-white transition-colors text-sm">How It Works</button>
              <button onClick={() => scrollToSection('examples')} className="hover:text-white transition-colors text-sm">Examples</button>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
            <p>&copy; {new Date().getFullYear()} SagaGo. Built for storytellers.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Landing