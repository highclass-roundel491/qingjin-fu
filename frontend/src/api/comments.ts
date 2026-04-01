import request from '@/utils/request'

export interface CommentItem {
  id: number
  work_id: number
  user_id: number
  username: string
  nickname: string | null
  avatar_url: string | null
  parent_id: number | null
  reply_to_username: string | null
  content: string
  like_count: number
  is_liked: boolean
  created_at: string
  replies: CommentItem[]
}

export interface CommentListResponse {
  items: CommentItem[]
  total: number
  page: number
  page_size: number
}

export const commentsApi = {
  async getComments(workId: number, params: { page?: number; page_size?: number } = {}): Promise<CommentListResponse> {
    const res: any = await request.get(`/works/${workId}/comments`, { params })
    return res.data || res
  },

  async createComment(workId: number, data: { content: string; parent_id?: number | null }): Promise<CommentItem> {
    const res: any = await request.post(`/works/${workId}/comments`, data)
    return res.data || res
  },

  async deleteComment(workId: number, commentId: number): Promise<any> {
    const res: any = await request.delete(`/works/${workId}/comments/${commentId}`)
    return res.data || res
  },

  async likeComment(workId: number, commentId: number): Promise<any> {
    const res: any = await request.post(`/works/${workId}/comments/${commentId}/like`)
    return res.data || res
  },

  async unlikeComment(workId: number, commentId: number): Promise<any> {
    const res: any = await request.delete(`/works/${workId}/comments/${commentId}/like`)
    return res.data || res
  }
}
