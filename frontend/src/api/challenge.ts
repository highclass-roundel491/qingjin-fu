import request from '@/utils/request'

export interface DailyChallenge {
  id: number
  challenge_type: string
  creator_id?: number
  creator_name?: string
  is_daily: boolean
  date?: string
  sentence_template: string
  sentence_template_2?: string
  blank_count: number
  theme?: string
  mood?: string
  hint?: string
  original_answer?: string
  original_answer_2?: string
  difficulty: string
  status: string
  response_count: number
  created_at?: string
}

export interface ChallengeListResponse {
  items: DailyChallenge[]
  total: number
  page: number
  page_size: number
}

export interface ChallengeCreateData {
  challenge_type: 'fill_blank' | 'continue_line'
  sentence_template: string
  sentence_template_2?: string
  blank_count?: number
  original_answer?: string
  original_answer_2?: string
  theme?: string
  mood?: string
  hint?: string
  difficulty?: string
}

export interface ChallengeSubmitResponse {
  id: number
  completed_sentence: string
  completed_sentence_2?: string
  exp_gained: number
  points_gained: number
  ai_score: number
  beauty_score: number
  creativity_score: number
  mood_score: number
  ai_feedback?: string
  ai_highlight?: string
  is_original_match: boolean
}

export interface ChallengeResponseItem {
  id: number
  challenge_id: number
  user_id: number
  username?: string
  answer: string
  answer_2?: string
  content?: string
  likes_count: number
  submitted_at: string
}

export interface ChallengeResponseListResponse {
  items: ChallengeResponseItem[]
  total: number
  page: number
  page_size: number
}

export interface ChallengeHistoryItem {
  id: number
  challenge_id: number
  challenge_type?: string
  answer: string
  answer_2?: string
  content?: string
  exp_gained: number
  points_gained: number
  ai_score: number
  beauty_score: number
  creativity_score: number
  mood_score: number
  submitted_at: string
}

export interface ChallengeHistoryResponse {
  items: ChallengeHistoryItem[]
  total: number
  streak_days: number
  page: number
  page_size: number
}

export interface ChallengeDeleteResponse {
  id: number
  exp_deducted: number
  points_deducted: number
  message: string
}

export interface ChallengeRankingItem {
  rank: number
  user_id: number
  username: string
  nickname?: string
  avatar_url?: string
  total_submissions: number
  total_exp: number
  total_points: number
  level: number
  exp: number
}

export interface ChallengeRankingResponse {
  items: ChallengeRankingItem[]
  total: number
  period: string
}

export interface ChallengeAIGenerateRequest {
  difficulty?: string
  theme?: string
  dynasty?: string
}

export interface ChallengeAIGenerateResponse {
  sentence_template: string
  sentence_template_2?: string
  blank_count: number
  original_answer: string
  original_answer_2?: string
  theme?: string
  mood?: string
  hint?: string
  difficulty: string
  poem_title?: string
  poem_author?: string
  poem_dynasty?: string
}

export interface ChallengeAIHintRequest {
  hint_level: number
}

export interface ChallengeAIHintResponse {
  hint_text: string
  hint_level: number
  next_available: boolean
}

export interface ChallengeAIReviewResponse {
  best_answer_index: number
  best_reason: string
  answer_tags: string[]
  overall_review: string
  diversity_note: string
}

export interface ChallengeAICheckRequest {
  sentence_template: string
  sentence_template_2?: string
  user_answer?: string
}

export interface ChallengeAICheckResponse {
  is_valid: boolean
  feedback: string
  suggestions: string[]
}

export interface ChallengeAIExplainRecommendation {
  title: string
  author: string
  reason: string
}

export interface ChallengeAIExplainResponse {
  poem_title: string
  poem_author: string
  poem_dynasty: string
  poem_content: string
  appreciation: string
  word_analysis: string
  comparison: string
  recommendations: ChallengeAIExplainRecommendation[]
}

export const challengeApi = {
  getDaily() {
    return request.get<DailyChallenge>('/challenges/daily')
  },

  getList(params: { challenge_type?: string; page?: number; page_size?: number }) {
    return request.get<ChallengeListResponse>('/challenges/list', { params })
  },

  getDetail(id: number) {
    return request.get<DailyChallenge>(`/challenges/${id}`)
  },

  create(data: ChallengeCreateData) {
    return request.post<DailyChallenge>('/challenges/create', data)
  },

  submit(data: { challenge_id: number; answer: string; answer_2?: string; content?: string }) {
    return request.post<ChallengeSubmitResponse>('/challenges/submit', data, { timeout: 25000 })
  },

  getResponses(challengeId: number, params: { page?: number; page_size?: number }) {
    return request.get<ChallengeResponseListResponse>(`/challenges/${challengeId}/responses`, { params })
  },

  getHistory(params: { page?: number; page_size?: number }) {
    return request.get<ChallengeHistoryResponse>('/challenges/history', { params })
  },

  deleteSubmission(submissionId: number) {
    return request.delete<ChallengeDeleteResponse>(`/challenges/submissions/${submissionId}`)
  },

  deleteChallenge(challengeId: number) {
    return request.delete<ChallengeDeleteResponse>(`/challenges/${challengeId}`)
  },

  getRankings(params: { period?: string; page?: number; page_size?: number }) {
    return request.get<ChallengeRankingResponse>('/challenges/rankings', { params })
  },

  aiGenerate(data: ChallengeAIGenerateRequest) {
    return request.post<ChallengeAIGenerateResponse>('/challenges/ai-generate', data, { timeout: 30000 })
  },

  aiHint(challengeId: number, data: ChallengeAIHintRequest) {
    return request.post<ChallengeAIHintResponse>(`/challenges/${challengeId}/ai-hint`, data, { timeout: 20000 })
  },

  aiReview(challengeId: number) {
    return request.post<ChallengeAIReviewResponse>(`/challenges/${challengeId}/ai-review`, {}, { timeout: 30000 })
  },

  aiCheckChallenge(data: ChallengeAICheckRequest) {
    return request.post<ChallengeAICheckResponse>('/challenges/ai-check', data)
  },

  aiExplain(challengeId: number) {
    return request.post<ChallengeAIExplainResponse>(`/challenges/${challengeId}/ai-explain`, {}, { timeout: 30000 })
  }
}