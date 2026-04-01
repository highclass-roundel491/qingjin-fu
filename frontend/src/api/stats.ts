import request from '@/utils/request'

export interface PlatformStats {
  total_poems: number
  tang_poems: number
  song_poems: number
  total_users: number
}

export const statsApi = {
  getPlatformStats() {
    return request.get<PlatformStats>('/stats/platform')
  }
}
