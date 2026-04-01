import request from '@/utils/request'

export interface RelayRoomCreateRequest {
  mode: string
  difficulty: string
  max_rounds: number
  time_limit: number
  max_players?: number
  password?: string
}

export interface RelayPlayerInfo {
  user_id: number
  username: string
  avatar_url: string | null
  score: number
  combo: number
  is_host: boolean
}

export interface RelayRoundInfo {
  round: number
  user_id: number
  username: string
  verse: string
  poem_title: string | null
  author: string | null
  score: number
  time_used: number
}

export interface RelayRoomResponse {
  id: number
  room_code: string
  mode: string
  difficulty: string
  max_rounds: number
  time_limit: number
  status: string
  host_id: number
  host_username: string
  max_players: number
  has_password: boolean
  created_at: string
}

export interface RelayLobbyItem {
  id: number
  room_code: string
  difficulty: string
  max_rounds: number
  time_limit: number
  max_players: number
  player_count: number
  host_username: string
  host_avatar: string | null
  has_password: boolean
  created_at: string
}

export interface RelayLobbyResponse {
  items: RelayLobbyItem[]
  total: number
  page: number
  page_size: number
}

export interface RelayRoomDetail {
  id: number
  room_code: string
  mode: string
  difficulty: string
  status: string
  current_round: number
  max_rounds: number
  time_limit: number
  next_char: string | null
  players: RelayPlayerInfo[]
  rounds: RelayRoundInfo[]
}

export interface RelayStartResponse {
  room_id: number
  status: string
  current_round: number
  starter_verse: string
  starter_poem_title: string
  starter_author: string
  next_char: string
  started_at: string
}

export interface RelaySubmitResponse {
  round: number
  verse: string
  poem_title: string | null
  author: string | null
  is_valid: boolean
  match_type: string
  score: number
  next_char: string
  time_used: number
  combo: number
}

export interface RelayHintItem {
  verse: string
  poem_title: string
  author: string
}

export interface RelayHintResponse {
  hints: RelayHintItem[]
  hint_count_used: number
  hint_count_max: number
}

export interface RelayEndResultItem {
  user_id: number
  username: string
  total_score: number
  max_combo: number
  rounds_played: number
  avg_time: number
  rank: number
}

export interface RelayEndResponse {
  room_id: number
  total_rounds: number
  duration: number
  results: RelayEndResultItem[]
  exp_gained: number
  points_gained: number
  new_achievements: string[]
}

export interface RelayHistoryItem {
  room_id: number
  mode: string
  difficulty: string
  total_rounds: number
  total_score: number
  max_combo: number
  duration: number
  result: string
  played_at: string
}

export interface RelayRankingItem {
  rank: number
  user_id: number
  username: string
  avatar_url: string | null
  total_score: number
  total_games: number
  max_combo: number
  best_rounds: number
  win_rate: number
}

export const relayApi = {
  async createRoom(data: RelayRoomCreateRequest): Promise<RelayRoomResponse> {
    const res: any = await request.post('/relay/rooms', data)
    return res.data || res
  },

  async joinRoom(roomCode: string, password?: string): Promise<any> {
    const params = password ? { password } : {}
    const res: any = await request.post(`/relay/rooms/${roomCode}/join`, null, { params })
    return res.data || res
  },

  async startGame(roomId: number): Promise<RelayStartResponse> {
    const res: any = await request.post(`/relay/rooms/${roomId}/start`)
    return res.data || res
  },

  async submitVerse(roomId: number, verse: string): Promise<RelaySubmitResponse> {
    const res: any = await request.post(`/relay/rooms/${roomId}/submit`, { verse })
    return res.data || res
  },

  async getRoomDetail(roomId: number): Promise<RelayRoomDetail> {
    const res: any = await request.get(`/relay/rooms/${roomId}`)
    return res.data || res
  },

  async getHint(roomId: number): Promise<RelayHintResponse> {
    const res: any = await request.get(`/relay/rooms/${roomId}/hint`)
    return res.data || res
  },

  async endGame(roomId: number): Promise<RelayEndResponse> {
    const res: any = await request.post(`/relay/rooms/${roomId}/end`)
    return res.data || res
  },

  async getHistory(params: { page?: number; page_size?: number } = {}): Promise<{ items: RelayHistoryItem[]; total: number; page: number; page_size: number }> {
    const res: any = await request.get('/relay/history', { params })
    return res.data || res
  },

  async getRankings(params: { period?: string; page?: number; page_size?: number } = {}): Promise<{ items: RelayRankingItem[]; total: number; period: string }> {
    const res: any = await request.get('/relay/rankings', { params })
    return res.data || res
  },

  async getLobby(params: { page?: number; page_size?: number } = {}): Promise<RelayLobbyResponse> {
    const res: any = await request.get('/relay/lobby', { params })
    return res.data || res
  },

  async quickMatch(): Promise<RelayRoomResponse> {
    const res: any = await request.post('/relay/quick-match')
    return res.data || res
  }
}
