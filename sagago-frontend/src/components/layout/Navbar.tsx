import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { useMessageStore } from '../../stores/messageStore'
import { 
  LogOut, 
  Home, 
  Compass,
  Bell,
  PenTool,
  Sparkles,
  User,
  Menu,
  X,
  Wand2,
  Search,
  Bookmark,
  BarChart3,
  MessageCircle,
  Layout,
  ChevronDown,
  Feather,
  Zap,
  Star
} from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import NotificationBell from '../notifications/NotificationBell'

const Navbar = () => {
  const { user, logout } = useAuthStore()
  const { unreadCount, fetchUnreadCount } = useMessageStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isCreateDropdownOpen, setIsCreateDropdownOpen] = useState(false)
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false)
  const createDropdownRef = useRef<HTMLDivElement>(null)
  const profileDropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (user) {
      fetchUnreadCount()
      const interval = setInterval(fetchUnreadCount, 30000)
      return () => clearInterval(interval)
    }
  }, [user])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (createDropdownRef.current && !createDropdownRef.current.contains(event.target as Node)) {
        setIsCreateDropdownOpen(false)
      }
      if (profileDropdownRef.current && !profileDropdownRef.current.contains(event.target as Node)) {
        setIsProfileDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    setIsMobileMenuOpen(false)
    setIsCreateDropdownOpen(false)
    setIsProfileDropdownOpen(false)
  }, [location])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path: string) => {
    return location.pathname === path
  }

  const NavLink = ({ to, icon: Icon, label, badge }: { to: string; icon: any; label: string; badge?: number }) => (
    <Link
      to={to}
      className={`relative flex items-center space-x-2 px-3 py-2 rounded-xl transition-all ${
        isActive(to)
          ? 'bg-primary-50 text-primary-600'
          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
      }`}
    >
      <Icon className="w-5 h-5" />
      <span className="text-sm font-medium hidden lg:inline">{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
          {badge > 9 ? '9+' : badge}
        </span>
      )}
    </Link>
  )

  return (
    <nav className="bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 lg:h-20">
          {/* Logo */}
          <Link 
            to="/" 
            className="flex items-center space-x-2 group"
          >
            <div className="w-8 h-8 lg:w-10 lg:h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all">
              <Feather className="w-4 h-4 lg:w-5 lg:h-5 text-white" />
            </div>
            <span className="text-xl lg:text-2xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
              SagaGo
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center space-x-1">
            {/* Main Navigation */}
            <div className="flex items-center space-x-1 mr-4">
              <NavLink to="/" icon={Home} label="Home" />
              <NavLink to="/explore" icon={Compass} label="Explore" />
              <NavLink to="/templates" icon={Layout} label="Templates" />
            </div>

            {/* Create Dropdown */}
            <div className="relative mr-4" ref={createDropdownRef}>
              <button
                onClick={() => setIsCreateDropdownOpen(!isCreateDropdownOpen)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all ${
                  isCreateDropdownOpen || isActive('/create') || isActive('/assisted') || isActive('/write')
                    ? 'bg-primary-600 text-white shadow-md'
                    : 'bg-primary-50 text-primary-600 hover:bg-primary-100'
                }`}
              >
                <PenTool className="w-4 h-4" />
                <span className="text-sm font-medium">Create</span>
                <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isCreateDropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {isCreateDropdownOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden animate-fadeIn">
                  <div className="p-2">
                    <Link
                      to="/create"
                      className="flex items-center space-x-3 px-4 py-3 hover:bg-purple-50 rounded-xl transition-colors group"
                      onClick={() => setIsCreateDropdownOpen(false)}
                    >
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                        <Sparkles className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">AI Interactive</p>
                        <p className="text-xs text-gray-500">Branching adventure game</p>
                      </div>
                    </Link>
                    <Link
                      to="/assisted"
                      className="flex items-center space-x-3 px-4 py-3 hover:bg-indigo-50 rounded-xl transition-colors group"
                      onClick={() => setIsCreateDropdownOpen(false)}
                    >
                      <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                        <Wand2 className="w-5 h-5 text-indigo-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">AI Assisted</p>
                        <p className="text-xs text-gray-500">Full paragraph stories</p>
                      </div>
                    </Link>
                    <Link
                      to="/write"
                      className="flex items-center space-x-3 px-4 py-3 hover:bg-blue-50 rounded-xl transition-colors group"
                      onClick={() => setIsCreateDropdownOpen(false)}
                    >
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                        <PenTool className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">Write Your Own</p>
                        <p className="text-xs text-gray-500">Share your creativity</p>
                      </div>
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Right Icons */}
            <div className="flex items-center space-x-1">
              <Link
                to="/search/users"
                className={`p-2 rounded-xl transition-all ${
                  isActive('/search/users') ? 'bg-primary-50 text-primary-600' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
                title="Search Users"
              >
                <Search className="w-5 h-5" />
              </Link>

              <Link
                to="/messages"
                className={`p-2 rounded-xl transition-all relative ${
                  isActive('/messages') ? 'bg-primary-50 text-primary-600' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
                title="Messages"
              >
                <MessageCircle className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </Link>

              <Link
                to="/reading-list"
                className={`p-2 rounded-xl transition-all ${
                  isActive('/reading-list') ? 'bg-primary-50 text-primary-600' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
                title="Reading List"
              >
                <Bookmark className="w-5 h-5" />
              </Link>

              <Link
                to="/analytics"
                className={`p-2 rounded-xl transition-all ${
                  isActive('/analytics') ? 'bg-primary-50 text-primary-600' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
                title="Analytics"
              >
                <BarChart3 className="w-5 h-5" />
              </Link>

              <NotificationBell />

              {/* Profile Dropdown */}
              <div className="relative" ref={profileDropdownRef}>
                <button
                  onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                  className={`flex items-center space-x-2 p-1.5 rounded-xl transition-all ${
                    isProfileDropdownOpen || isActive(`/profile/${user?.username}`)
                      ? 'bg-primary-50'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  {user?.avatar_url ? (
                    <img src={user.avatar_url} alt={user.username} className="w-8 h-8 rounded-lg object-cover" />
                  ) : (
                    <div className="w-8 h-8 bg-gradient-to-br from-primary-100 to-purple-100 rounded-lg flex items-center justify-center">
                      <span className="text-sm font-bold text-primary-600">
                        {user?.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                  <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${isProfileDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {isProfileDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden animate-fadeIn">
                    <div className="p-2">
                      <Link
                        to={`/profile/${user?.username}`}
                        className="flex items-center space-x-3 px-4 py-3 hover:bg-gray-50 rounded-xl transition-colors"
                        onClick={() => setIsProfileDropdownOpen(false)}
                      >
                        <User className="w-5 h-5 text-gray-500" />
                        <span className="text-sm text-gray-700">Your Profile</span>
                      </Link>
                      <Link
                        to="/notifications"
                        className="flex items-center space-x-3 px-4 py-3 hover:bg-gray-50 rounded-xl transition-colors"
                        onClick={() => setIsProfileDropdownOpen(false)}
                      >
                        <Bell className="w-5 h-5 text-gray-500" />
                        <span className="text-sm text-gray-700">Notifications</span>
                      </Link>
                      <div className="border-t border-gray-100 my-2"></div>
                      <button
                        onClick={handleLogout}
                        className="flex items-center space-x-3 px-4 py-3 w-full text-left hover:bg-red-50 rounded-xl transition-colors group"
                      >
                        <LogOut className="w-5 h-5 text-gray-500 group-hover:text-red-500" />
                        <span className="text-sm text-gray-700 group-hover:text-red-500">Logout</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden p-2 hover:bg-gray-100 rounded-xl transition-colors"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6 text-gray-600" />
            ) : (
              <Menu className="w-6 h-6 text-gray-600" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="lg:hidden py-4 border-t border-gray-100 animate-slideDown">
            <div className="space-y-4">
              {/* Create Section */}
              <div className="px-2">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-3">Create</p>
                <div className="space-y-1">
                  <Link
                    to="/create"
                    className="flex items-center space-x-3 px-4 py-3 bg-purple-50 text-purple-700 rounded-xl hover:bg-purple-100 transition-colors"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Sparkles className="w-5 h-5" />
                    <div>
                      <p className="font-medium">AI Interactive</p>
                      <p className="text-xs text-purple-600">Branching adventure</p>
                    </div>
                  </Link>
                  <Link
                    to="/assisted"
                    className="flex items-center space-x-3 px-4 py-3 bg-indigo-50 text-indigo-700 rounded-xl hover:bg-indigo-100 transition-colors"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Wand2 className="w-5 h-5" />
                    <div>
                      <p className="font-medium">AI Assisted</p>
                      <p className="text-xs text-indigo-600">Full paragraphs</p>
                    </div>
                  </Link>
                  <Link
                    to="/write"
                    className="flex items-center space-x-3 px-4 py-3 bg-blue-50 text-blue-700 rounded-xl hover:bg-blue-100 transition-colors"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <PenTool className="w-5 h-5" />
                    <div>
                      <p className="font-medium">Write Your Own</p>
                      <p className="text-xs text-blue-600">Share creativity</p>
                    </div>
                  </Link>
                </div>
              </div>

              {/* Navigation Links */}
              <div className="px-2">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-3">Menu</p>
                <div className="space-y-1">
                  <Link
                    to="/"
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
                      isActive('/') ? 'bg-primary-50 text-primary-600' : 'text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Home className="w-5 h-5" />
                    <span>Home</span>
                  </Link>
                  <Link
                    to="/explore"
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
                      isActive('/explore') ? 'bg-primary-50 text-primary-600' : 'text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Compass className="w-5 h-5" />
                    <span>Explore</span>
                  </Link>
                  <Link
                    to="/templates"
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
                      isActive('/templates') ? 'bg-primary-50 text-primary-600' : 'text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Layout className="w-5 h-5" />
                    <span>Templates</span>
                  </Link>
                  <Link
                    to="/search/users"
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
                      isActive('/search/users') ? 'bg-primary-50 text-primary-600' : 'text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Search className="w-5 h-5" />
                    <span>Search Users</span>
                  </Link>
                  <Link
                    to="/messages"
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors relative ${
                      isActive('/messages') ? 'bg-primary-50 text-primary-600' : 'text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <MessageCircle className="w-5 h-5" />
                    <span>Messages</span>
                    {unreadCount > 0 && (
                      <span className="ml-auto bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </Link>
                  <Link
                    to="/reading-list"
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
                      isActive('/reading-list') ? 'bg-primary-50 text-primary-600' : 'text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Bookmark className="w-5 h-5" />
                    <span>Reading List</span>
                  </Link>
                  <Link
                    to="/analytics"
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
                      isActive('/analytics') ? 'bg-primary-50 text-primary-600' : 'text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <BarChart3 className="w-5 h-5" />
                    <span>Analytics</span>
                  </Link>
                  <Link
                    to={`/profile/${user?.username}`}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
                      isActive(`/profile/${user?.username}`) ? 'bg-primary-50 text-primary-600' : 'text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt={user.username} className="w-5 h-5 rounded-full" />
                    ) : (
                      <div className="w-5 h-5 bg-primary-100 rounded-full flex items-center justify-center">
                        <span className="text-primary-600 text-xs font-semibold">
                          {user?.username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                    <span>Profile</span>
                  </Link>
                </div>
              </div>

              {/* Logout Button */}
              <div className="px-2 pt-2">
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-3 px-4 py-3 w-full text-red-600 bg-red-50 hover:bg-red-100 rounded-xl transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

export default Navbar