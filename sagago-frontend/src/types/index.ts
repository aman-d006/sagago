export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  avatar_url?: string
  bio?: string
  followers_count: number
  following_count: number
  stories_count: number
  created_at: string
}

export interface StoryNode {
  id: number
  content: string
  is_ending: boolean
  is_winning_ending: boolean
  options: StoryOption[]
}

export interface StoryOption {
  text: string
  node_id: number
}

export interface StoryAuthor {
  id: number
  username: string
  full_name?: string
  avatar_url?: string
}

export interface Story {
  id: number
  title: string
  content?: string
  excerpt: string
  cover_image?: string
  created_at: string
  updated_at?: string
  author: StoryAuthor
  like_count: number
  comment_count: number
  view_count: number
  is_liked_by_current_user: boolean
  is_published: boolean
  story_type: 'interactive' | 'written'
  reading_time?: number
  tags?: string[]
  chapters?: Chapter[]
  root_node?: StoryNode
  all_nodes?: Record<number, StoryNode>
  genre?: string
}

export interface Chapter {
  id: number
  title: string
  content: string
  chapter_number: number
  created_at: string
}

export interface Comment {
  id: number
  content: string
  username: string
  user_avatar?: string
  like_count: number
  reply_count: number
  created_at: string
  is_liked_by_current_user: boolean
}

export interface Notification {
  id: number
  notification_type: string
  actor_username: string
  actor_avatar?: string
  story_title?: string
  story_id?: number
  content?: string
  is_read: boolean
  created_at: string
}

export interface FeedResponse {
  stories: Story[]
  total: number
  page: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export interface JobResponse {
  job_id: string
  status: string
  created_at: string
  story_id?: number
  error?: string
  completed_at?: string
}

export interface CreateStoryData {
  title: string
  content: string
  excerpt?: string
  cover_image?: string
  story_type: 'interactive' | 'written'
  tags?: string[]
  is_published?: boolean
}

export interface PublishStoryData {
  title: string
  content: string
  excerpt?: string
  cover_image?: string
  tags?: string[]
}