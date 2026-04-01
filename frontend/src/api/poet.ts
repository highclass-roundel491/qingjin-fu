import request from '@/utils/request'

export interface PoetBrief {
  id: number
  name: string
  dynasty: string
  alias?: string
  birth_death_desc?: string
  styles?: string
  brief?: string
  representative_works?: string
  influence_score: number
}

export interface PoetListItem {
  id: number
  name: string
  dynasty: string
  alias?: string
  birth_death_desc?: string
  styles?: string
  brief?: string
  influence_score: number
  poem_count: number
}

export interface PoetListResponse {
  items: PoetListItem[]
  total: number
}

export interface PoetDetail extends PoetBrief {
  birth_year?: string
  death_year?: string
  detailed_bio?: string
  poem_count: number
  portrait_url?: string
  created_at?: string
  updated_at?: string
}

export const poetApi = {
  getPoets(params: { page?: number; page_size?: number; dynasty?: string; keyword?: string } = {}) {
    return request.get<PoetListResponse>('/poets', { params })
  },

  getByName(name: string, dynasty?: string) {
    const params: Record<string, string> = { name }
    if (dynasty) params.dynasty = dynasty
    return request.get<PoetBrief | null>('/poets/by-name', { params })
  },

  getDetail(id: number) {
    return request.get<PoetDetail>(`/poets/${id}`)
  },
}
