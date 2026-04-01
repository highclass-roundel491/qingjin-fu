import request from '@/utils/request'

export interface QuestionOption {
  key: string
  text: string
}

export interface TimedQuestion {
  index: number
  question_type: string
  question_text: string
  options: QuestionOption[]
  hint?: string
  poem_dynasty?: string
  time_limit: number
}

export interface TimedStartResponse {
  session_id: number
  difficulty: string
  total_questions: number
  time_per_question: number
  first_question: TimedQuestion
}

export interface TimedAnswerResponse {
  is_correct: boolean
  correct_answer: string
  score_gained: number
  combo: number
  total_score: number
  correct_count: number
  answered_count: number
  poem_title?: string
  poem_author?: string
  poem_content?: string
  next_question?: TimedQuestion
  is_finished: boolean
}

export interface TimedAnswerDetail {
  index: number
  question_type: string
  question_text: string
  correct_answer: string
  user_answer?: string
  is_correct: boolean
  score: number
  time_spent: number
}

export interface TimedChallengeResult {
  session_id: number
  difficulty: string
  total_questions: number
  answered_count: number
  correct_count: number
  accuracy: number
  total_score: number
  max_combo: number
  exp_gained: number
  duration: number
  answers: TimedAnswerDetail[]
}

export interface TimedHistoryItem {
  id: number
  difficulty: string
  total_questions: number
  correct_count: number
  accuracy: number
  total_score: number
  max_combo: number
  exp_gained: number
  started_at: string
  duration: number
}

export interface TimedHistoryResponse {
  items: TimedHistoryItem[]
  total: number
  page: number
  page_size: number
  best_score: number
  best_accuracy: number
  total_games: number
}

export interface TimedRankingItem {
  rank: number
  user_id: number
  username: string
  nickname?: string
  avatar_url?: string
  total_score: number
  best_score: number
  total_games: number
  best_accuracy: number
  level: number
  exp: number
}

export interface TimedRankingResponse {
  items: TimedRankingItem[]
  total: number
  period: string
}

export const timedChallengeApi = {
  start(data: { difficulty?: string; question_count?: number; question_type?: string }): Promise<TimedStartResponse> {
    return request.post('/timed-challenge/start', data)
  },

  answer(data: { session_id: number; question_index: number; answer: string; time_spent: number }): Promise<TimedAnswerResponse> {
    return request.post('/timed-challenge/answer', data)
  },

  end(session_id: number): Promise<TimedChallengeResult> {
    return request.post('/timed-challenge/end', { session_id })
  },

  getHistory(params: { page?: number; page_size?: number } = {}): Promise<TimedHistoryResponse> {
    return request.get('/timed-challenge/history', { params })
  },

  getRankings(params: { period?: string; page?: number; page_size?: number } = {}): Promise<TimedRankingResponse> {
    return request.get('/timed-challenge/rankings', { params })
  },
}
