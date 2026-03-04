import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { messagesApi, type Conversation, type Message } from '../api/messages'
import { usersApi } from '../api/users'
import BackButton from '../components/ui/BackButton'
import {
  Loader,
  Send,
  User,
  MoreVertical,
  Check,
  CheckCheck,
  Info,
  ArrowLeft,
  PlusCircle,
  Search,
  X
} from 'lucide-react'
import { toast } from 'react-toastify'
import { format } from 'date-fns'

const Messages = () => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const queryParams = new URLSearchParams(location.search)
  const startUserId = queryParams.get('start')
  
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [showMobileList, setShowMobileList] = useState(true)
  const [showNewMessageModal, setShowNewMessageModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchConversations()
    const interval = setInterval(fetchUnreadCounts, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (startUserId) {
      startConversation(parseInt(startUserId))
    }
  }, [startUserId])

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(1, true)
    }
  }, [selectedConversation])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const fetchConversations = async () => {
    try {
      const data = await messagesApi.getConversations()
      setConversations(data)
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchUnreadCounts = async () => {
    try {
      const data = await messagesApi.getUnreadCount()
      setConversations(prev => prev.map(conv => {
        const unreadData = data.conversations.find(c => c.user_id === conv.user_id)
        return {
          ...conv,
          unread_count: unreadData?.unread_count || 0
        }
      }))
    } catch (error) {
      console.error('Failed to fetch unread counts:', error)
    }
  }

  const fetchMessages = async (pageNum: number, reset: boolean = false) => {
    if (!selectedConversation) return
    
    if (reset) {
      setLoadingMore(false)
    } else {
      setLoadingMore(true)
    }
    
    try {
      const data = await messagesApi.getConversation(selectedConversation.user_id, pageNum)
      
      if (reset) {
        setMessages(data.messages)
        setPage(data.page)
        setHasMore(data.page < data.pages)
      } else {
        setMessages(prev => [...data.messages, ...prev])
        setPage(data.page)
        setHasMore(data.page < data.pages)
      }
      
      if (reset) {
        await messagesApi.markConversationRead(selectedConversation.user_id)
        setConversations(prev => prev.map(conv => 
          conv.user_id === selectedConversation.user_id 
            ? { ...conv, unread_count: 0 }
            : conv
        ))
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    } finally {
      setLoadingMore(false)
    }
  }

  const startConversation = async (userId: number) => {
    try {
      const existingConv = conversations.find(c => c.user_id === userId)
      if (existingConv) {
        setSelectedConversation(existingConv)
        setShowMobileList(false)
      } else {
        const userData = await usersApi.getUserByUsername(
          (await usersApi.getUserById(userId)).username
        )
        const newConv: Conversation = {
          id: Date.now(),
          user_id: userId,
          username: userData.username,
          avatar_url: userData.avatar_url,
          last_message: '',
          last_message_at: new Date().toISOString(),
          unread_count: 0,
          is_online: false
        }
        setSelectedConversation(newConv)
        setShowMobileList(false)
      }
      setShowNewMessageModal(false)
    } catch (error) {
      toast.error('Failed to start conversation')
    }
  }

  const handleSendMessage = async () => {
    if (!selectedConversation || !newMessage.trim()) return
    
    setIsSending(true)
    try {
      const message = await messagesApi.sendMessage(
        selectedConversation.user_id,
        newMessage.trim()
      )
      
      setMessages(prev => [...prev, message])
      setNewMessage('')
      scrollToBottom()
      
      setConversations(prev => {
        const exists = prev.some(c => c.user_id === selectedConversation.user_id)
        if (exists) {
          return prev.map(conv => 
            conv.user_id === selectedConversation.user_id
              ? { ...conv, last_message: message.content, last_message_at: message.created_at }
              : conv
          )
        } else {
          const newConv: Conversation = {
            id: Date.now(),
            user_id: selectedConversation.user_id,
            username: selectedConversation.username,
            avatar_url: selectedConversation.avatar_url,
            last_message: message.content,
            last_message_at: message.created_at,
            unread_count: 0,
            is_online: selectedConversation.is_online
          }
          return [newConv, ...prev]
        }
      })
    } catch (error) {
      toast.error('Failed to send message')
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleScroll = () => {
    if (!messagesContainerRef.current || loadingMore || !hasMore) return
    
    const { scrollTop } = messagesContainerRef.current
    if (scrollTop < 100) {
      fetchMessages(page + 1)
    }
  }

  const handleSearch = async (query: string) => {
    setSearchQuery(query)
    if (query.length < 2) {
      setSearchResults([])
      return
    }
    
    setSearching(true)
    try {
      const results = await usersApi.searchUsers(query)
      setSearchResults(results.filter((u: any) => u.id !== user?.id))
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setSearching(false)
    }
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 24) {
      return format(date, 'h:mm a')
    } else if (diffInHours < 48) {
      return 'Yesterday'
    } else {
      return format(date, 'MMM d')
    }
  }

  const getMessageStatus = (message: Message, index: number) => {
    if (message.sender_id !== user?.id) return null
    
    const nextMessage = messages[index + 1]
    if (nextMessage?.sender_id === user?.id) return null
    
    if (message.is_read) {
      return <CheckCheck className="w-4 h-4 text-blue-500" />
    }
    return <Check className="w-4 h-4 text-gray-400" />
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-4rem)] max-w-7xl mx-auto">
      {/* New Message Modal */}
      {showNewMessageModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowNewMessageModal(false)} />
          <div className="relative bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">New Message</h3>
              <button
                onClick={() => setShowNewMessageModal(false)}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Search users..."
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                autoFocus
              />
            </div>
            
            <div className="max-h-96 overflow-y-auto">
              {searching && (
                <div className="flex justify-center py-4">
                  <Loader className="w-5 h-5 text-primary-600 animate-spin" />
                </div>
              )}
              
              {searchResults.map((result) => (
                <div
                  key={result.id}
                  onClick={() => startConversation(result.id)}
                  className="flex items-center space-x-3 p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
                >
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    {result.avatar_url ? (
                      <img
                        src={result.avatar_url}
                        alt={result.username}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <span className="text-lg font-bold text-primary-600">
                        {result.username.charAt(0).toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{result.full_name || result.username}</p>
                    <p className="text-sm text-gray-500">@{result.username}</p>
                  </div>
                </div>
              ))}
              
              {searchQuery.length >= 2 && searchResults.length === 0 && !searching && (
                <p className="text-center text-gray-500 py-4">No users found</p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="flex h-full bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Conversations List */}
        <div className={`${showMobileList ? 'flex' : 'hidden'} md:flex w-full md:w-80 border-r border-gray-200 flex-col`}>
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">Messages</h2>
              <button
                onClick={() => setShowNewMessageModal(true)}
                className="p-2 text-primary-600 hover:bg-primary-50 rounded-full transition-colors"
                title="New Message"
              >
                <PlusCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <button
                onClick={() => messagesApi.markAllRead()}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Mark all read
              </button>
              <BackButton />
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {conversations.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <p className="mb-4">No conversations yet</p>
                <button
                  onClick={() => setShowNewMessageModal(true)}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  Start a conversation
                </button>
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => {
                    setSelectedConversation(conv)
                    setShowMobileList(false)
                  }}
                  className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${
                    selectedConversation?.user_id === conv.user_id ? 'bg-primary-50' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className="relative">
                      <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                        {conv.avatar_url ? (
                          <img
                            src={conv.avatar_url}
                            alt={conv.username}
                            className="w-12 h-12 rounded-full object-cover"
                          />
                        ) : (
                          <span className="text-lg font-bold text-primary-600">
                            {conv.username.charAt(0).toUpperCase()}
                          </span>
                        )}
                      </div>
                      {/* Online status indicator removed */}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900 truncate">
                          {conv.username}
                        </h3>
                        <span className="text-xs text-gray-500">
                          {formatTime(conv.last_message_at)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 truncate">{conv.last_message}</p>
                    </div>
                    
                    {conv.unread_count > 0 && (
                      <div className="w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center">
                        <span className="text-xs text-white">{conv.unread_count}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className={`${!showMobileList ? 'flex' : 'hidden'} md:flex flex-1 flex-col`}>
          {selectedConversation ? (
            <>
              {/* Chat Header */}
              <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setShowMobileList(true)}
                    className="md:hidden p-2 hover:bg-gray-100 rounded-full"
                  >
                    <ArrowLeft className="w-5 h-5" />
                  </button>
                  
                  <div className="relative">
                    <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                      {selectedConversation.avatar_url ? (
                        <img
                          src={selectedConversation.avatar_url}
                          alt={selectedConversation.username}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <span className="text-lg font-bold text-primary-600">
                          {selectedConversation.username.charAt(0).toUpperCase()}
                        </span>
                      )}
                    </div>
                    {/* Online status indicator removed */}
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {selectedConversation.username}
                    </h3>
                    {/* Online/Offline text removed */}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {/* Phone and Video buttons removed */}
                  <button className="p-2 hover:bg-gray-100 rounded-full">
                    <Info className="w-5 h-5 text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div
                ref={messagesContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto p-4 space-y-4"
              >
                {loadingMore && (
                  <div className="flex justify-center">
                    <Loader className="w-5 h-5 text-primary-600 animate-spin" />
                  </div>
                )}
                
                {messages.map((msg, index) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.sender_id === user?.id ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className="flex items-end space-x-2 max-w-[70%]">
                      {msg.sender_id !== user?.id && (
                        <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-xs font-bold text-primary-600">
                            {msg.sender_username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      )}
                      
                      <div
                        className={`rounded-2xl px-4 py-2 ${
                          msg.sender_id === user?.id
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                        <div className={`flex items-center justify-end space-x-1 mt-1 text-xs ${
                          msg.sender_id === user?.id ? 'text-primary-200' : 'text-gray-500'
                        }`}>
                          <span>{format(new Date(msg.created_at), 'h:mm a')}</span>
                          {getMessageStatus(msg, index)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input */}
              <div className="p-4 border-t border-gray-200">
                <div className="flex items-end space-x-2">
                  <textarea
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Type a message..."
                    rows={1}
                    className="flex-1 px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                    style={{ minHeight: '44px', maxHeight: '120px' }}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!newMessage.trim() || isSending}
                    className="p-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <User className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="mb-4">Select a conversation to start messaging</p>
                <button
                  onClick={() => setShowNewMessageModal(true)}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  Start a new conversation
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Messages