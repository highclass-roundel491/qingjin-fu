import request from '@/utils/request'

export interface FollowResponse {
  following_id: number
  following_username: string
  is_mutual: boolean
}

export interface FollowingItem {
  user_id: number
  username: string
  nickname: string | null
  avatar_url: string | null
  bio: string | null
  level: number
  is_mutual: boolean
  followed_at: string
}

export interface FollowerItem {
  user_id: number
  username: string
  nickname: string | null
  avatar_url: string | null
  bio: string | null
  level: number
  is_following: boolean
  followed_at: string
}

export interface UserAchievementBrief {
  id: number
  code: string
  name: string
  description: string
  icon: string
  rarity: string
  unlocked_at: string
}

export interface RecentWorkBrief {
  id: number
  title: string
  genre: string
  like_count: number
  published_at: string | null
}

export interface UserPublicProfile {
  user_id: number
  username: string
  nickname: string | null
  avatar_url: string | null
  bio: string | null
  level: number
  exp: number
  following_count: number
  follower_count: number
  work_count: number
  is_following: boolean
  is_follower: boolean
  achievements: UserAchievementBrief[]
  recent_works: RecentWorkBrief[]
  joined_at: string
}

export interface ActivityFeedItem {
  id: number
  type: string
  user_id: number
  username: string
  avatar_url: string | null
  content: string
  reference_id: number | null
  reference_type: string | null
  created_at: string
}

export const socialApi = {
  async followUser(userId: number): Promise<FollowResponse> {
    const res: any = await request.post(`/social/follow/${userId}`)
    return res.data || res
  },

  async unfollowUser(userId: number): Promise<any> {
    const res: any = await request.delete(`/social/follow/${userId}`)
    return res.data || res
  },

  async getFollowing(params: { user_id?: number; page?: number; page_size?: number } = {}): Promise<{ items: FollowingItem[]; total: number; page: number; page_size: number }> {
    const res: any = await request.get('/social/following', { params })
    return res.data || res
  },

  async getFollowers(params: { user_id?: number; page?: number; page_size?: number } = {}): Promise<{ items: FollowerItem[]; total: number; page: number; page_size: number }> {
    const res: any = await request.get('/social/followers', { params })
    return res.data || res
  },

  async getUserProfile(userId: number): Promise<UserPublicProfile> {
    const res: any = await request.get(`/social/users/${userId}/profile`)
    return res.data || res
  },

  async getFeed(params: { page?: number; page_size?: number } = {}): Promise<{ items: ActivityFeedItem[]; total: number; page: number; page_size: number }> {
    const res: any = await request.get('/social/feed', { params })
    return res.data || res
  }
}
