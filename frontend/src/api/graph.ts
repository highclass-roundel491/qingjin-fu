import request from '@/utils/request'

export interface GraphNode {
  id: string
  name: string
  category: number
  value: number
  symbolSize: number
  dynasty?: string
  poem_count?: number
  representative_work?: string
  alias?: string
  influence?: number
  styles?: string[]
  description?: string
}

export interface GraphLink {
  source: string
  target: string
  value: number
  label?: string
  description?: string
}

export interface GraphCategory {
  name: string
}

export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
  categories: GraphCategory[]
}

export interface DynastyItem {
  name: string
  count: number
}

export interface CategoryItem {
  name: string
  count: number
}

export interface PoetRelationItem {
  target: string
  label: string
  description: string
}

export interface AuthorDetail {
  name: string
  dynasty: string
  poem_count: number
  categories: string[]
  representative_poems: { id: number; title: string; content: string }[]
  alias?: string
  influence?: number
  styles?: string[]
  description?: string
  relations?: PoetRelationItem[]
}

export interface PoetProfile {
  alias: string
  years: string
  influence: number
  styles: string[]
  description: string
}

export interface PoetRelation {
  source: string
  target: string
  label: string
  description: string
}

export interface DynastyProfile {
  description: string
  influence: string
  poem_count_label: string
}

export interface AIRelationSection {
  title: string
  content: string
}

export interface AIRelationResponse {
  poet_a: string
  poet_b: string
  summary: string
  sections: AIRelationSection[]
  known_relation?: string
}

export const graphApi = {
  getData(params?: { dynasty?: string; category?: string; min_poems?: number }) {
    return request.get<GraphData>('/graph/data', { params, timeout: 30000 })
  },

  getDynasties() {
    return request.get<DynastyItem[]>('/graph/dynasties')
  },

  getCategories() {
    return request.get<CategoryItem[]>('/graph/categories')
  },

  getAuthorDetail(authorName: string) {
    return request.get<AuthorDetail>(`/graph/author/${encodeURIComponent(authorName)}`)
  },

  getDynastyProfiles() {
    return request.get<Record<string, DynastyProfile>>('/graph/dynasty-profiles')
  },

  getPoetProfiles() {
    return request.get<Record<string, PoetProfile>>('/graph/poet-profiles')
  },

  getPoetRelations() {
    return request.get<PoetRelation[]>('/graph/poet-relations')
  },

  aiRelation(poetA: string, poetB: string) {
    return request.post<AIRelationResponse>('/graph/ai-relation', {
      poet_a: poetA,
      poet_b: poetB,
    }, { timeout: 60000 })
  }
}
