import request from '@/utils/request'

export interface AIRoundData {
  verse: string
  poem_title?: string
  author?: string
  dynasty?: string
  round_number: number
  verified?: boolean
}

export interface FeiHuaLingGameResponse {
  game_id: string
  keyword: string
  time_limit: number
  target_rounds: number
  ai_score: number
  ai_first_round?: AIRoundData
}

export interface PoemSubmitRequest {
  game_id: string
  poem_content: string
  response_time: number
  target_rounds?: number
}

export interface PoemSubmitResponse {
  valid: boolean
  message: string
  continue_game: boolean
  user_score: number
  ai_score: number
  round_number: number
  score_gained: number
  combo: number
  user_round_count: number
  poem_author?: string
  poem_title?: string
  poem_dynasty?: string
  ai_round?: AIRoundData
  ai_failed?: boolean
  retry?: boolean
}

export interface GameEndRequest {
  game_id: string
  reason: string
}

export interface RoundHistory {
  round_number: number
  player: string
  poem_content: string
  author?: string
  title?: string
  dynasty?: string
  created_at: string
}

export interface GameResult {
  game_id: string
  result: string
  user_score: number
  ai_score: number
  total_rounds: number
  user_round_count: number
  keyword: string
  duration: number
  rounds: RoundHistory[]
}

export interface GameHistoryItem {
  id: string
  keyword: string
  result: string
  user_score: number
  ai_score: number
  total_rounds: number
  created_at: string
}

export interface GameHistoryResponse {
  items: GameHistoryItem[]
  total: number
  page: number
  page_size: number
}

export const feiHuaLingApi = {
  startGame(difficulty?: number, keyword?: string): Promise<FeiHuaLingGameResponse> {
    return request.post('/feihualing/start', { difficulty, keyword }, { timeout: 30000 })
  },

  submitPoem(data: PoemSubmitRequest): Promise<PoemSubmitResponse> {
    return request.post('/feihualing/submit', data, { timeout: 15000 })
  },

  getHint(gameId: string): Promise<{ hint: string; author: string; hint_cost: number }> {
    return request.get(`/feihualing/hint/${gameId}`)
  },

  endGame(data: GameEndRequest): Promise<GameResult> {
    return request.post('/feihualing/end', data)
  },

  getHistory(params: { page: number; page_size: number }): Promise<GameHistoryResponse> {
    return request.get('/feihualing/history', { params })
  }
}
