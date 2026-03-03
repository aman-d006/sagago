import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { templatesApi, type Template, type WritingPrompt } from '../api/templates'
import { storiesApi } from '../api/stories'
import BackButton from '../components/ui/BackButton'
import {
  Loader,
  Search,
  Filter,
  Star,
  TrendingUp,
  Clock,
  BookOpen,
  Sparkles,
  ChevronRight,
  X,
  Heart,
  Eye,
  MessageCircle,
  Calendar,
  Wand2,
  Gamepad2,
  FileText
} from 'lucide-react'
import { toast } from 'react-toastify'

const Templates = () => {
  const navigate = useNavigate()
  const [templates, setTemplates] = useState<Template[]>([])
  const [favorites, setFavorites] = useState<Template[]>([])
  const [dailyPrompt, setDailyPrompt] = useState<WritingPrompt | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedGenre, setSelectedGenre] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'popular' | 'newest' | 'title'>('popular')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [showTypeModal, setShowTypeModal] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [selectedPrompt, setSelectedPrompt] = useState<WritingPrompt | null>(null)
  const [customTitle, setCustomTitle] = useState('')
  const [usingTemplate, setUsingTemplate] = useState(false)
  const [showFavorites, setShowFavorites] = useState(false)
  const [modalMode, setModalMode] = useState<'template' | 'prompt'>('prompt')

  const genres = ['all', 'fantasy', 'sci-fi', 'romance', 'horror', 'mystery', 'adventure']

  useEffect(() => {
    Promise.all([
      fetchTemplates(true),
      fetchDailyPrompt(),
      fetchFavorites()
    ]).catch(error => {
      console.error('Failed to load initial data:', error)
    })
  }, [])

  useEffect(() => {
    fetchTemplates(true)
  }, [selectedGenre, sortBy, searchQuery])

  const fetchTemplates = async (reset: boolean = false) => {
    if (reset) {
      setIsLoading(true)
      setPage(1)
    } else {
      setLoadingMore(true)
    }

    try {
      const currentPage = reset ? 1 : page + 1
      const response = await templatesApi.getTemplates(
        currentPage,
        selectedGenre !== 'all' ? selectedGenre : undefined,
        searchQuery || undefined,
        sortBy
      )

      if (reset) {
        setTemplates(response.templates)
      } else {
        setTemplates(prev => [...prev, ...response.templates])
      }

      setPage(response.page)
      setHasMore(response.page < response.pages)
    } catch (error) {
      console.error('Failed to load templates:', error)
      toast.error('Failed to load templates')
    } finally {
      setIsLoading(false)
      setLoadingMore(false)
    }
  }

  const fetchFavorites = async () => {
    try {
      const data = await templatesApi.getFavorites()
      setFavorites(data || [])
    } catch (error) {
      console.error('Failed to fetch favorites:', error)
      setFavorites([])
    }
  }

  const fetchDailyPrompt = async () => {
    try {
      const data = await templatesApi.getDailyPrompt()
      setDailyPrompt(data)
    } catch (error) {
      console.error('Failed to fetch daily prompt:', error)
    }
  }

  const handleTemplateClick = (template: Template) => {
    setSelectedTemplate(template)
    setCustomTitle('')
    setModalMode('template')
    setShowTypeModal(true)
  }

  const handlePromptClick = () => {
    if (!dailyPrompt) return
    setSelectedPrompt(dailyPrompt)
    setModalMode('prompt')
    setShowTypeModal(true)
  }

  const handleTypeSelect = async (type: 'assisted' | 'interactive' | 'template') => {
    if (type === 'template' && selectedTemplate) {
      setUsingTemplate(true)
      try {
        const response = await templatesApi.useTemplate(
          selectedTemplate.id,
          customTitle || undefined
        )
        toast.success('Story created from template!')
        setShowTypeModal(false)
        setSelectedTemplate(null)
        setCustomTitle('')
        navigate(`/write?story=${response.story_id}`)
      } catch (error: any) {
        console.error('Failed to use template:', error)
        toast.error(error.response?.data?.detail || 'Failed to create story from template')
      } finally {
        setUsingTemplate(false)
      }
      return
    }

    if (modalMode === 'prompt' && selectedPrompt) {
      if (type === 'assisted') {
        navigate('/assisted', { 
          state: { prompt: selectedPrompt.prompt } 
        })
      } else {
        // Interactive game - pass prompt as theme
        navigate('/create', { 
          state: { theme: selectedPrompt.prompt } 
        })
      }
    }

    if (modalMode === 'template' && selectedTemplate) {
      if (type === 'assisted') {
        navigate('/assisted', { 
          state: { prompt: selectedTemplate.prompt || `Create a story based on ${selectedTemplate.title} template` } 
        })
      } else {
        // Interactive game - create theme from template
        const theme = selectedTemplate.prompt || 
          `Create an interactive ${selectedTemplate.genre || 'adventure'} story based on ${selectedTemplate.title} with ${
            selectedTemplate.content_structure.outline.length} plot points including: ${
            selectedTemplate.content_structure.outline.slice(0, 3).join(', ')}`
        navigate('/create', { 
          state: { theme: theme } 
        })
      }
    }

    setShowTypeModal(false)
  }

  const handleToggleFavorite = async (template: Template, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await templatesApi.toggleFavorite(template.id)
      
      setTemplates(prev => prev.map(t => 
        t.id === template.id ? { ...t, is_favorite: !t.is_favorite } : t
      ))
      
      if (template.is_favorite) {
        setFavorites(prev => prev.filter(t => t.id !== template.id))
        toast.success('Removed from favorites')
      } else {
        setFavorites(prev => [...prev, { ...template, is_favorite: true }])
        toast.success('Added to favorites')
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error)
      toast.error('Failed to update favorite')
    }
  }

  const getGenreColor = (genre?: string) => {
    const colors: Record<string, string> = {
      fantasy: 'from-purple-500 to-indigo-500',
      'sci-fi': 'from-blue-500 to-cyan-500',
      mystery: 'from-gray-700 to-gray-900',
      romance: 'from-pink-500 to-rose-500',
      horror: 'from-red-700 to-red-900',
      adventure: 'from-green-500 to-emerald-500'
    }
    return colors[genre || ''] || 'from-primary-500 to-primary-700'
  }

  const TemplateCard = ({ template }: { template: Template }) => (
    <div
      onClick={() => handleTemplateClick(template)}
      className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all cursor-pointer border border-gray-100 overflow-hidden group"
    >
      {template.cover_image ? (
        <div className="h-32 bg-gray-100 overflow-hidden">
          <img
            src={template.cover_image}
            alt={template.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        </div>
      ) : (
        <div className={`h-32 bg-gradient-to-r ${getGenreColor(template.genre)} flex items-center justify-center`}>
          <BookOpen className="w-8 h-8 text-white opacity-50" />
        </div>
      )}
      
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-gray-900 line-clamp-1 flex-1">{template.title}</h3>
          <button
            onClick={(e) => handleToggleFavorite(template, e)}
            className={`p-1 rounded-full transition-colors ml-2 ${
              template.is_favorite ? 'text-yellow-500' : 'text-gray-300 hover:text-yellow-500'
            }`}
          >
            <Star className={`w-4 h-4 ${template.is_favorite ? 'fill-yellow-500' : ''}`} />
          </button>
        </div>
        
        {template.description && (
          <p className="text-xs text-gray-500 mb-2 line-clamp-2">{template.description}</p>
        )}
        
        <div className="flex items-center justify-between text-xs">
          <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
            {template.genre || 'General'}
          </span>
          <span className="text-gray-400 flex items-center">
            <TrendingUp className="w-3 h-3 mr-1" />
            {template.usage_count} uses
          </span>
        </div>
      </div>
    </div>
  )

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Type Selection Modal */}
      {showTypeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowTypeModal(false)} />
          <div className="relative bg-white rounded-2xl shadow-xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                {modalMode === 'prompt' ? 'Use Daily Prompt' : 'Use Template'}
              </h2>
              <button
                onClick={() => setShowTypeModal(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalMode === 'prompt' && selectedPrompt && (
              <p className="text-gray-600 mb-6">
                How would you like to use this prompt: "{selectedPrompt.prompt.substring(0, 100)}..."
              </p>
            )}

            {modalMode === 'template' && selectedTemplate && (
              <div className="mb-6">
                <p className="text-gray-600 mb-4">
                  Choose how to use the "{selectedTemplate.title}" template:
                </p>
                {selectedTemplate.prompt && (
                  <div className="bg-primary-50 p-3 rounded-lg mb-4">
                    <p className="text-sm text-primary-700">{selectedTemplate.prompt}</p>
                  </div>
                )}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Custom Title (Optional for template story)
                  </label>
                  <input
                    type="text"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    placeholder={`My ${selectedTemplate.title}`}
                    className="input-field"
                  />
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 gap-3">
              <button
                onClick={() => handleTypeSelect('assisted')}
                className="group p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl hover:shadow-md transition-all text-left flex items-center space-x-4"
              >
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <Wand2 className="w-6 h-6 text-purple-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">AI Assisted Story</h3>
                  <p className="text-sm text-gray-500">Generate a full written story with paragraphs</p>
                </div>
              </button>

              <button
                onClick={() => handleTypeSelect('interactive')}
                className="group p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl hover:shadow-md transition-all text-left flex items-center space-x-4"
              >
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Gamepad2 className="w-6 h-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">Interactive Game</h3>
                  <p className="text-sm text-gray-500">Create a branching narrative with choices and multiple endings</p>
                </div>
              </button>

              {modalMode === 'template' && (
                <button
                  onClick={() => handleTypeSelect('template')}
                  disabled={usingTemplate}
                  className="group p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl hover:shadow-md transition-all text-left flex items-center space-x-4"
                >
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <FileText className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">Use Template Structure</h3>
                    <p className="text-sm text-gray-500">Create a story with pre-built outline and character suggestions</p>
                  </div>
                  {usingTemplate && (
                    <Loader className="w-5 h-5 animate-spin text-blue-600" />
                  )}
                </button>
              )}
            </div>

            <button
              onClick={() => setShowTypeModal(false)}
              className="w-full mt-4 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <BackButton />
          <h1 className="text-2xl font-bold text-gray-900">Writing Templates</h1>
        </div>
      </div>

      {/* Daily Writing Prompt */}
      {dailyPrompt && (
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl shadow-lg p-6 text-white mb-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <Sparkles className="w-5 h-5" />
                <h2 className="text-lg font-semibold">Daily Writing Prompt</h2>
              </div>
              <p className="text-white/90 text-lg mb-4">"{dailyPrompt.prompt}"</p>
              <button
                onClick={handlePromptClick}
                className="bg-white/20 hover:bg-white/30 backdrop-blur-sm px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Use this prompt
              </button>
            </div>
            <div className="text-right">
              <span className="text-xs bg-white/20 px-2 py-1 rounded-full">
                {dailyPrompt.difficulty}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setShowFavorites(false)}
          className={`px-4 py-2 font-medium rounded-lg transition-colors ${
            !showFavorites
              ? 'bg-primary-600 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          All Templates
        </button>
        <button
          onClick={() => setShowFavorites(true)}
          className={`px-4 py-2 font-medium rounded-lg transition-colors ${
            showFavorites
              ? 'bg-primary-600 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <Star className="w-4 h-4 inline mr-2" />
          Favorites
        </button>
      </div>

      {!showFavorites ? (
        <>
          {/* Search and Filters */}
          <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search templates..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="relative">
                <select
                  value={selectedGenre}
                  onChange={(e) => setSelectedGenre(e.target.value)}
                  className="appearance-none px-4 py-2 pr-10 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                >
                  {genres.map(genre => (
                    <option key={genre} value={genre}>
                      {genre === 'all' ? 'All Genres' : genre.charAt(0).toUpperCase() + genre.slice(1)}
                    </option>
                  ))}
                </select>
                <Filter className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>

              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="appearance-none px-4 py-2 pr-10 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                >
                  <option value="popular">Most Popular</option>
                  <option value="newest">Newest</option>
                  <option value="title">Title</option>
                </select>
                <ChevronRight className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Templates Grid */}
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader className="w-8 h-8 text-primary-600 animate-spin" />
            </div>
          ) : templates.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
              <p className="text-gray-500">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {templates.map(template => (
                <TemplateCard key={template.id} template={template} />
              ))}
            </div>
          )}

          {hasMore && !isLoading && (
            <div className="flex justify-center mt-6">
              <button
                onClick={() => fetchTemplates(false)}
                disabled={loadingMore}
                className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                {loadingMore ? (
                  <Loader className="w-5 h-5 animate-spin" />
                ) : (
                  'Load More'
                )}
              </button>
            </div>
          )}
        </>
      ) : (
        /* Favorites View */
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Your Favorite Templates</h2>
          
          {favorites.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              You haven't favorited any templates yet
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {favorites.map(template => (
                <TemplateCard key={template.id} template={template} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Templates