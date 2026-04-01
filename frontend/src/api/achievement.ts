import request from '@/utils/request'

export interface AchievementInfo {
  id: number
  code: string
  name: string
  description: string
  icon: string
  rarity: string
  condition_type: string
  condition_value: number
  exp_reward: number
  points_reward: number
}

export interface AchievementCategory {
  category: string
  category_name: string
  achievements: AchievementInfo[]
}

export interface UserAchievementItem {
  id: number
  code: string
  name: string
  description: string
  icon: string
  rarity: string
  category: string
  exp_reward: number
  points_reward: number
  unlocked_at: string
}

export interface AchievementProgressItem {
  achievement_id: number
  code: string
  name: string
  description: string
  icon: string
  rarity: string
  category: string
  condition_type: string
  exp_reward: number
  points_reward: number
  current_value: number
  target_value: number
  percentage: number
  is_unlocked: boolean
}

export interface AchievementMineResponse {
  unlocked: UserAchievementItem[]
  newly_unlocked: UserAchievementItem[]
  total_unlocked: number
  total_achievements: number
  completion_rate: number
  current_level: number
  current_exp: number
  next_level_exp: number | null
  total_exp_rewarded: number
  total_points_rewarded: number
}

export interface AchievementProgressResponse {
  progress: AchievementProgressItem[]
  newly_unlocked: UserAchievementItem[]
}

export const achievementApi = {
  async getAllAchievements(): Promise<{ categories: AchievementCategory[] }> {
    const res: any = await request.get('/achievements')
    return res.data || res
  },

  async getMyAchievements(): Promise<AchievementMineResponse> {
    const res: any = await request.get('/achievements/mine')
    return res.data || res
  },

  async getProgress(): Promise<AchievementProgressResponse> {
    const res: any = await request.get('/achievements/progress')
    return res.data || res
  }
}
