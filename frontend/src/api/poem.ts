import request from '@/utils/request'

export interface Poem {
  id: number
  title: string
  author: string
  dynasty: string
  content: string
  category?: string
  genre?: string
  view_count: number
  favorite_count: number
}

export interface PoemDetail extends Poem {
  translation?: string
  annotation?: string
  background?: string
  appreciation?: string
  tags?: string
  created_at: string
  updated_at: string
  is_favorited: boolean
}

export interface PoemListResponse {
  items: Poem[]
  total: number
  page: number
  page_size: number
}

export const poemApi = {
  getList(params: {
    page?: number
    page_size?: number
    dynasty?: string
    author?: string
    category?: string
    genre?: string
  }) {
    return request.get<PoemListResponse>('/poems', { params })
  },

  getDetail(id: number) {
    return request.get<PoemDetail>(`/poems/${id}`)
  },

  search(params: {
    keyword: string
    search_type?: 'title' | 'author' | 'content'
    page?: number
    page_size?: number
  }) {
    return request.get<PoemListResponse>('/poems/search', { params })
  },

  getRandom(dynasty?: string) {
    return request.get<PoemDetail>('/poems/random', {
      params: dynasty ? { dynasty } : {}
    })
  },

  incrementView(id: number) {
    return request.post(`/poems/${id}/view`)
  },

  favorite(id: number) {
    return request.post(`/poems/${id}/favorite`)
  },

  unfavorite(id: number) {
    return request.delete(`/poems/${id}/favorite`)
  }
}
