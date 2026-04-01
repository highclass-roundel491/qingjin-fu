import { ref } from 'vue'
import { useUserStore } from '@/store/modules/user'

export type RelayWsMessage =
  | { type: 'player_joined'; user_id: number; username: string; avatar_url: string | null; players: WsPlayerInfo[]; player_count: number; max_players: number }
  | { type: 'player_left'; user_id: number; username: string; players: WsPlayerInfo[]; player_count: number }
  | { type: 'player_disconnected'; user_id: number; username: string; players: WsPlayerInfo[]; player_count: number; can_reconnect: boolean }
  | { type: 'player_reconnected'; user_id: number; username: string; players: WsPlayerInfo[]; player_count: number }
  | { type: 'ready_changed'; user_id: number; is_ready: boolean; all_ready: boolean; players: WsPlayerInfo[] }
  | { type: 'game_started'; starter_verse: string; starter_poem_title: string; starter_author: string; next_char: string; current_round: number; max_rounds: number; time_limit: number; current_turn: WsTurnInfo; players: WsPlayerInfo[] }
  | { type: 'game_state_sync'; next_char: string; current_round: number; max_rounds: number; time_limit: number; current_turn: WsTurnInfo; players: WsPlayerInfo[]; rounds: WsRoundItem[]; players_scores: WsPlayerScore[] }
  | { type: 'verse_accepted'; user_id: number; username: string; verse: string; poem_title: string | null; author: string | null; score: number; combo: number; current_round: number; next_char: string; players_scores: WsPlayerScore[]; game_finished: boolean; next_turn: WsTurnInfo | null }
  | { type: 'verse_invalid'; message: string }
  | { type: 'turn_timeout'; user_id: number; next_turn: WsTurnInfo }
  | { type: 'hint_response'; hints: WsHintItem[]; hint_count_used: number; hint_count_max: number }
  | { type: 'chat'; user_id: number; username: string; content: string }
  | { type: 'game_ended'; total_rounds: number; duration: number; results: WsGameResult[] }
  | { type: 'rematch_created'; new_room_id: number; new_room_code: string; players: WsPlayerInfo[]; player_count: number; max_players: number }
  | { type: 'kicked'; message: string }
  | { type: 'player_kicked'; user_id: number; username: string; players: WsPlayerInfo[]; player_count: number }
  | { type: 'error'; message: string }

export interface WsPlayerInfo {
  user_id: number
  username: string
  avatar_url: string | null
  is_host: boolean
  is_ready?: boolean
  connected?: boolean
}

export interface WsRoundItem {
  user_id: number
  username?: string
  verse: string
  poem_title?: string | null
  author?: string | null
  score: number
}

export interface WsTurnInfo {
  user_id: number
  username: string
}

export interface WsPlayerScore {
  user_id: number
  username: string
  score: number
  combo: number
  max_combo: number
  rounds_played: number
}

export interface WsHintItem {
  verse: string
  poem_title: string
  author: string
}

export interface WsGameResult {
  user_id: number
  username: string
  avatar_url: string | null
  total_score: number
  max_combo: number
  rounds_played: number
  avg_time: number
  rank: number
  exp_gained: number
  points_gained: number
}

export function useRelayWebSocket() {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const reconnecting = ref(false)
  const handlers = new Map<string, Set<(msg: any) => void>>()

  let reconnectAttempts = 0
  const maxReconnectAttempts = 5
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let currentRoomId: number | null = null

  function resolveDefaultApiBaseUrl(): string {
    if (typeof window === 'undefined') return 'http://localhost:8000/api/v1'
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
    return `${protocol}//${window.location.hostname}:8000/api/v1`
  }

  function getWsBaseUrl(): string {
    const apiBase = import.meta.env.VITE_API_BASE_URL || resolveDefaultApiBaseUrl()
    return apiBase.replace(/^http/, 'ws')
  }

  function connect(roomId: number) {
    const userStore = useUserStore()
    if (!userStore.token) return

    currentRoomId = roomId
    const url = `${getWsBaseUrl()}/ws/relay/${roomId}?token=${userStore.token}`

    if (ws.value) {
      ws.value.close()
    }

    const socket = new WebSocket(url)
    ws.value = socket

    socket.onopen = () => {
      connected.value = true
      reconnecting.value = false
      reconnectAttempts = 0
      emit('connected', {})
    }

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as RelayWsMessage
        const typeHandlers = handlers.get(msg.type)
        if (typeHandlers) {
          typeHandlers.forEach(fn => fn(msg))
        }
        const allHandlers = handlers.get('*')
        if (allHandlers) {
          allHandlers.forEach(fn => fn(msg))
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e)
      }
    }

    socket.onclose = (event) => {
      connected.value = false
      ws.value = null
      if (event.code === 4001) {
        emit('kicked', { message: event.reason || '你被房主移出了房间' })
        emit('disconnected', {})
      } else if (event.code !== 1000 && currentRoomId) {
        attemptReconnect()
      } else {
        emit('disconnected', {})
      }
    }

    socket.onerror = () => {
      connected.value = false
    }
  }

  function emit(type: string, data: any) {
    const typeHandlers = handlers.get(type)
    if (typeHandlers) {
      typeHandlers.forEach(fn => fn(data))
    }
  }

  function attemptReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts || !currentRoomId) {
      emit('disconnected', {})
      return
    }
    reconnecting.value = true
    reconnectAttempts++
    emit('reconnecting', { attempt: reconnectAttempts })
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 10000)
    reconnectTimer = setTimeout(() => {
      if (currentRoomId) {
        connect(currentRoomId)
      }
    }, delay)
  }

  function disconnect() {
    currentRoomId = null
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws.value) {
      ws.value.close(1000)
      ws.value = null
    }
    connected.value = false
    reconnecting.value = false
  }

  function send(action: string, data: Record<string, any> = {}) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ action, ...data }))
    }
  }

  function on(type: string, handler: (msg: any) => void) {
    if (!handlers.has(type)) {
      handlers.set(type, new Set())
    }
    handlers.get(type)!.add(handler)
  }

  function off(type: string, handler: (msg: any) => void) {
    handlers.get(type)?.delete(handler)
  }

  function startGame() {
    send('start_game')
  }

  function submitVerse(verse: string) {
    send('submit_verse', { verse })
  }

  function requestHint() {
    send('request_hint')
  }

  function sendChat(content: string) {
    send('chat', { content })
  }

  function endGame() {
    send('end_game')
  }

  function setReady() {
    send('ready')
  }

  function rematch() {
    send('rematch')
  }

  function kick(targetUserId: number) {
    send('kick', { target_user_id: targetUserId })
  }

  return {
    ws,
    connected,
    reconnecting,
    connect,
    disconnect,
    send,
    on,
    off,
    startGame,
    submitVerse,
    requestHint,
    sendChat,
    endGame,
    setReady,
    rematch,
    kick
  }
}
