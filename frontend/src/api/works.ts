import request from '@/utils/request'

export interface WorkCreateRequest {
  title: string
  content: string
  genre: string
}

export interface WorkUpdateRequest {
  title?: string
  content?: string
  genre?: string
}

export interface WorkItem {
  id: number
  user_id: number
  username: string
  avatar_url: string | null
  title: string
  content: string
  genre: string
  status: string
  ai_total_score: number | null
  like_count: number
  view_count: number
  is_liked: boolean
  created_at: string
  published_at: string | null
}

export interface WorkDetail {
  id: number
  user_id: number
  username: string
  avatar_url: string | null
  title: string
  content: string
  genre: string
  status: string
  ai_grammar_score: number | null
  ai_artistic_score: number | null
  ai_total_score: number | null
  ai_feedback: string | null
  like_count: number
  view_count: number
  comment_count: number
  is_liked: boolean
  created_at: string
  updated_at: string
  published_at: string | null
}

export interface WorkListResponse {
  items: WorkItem[]
  total: number
  page: number
  page_size: number
}

export interface WorkRankingItem {
  rank: number
  user_id: number
  username: string
  avatar_url: string | null
  exp: number
  level: number
  work_count: number
  total_likes: number
  avg_score: number | null
}

export interface WorkPieceRankingItem {
  rank: number
  work_id: number
  title: string
  content: string
  genre: string
  user_id: number
  username: string
  avatar_url: string | null
  like_count: number
  view_count: number
  ai_grammar_score: number | null
  ai_artistic_score: number | null
  ai_total_score: number | null
  composite_score: number
  published_at: string | null
}

export interface WorkPieceRankingResponse {
  items: WorkPieceRankingItem[]
  total: number
  ranking_type: string
  period: string
}

export interface AIScoreResponse {
  work_id: number
  grammar_score: number
  artistic_score: number
  total_score: number
  feedback: string
  composite_score: number
}

export const worksApi = {
  async createWork(data: WorkCreateRequest): Promise<any> {
    const res: any = await request.post('/works', data)
    return res.data
  },

  async updateWork(workId: number, data: WorkUpdateRequest): Promise<any> {
    const res: any = await request.put(`/works/${workId}`, data)
    return res.data
  },

  async publishWork(workId: number): Promise<any> {
    const res: any = await request.post(`/works/${workId}/publish`)
    return res.data
  },

  async unpublishWork(workId: number): Promise<any> {
    const res: any = await request.post(`/works/${workId}/unpublish`)
    return res.data
  },

  async deleteWork(workId: number): Promise<any> {
    const res: any = await request.delete(`/works/${workId}`)
    return res.data
  },

  async getWorks(params: {
    sort?: string
    genre?: string
    page?: number
    page_size?: number
  } = {}): Promise<WorkListResponse> {
    const res: any = await request.get('/works', { params })
    return res.data
  },

  async getMyWorks(params: {
    status?: string
    page?: number
    page_size?: number
  } = {}): Promise<WorkListResponse> {
    const res: any = await request.get('/works/mine', { params })
    return res.data
  },

  async getWorkDetail(workId: number): Promise<WorkDetail> {
    const res: any = await request.get(`/works/${workId}`)
    return res.data
  },

  async likeWork(workId: number): Promise<any> {
    const res: any = await request.post(`/works/${workId}/like`)
    return res
  },

  async unlikeWork(workId: number): Promise<any> {
    const res: any = await request.delete(`/works/${workId}/like`)
    return res
  },

  async getRankings(params: {
    period?: string
    page?: number
    page_size?: number
  } = {}): Promise<{ items: WorkRankingItem[]; total: number }> {
    const res: any = await request.get('/works/rankings', { params })
    return res.data
  },

  async getWorkPieceRankings(params: {
    ranking_type?: string
    period?: string
    genre?: string
    page?: number
    page_size?: number
  } = {}): Promise<WorkPieceRankingResponse> {
    const res: any = await request.get('/works/rankings/works', { params })
    return res.data
  },

  async scoreWorkWithAI(workId: number): Promise<AIScoreResponse> {
    const res: any = await request.post(`/works/${workId}/ai-score`)
    return res.data
  }
}
