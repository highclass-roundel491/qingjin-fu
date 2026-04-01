import request from '@/utils/request'
import type { PoemListResponse } from '@/api/poem'

export interface UserInfo {
  id: number
  username: string
  email: string
  phone?: string
  nickname?: string
  avatar_url?: string
  bio?: string
  level: number
  exp: number
  points: number
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserInfoResponse {
  code: number
  message: string
  data: UserInfo
}

export interface RegisterResponse {
  code: number
  message: string
  data: {
    user_id: number
    username: string
    email: string
  }
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  phone?: string
}

export interface UpdateProfileRequest {
  nickname?: string | null
  avatar_url?: string | null
  bio?: string | null
  email?: string | null
  phone?: string | null
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export interface UserProfileStats {
  total_study_time: number
  total_poems_learned: number
  total_questions_answered: number
  correct_rate: number
  total_works_created: number
  total_likes_received: number
  follower_count: number
  following_count: number
}

export interface UserExpHistoryItem {
  id: string
  source: string
  source_label: string
  title: string
  detail: string
  exp: number
  occurred_at: string
}

export interface UserExpHistoryResponse {
  items: UserExpHistoryItem[]
  total: number
  page: number
  page_size: number
}

export const userApi = {
  async getCurrentUser(): Promise<UserInfo> {
    const res: any = await request.get('/users/me')
    return res.data
  },

  async login(data: LoginRequest): Promise<LoginResponse> {
    const res: any = await request.post('/users/login', data)
    return res.data
  },

  async register(data: RegisterRequest): Promise<any> {
    const res: any = await request.post('/users/register', data)
    return res.data
  },

  async updateProfile(data: UpdateProfileRequest): Promise<UserInfo> {
    const res: any = await request.put('/users/me', data)
    return res.data
  },

  async changePassword(data: ChangePasswordRequest): Promise<void> {
    await request.post('/users/change-password', data)
  },

  async uploadAvatar(file: File): Promise<{ avatar_url: string }> {
    const formData = new FormData()
    formData.append('file', file)
    const res: any = await request.post('/users/me/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data
  },

  async getFavorites(params: { page?: number; page_size?: number } = {}): Promise<PoemListResponse> {
    const res: any = await request.get('/users/me/favorites', { params })
    return res.data
  },

  async getExpHistory(params: { page?: number; page_size?: number } = {}): Promise<UserExpHistoryResponse> {
    const res: any = await request.get('/users/me/exp-history', { params })
    return res.data
  },

  async getUserStats(userId: number): Promise<UserProfileStats> {
    const res: any = await request.get(`/users/${userId}/stats`)
    return res.data
  }
}
