import request from '@/utils/request'

export interface UserStats {
  total_learned: number
  total_favorites: number
  study_time: number
  streak_days: number
  level: number
  exp: number
  next_level_exp: number
}

export interface LearningProgress {
  daily_study_time: Array<{ date: string; duration: number }>
  dynasty_distribution: Array<{ dynasty: string; count: number }>
  genre_distribution: Array<{ genre: string; count: number }>
  cumulative_learned: Array<{ date: string; total: number }>
  challenge_performance: {
    beauty_avg: number
    creativity_avg: number
    mood_avg: number
  }
  study_calendar: Array<{ date: string; activity: number }>
}

export const learningApi = {
  recordLearning(data: {
    poem_id: number
    action: string
    duration?: number
  }) {
    return request.post('/learning/record', data)
  },

  getStats() {
    return request.get<UserStats>('/learning/stats')
  },

  getProgress() {
    return request.get<LearningProgress>('/learning/progress')
  }
}
