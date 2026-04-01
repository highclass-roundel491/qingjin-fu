import request from '@/utils/request'

export interface AIChatRequest {
  prompt: string
  system_prompt?: string
  temperature?: number
  max_tokens?: number
}

export interface AIChatResponse {
  content: string
  model: string
}

export interface AIScoreRequest {
  question: string
  correct_answers: string[]
  user_answer: string
}

export interface AIScoreResponse {
  score: number
  accuracy_score: number
  artistic_score: number
  diction_score: number
  feedback: string
  is_correct: boolean
}

export interface AIReferencePoemInfo {
  title: string
  author: string
  dynasty: string
  content: string
  genre?: string
}

export interface AICreationRequest {
  context: string
  mode: 'continue' | 'inspire' | 'generate' | 'theme' | 'imitate_guide'
  keywords?: string[]
  reference_poem?: AIReferencePoemInfo
}

export interface AICreationResponse {
  content: string
  explanation: string
  suggestions?: string[]
}

export interface AICheckPoemRequest {
  poem_text: string
}

export interface AICheckPoemIssue {
  type: string
  location: string
  description: string
}

export interface AICheckPoemResponse {
  is_valid: boolean
  tone_analysis?: any[]
  rhyme_analysis?: Record<string, any>
  couplet_analysis?: Record<string, any>
  issues: AICheckPoemIssue[]
  suggestions: string[]
}

export interface AIAnalyzePoemRequest {
  poem_text: string
}

export interface AIAnalyzePoemResponse {
  total_score: number
  meter_score: number
  artistic_score: number
  diction_score: number
  overall_score: number
  highlights: string[]
  improvements: string[]
  appreciation: string
}

export function aiChat(data: AIChatRequest) {
  return request.post<AIChatResponse>('/ai/chat', data)
}

export function aiScore(data: AIScoreRequest) {
  return request.post<AIScoreResponse>('/ai/score', data)
}

const AI_TIMEOUT = { timeout: 60000 }
const AI_CONTEXT_TIMEOUT = { timeout: 120000 }

export function aiCreation(data: AICreationRequest) {
  return request.post<AICreationResponse>('/ai/creation', data, AI_TIMEOUT)
}

export function aiCheckPoem(data: AICheckPoemRequest) {
  return request.post<AICheckPoemResponse>('/ai/check-poem', data, AI_TIMEOUT)
}

export function aiAnalyzePoem(data: AIAnalyzePoemRequest) {
  return request.post<AIAnalyzePoemResponse>('/ai/analyze-poem', data, AI_TIMEOUT)
}

export type PoemContextQueryType = 'author_bio' | 'deep_appreciation' | 'allusions' | 'verse_analysis' | 'free_qa' | 'meter_analysis'

export interface AIPoemContextRequest {
  title: string
  author: string
  dynasty: string
  content: string
  genre?: string
  category?: string
  query_type: PoemContextQueryType
  question?: string
}

export interface AIPoemContextSection {
  heading: string
  text: string
}

export interface AIMeterLine {
  text: string
  tones: string[]
  rhyme: string
  couplet: string
  note: string
}

export interface AIPoemContextResponse {
  query_type: string
  content: string
  title?: string
  sections?: AIPoemContextSection[]
  lines?: AIMeterLine[]
  rhyme_scheme?: string
  meter_type?: string
}

export function aiPoemContext(data: AIPoemContextRequest) {
  return request.post<AIPoemContextResponse>('/ai/poem-context', data, AI_CONTEXT_TIMEOUT)
}

export interface AIPoemChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AIPoemChatRequest {
  title: string
  author: string
  dynasty: string
  content: string
  genre?: string
  category?: string
  history: AIPoemChatMessage[]
  message: string
}

export interface StreamEvent {
  type: 'content' | 'thinking' | 'tool_call' | 'memory' | 'error' | 'done'
  content?: string
  tools?: string[]
  labels?: string[]
  round?: number
}

export async function aiPoemChatStream(
  data: AIPoemChatRequest,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError?: (err: string) => void,
  onEvent?: (event: StreamEvent) => void,
) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  const userStore = (await import('@/store/modules/user')).useUserStore()
  const token = userStore.token

  const response = await fetch(`${baseURL}/ai/poem-chat-stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(data),
  })

  if (!response.ok || !response.body) {
    onError?.('AI对话服务暂时不可用')
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const payload = line.slice(6).trim()
      if (payload === '[DONE]') {
        onDone()
        return
      }
      try {
        const parsed = JSON.parse(payload)
        if (parsed.error) {
          onError?.(parsed.error)
          return
        }
        if (parsed.type === 'thinking' || parsed.type === 'tool_call' || parsed.type === 'memory') {
          onEvent?.(parsed as StreamEvent)
        } else if (parsed.content) {
          onChunk(parsed.content)
        }
      } catch {
      }
    }
  }
  onDone()
}

export async function aiStreamRequest<T>(
  url: string,
  data: Record<string, any>,
  onEvent: (event: StreamEvent) => void,
  onResult: (result: T) => void,
  onError?: (err: string) => void,
) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  const userStore = (await import('@/store/modules/user')).useUserStore()
  const token = userStore.token

  const response = await fetch(`${baseURL}${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(data),
  })

  if (!response.ok || !response.body) {
    onError?.('AI服务暂时不可用')
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const payload = line.slice(6).trim()
      if (!payload) continue
      try {
        const parsed = JSON.parse(payload)
        if (parsed.type === 'error') {
          onError?.(parsed.content || 'AI服务暂时不可用')
          return
        }
        if (parsed.type === 'result') {
          onResult(parsed.data as T)
          return
        }
        if (parsed.type === 'thinking' || parsed.type === 'tool_call') {
          onEvent(parsed as StreamEvent)
        }
      } catch {}
    }
  }
}

export function aiCheckPoemStream(
  data: AICheckPoemRequest,
  onEvent: (event: StreamEvent) => void,
  onResult: (result: AICheckPoemResponse) => void,
  onError?: (err: string) => void,
) {
  return aiStreamRequest<AICheckPoemResponse>('/ai/check-poem-stream', data, onEvent, onResult, onError)
}

export function aiAnalyzePoemStream(
  data: AIAnalyzePoemRequest,
  onEvent: (event: StreamEvent) => void,
  onResult: (result: AIAnalyzePoemResponse) => void,
  onError?: (err: string) => void,
) {
  return aiStreamRequest<AIAnalyzePoemResponse>('/ai/analyze-poem-stream', data, onEvent, onResult, onError)
}

export function aiCreationStream(
  data: AICreationRequest,
  onEvent: (event: StreamEvent) => void,
  onResult: (result: AICreationResponse) => void,
  onError?: (err: string) => void,
) {
  return aiStreamRequest<AICreationResponse>('/ai/creation-stream', data, onEvent, onResult, onError)
}

export function aiPoemContextStream(
  data: AIPoemContextRequest,
  onEvent: (event: StreamEvent) => void,
  onResult: (result: AIPoemContextResponse) => void,
  onError?: (err: string) => void,
) {
  return aiStreamRequest<AIPoemContextResponse>('/ai/poem-context-stream', data, onEvent, onResult, onError)
}
