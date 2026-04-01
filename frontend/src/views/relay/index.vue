<template>
  <div class="relay-page">
    <img :src="waveBg" class="relay-bg-wave" alt="" />
    <img :src="inkSplash" class="relay-bg-ink" alt="" />

    <nav class="page-nav">
      <div class="nav-inner">
        <router-link to="/games" class="back-link">
          <img :src="chainLinkIcon" class="back-icon" alt="" />
          <span>返回</span>
        </router-link>
        <h1 class="page-title">诗词接龙</h1>
        <div class="nav-actions">
          <router-link to="/relay/history" class="nav-action-link">历史</router-link>
          <router-link to="/relay/rankings" class="nav-action-link">排行</router-link>
        </div>
      </div>
    </nav>

    <div class="relay-content" v-if="phase === 'setup'">
      <div class="relay-guide" v-if="!guideHidden">
        <div class="relay-guide__body">
          <div class="relay-guide__icon">龙</div>
          <div class="relay-guide__text">
            <h3 class="relay-guide__title">诗词接龙</h3>
            <p class="relay-guide__desc">上一句诗的末字 = 下一句的首字，在限时内接出真实诗句即可得分。连击越多分数越高，还可使用提示。</p>
          </div>
          <button class="relay-guide__close" @click="guideHidden = true" title="收起">✕</button>
        </div>
        <div class="relay-guide__steps">
          <span class="relay-guide__step">选择模式与难度</span>
          <span class="relay-guide__arrow">→</span>
          <span class="relay-guide__step">系统出首句</span>
          <span class="relay-guide__arrow">→</span>
          <span class="relay-guide__step">你来接龙</span>
          <span class="relay-guide__arrow">→</span>
          <span class="relay-guide__step">获得积分与经验</span>
        </div>
      </div>

      <div class="mode-selector">
        <div class="mode-card" :class="{ active: gameMode === 'single' }" @click="gameMode = 'single'">
          <img :src="dragonSeal" class="mode-card__icon" alt="" />
          <div class="mode-card__title">单人练习</div>
          <div class="mode-card__desc">独自接龙，磨炼诗词功底</div>
        </div>
        <div class="mode-card" :class="{ active: gameMode === 'multi' }" @click="gameMode = 'multi'">
          <img :src="chainLinkIcon" class="mode-card__icon" alt="" />
          <div class="mode-card__title">多人对弈</div>
          <div class="mode-card__desc">实时对战，以诗会友</div>
        </div>
      </div>

      <div class="setup-panel">
        <div class="setup-header">
          <img :src="dragonSeal" class="seal-icon" alt="" />
          <h2>{{ gameMode === 'single' ? '单人接龙' : '多人对弈' }}</h2>
          <p class="setup-desc">以诗会友，尾字接首字，妙语连珠</p>
        </div>

        <div class="setup-form">
          <div class="form-group">
            <label>难度</label>
            <div class="option-group option-group--difficulty">
              <button v-for="d in difficulties" :key="d.value" class="option-btn diff-btn" :class="{ active: form.difficulty === d.value, [d.value]: true }" @click="form.difficulty = d.value">
                <span class="diff-label">{{ d.label }}</span>
                <span class="diff-desc">{{ d.desc }}</span>
              </button>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group form-group--half">
              <label>回合数</label>
              <div class="option-group">
                <button v-for="r in roundOptions" :key="r" class="option-btn" :class="{ active: form.max_rounds === r }" @click="form.max_rounds = r">
                  {{ r }}
                </button>
              </div>
            </div>
            <div class="form-group form-group--half">
              <label>限时</label>
              <div class="option-group">
                <button v-for="t in timeOptions" :key="t" class="option-btn" :class="{ active: form.time_limit === t }" @click="form.time_limit = t">
                  {{ t }}s
                </button>
              </div>
            </div>
          </div>
          <div class="form-group" v-if="gameMode === 'multi'">
            <label>人数</label>
            <div class="option-group">
              <button v-for="p in playerOptions" :key="p" class="option-btn" :class="{ active: form.max_players === p }" @click="form.max_players = p">
                {{ p }}人
              </button>
            </div>
          </div>
          <div class="form-group" v-if="gameMode === 'multi'">
            <label>房间密码<span class="label-hint">（可选）</span></label>
            <input v-model="form.password" class="form-text-input" type="text" placeholder="留空则开放加入" maxlength="20" autocomplete="off" />
          </div>
          <button class="start-btn" @click="gameMode === 'single' ? startSingleGame() : createMultiRoom()" :disabled="loading">
            <span>{{ loading ? '准备中...' : (gameMode === 'single' ? '开始接龙' : '创建房间') }}</span>
          </button>
        </div>
      </div>

      <div class="lobby-section" v-if="gameMode === 'multi'">
        <div class="lobby-header">
          <span class="lobby-title">在线房间</span>
          <div class="lobby-actions">
            <button class="lobby-btn lobby-btn--primary" @click="quickMatch" :disabled="loading">快速匹配</button>
            <button class="lobby-btn" @click="showJoinInput = !showJoinInput">输入房间号</button>
            <button class="lobby-btn" @click="loadLobby">刷新</button>
          </div>
        </div>
        <div class="join-input-row" v-if="showJoinInput">
          <input v-model="joinCode" class="join-code-input" placeholder="输入8位房间号" maxlength="8" @keyup.enter="joinRoomByCode" />
          <input v-model="joinPassword" class="join-code-input" placeholder="密码（可选）" maxlength="20" type="text" />
          <button class="lobby-btn lobby-btn--primary" @click="joinRoomByCode" :disabled="!joinCode.trim()">加入</button>
        </div>
        <div class="room-list" v-if="lobbyRooms.length > 0">
          <div v-for="room in lobbyRooms" :key="room.id" class="room-item" :style="{ animationDelay: lobbyRooms.indexOf(room) * 0.05 + 's' }">
            <div class="room-info">
              <div class="room-host">{{ room.host_username }}</div>
              <div class="room-meta">
                <span>{{ diffLabel(room.difficulty) }}</span>
                <span>{{ room.max_rounds }}回合</span>
                <span>{{ room.time_limit }}s</span>
              </div>
            </div>
            <div class="room-players">{{ room.player_count }}/{{ room.max_players }}</div>
            <span class="room-lock" v-if="room.has_password" title="需要密码">🔒</span>
            <button class="join-room-btn" @click="handleJoinLobbyRoom(room)">加入</button>
          </div>
        </div>
        <div class="lobby-empty" v-else>暂无可加入的房间</div>
      </div>
    </div>

    <div class="waiting-room" v-if="phase === 'waiting'">
      <div class="waiting-card">
        <img :src="dragonSeal" class="seal-icon" alt="" />
        <h2>等待玩家加入</h2>
        <div class="room-code-display" @click="copyRoomCode" :title="codeCopied ? '已复制' : '点击复制房间号'">
          {{ currentRoomCode }}
        </div>
        <div class="code-hint">{{ codeCopied ? '已复制到剪贴板' : '分享房间号给好友' }}</div>

        <div class="players-list">
          <div v-for="p in wsPlayers" :key="p.user_id" class="player-slot" :class="{ 'player-slot--disconnected': p.connected === false }">
            <div class="player-avatar">{{ p.username[0] }}</div>
            <div class="player-name">{{ p.username }}</div>
            <div class="player-badge" v-if="p.is_host">房主</div>
            <div class="player-badge player-badge--ready" v-else-if="p.is_ready">已准备</div>
            <div class="player-badge player-badge--not-ready" v-else-if="p.connected !== false">未准备</div>
            <div class="player-badge player-badge--offline" v-if="p.connected === false">离线</div>
            <button class="kick-btn" v-if="isHost && !p.is_host" @click="kickPlayer(p.user_id)" title="移出房间">✕</button>
          </div>
          <div v-for="i in emptySlots" :key="'empty-'+i" class="player-slot player-slot--empty">
            等待加入...
          </div>
        </div>

        <div class="waiting-dots" v-if="wsPlayers.length < wsMaxPlayers">
          <span></span><span></span><span></span>
        </div>

        <div class="waiting-actions">
          <button class="action-btn" :class="myReady ? 'cancel-ready' : 'ready'" v-if="!isHost" @click="toggleReady">{{ myReady ? '取消准备' : '准备' }}</button>
          <button class="action-btn primary" v-if="isHost && allReady" @click="wsStartGame">开始游戏</button>
          <button class="action-btn primary disabled" v-else-if="isHost" disabled>等待全员准备</button>
          <button class="action-btn" @click="leaveWaitingRoom">离开</button>
        </div>

        <div class="chat-area">
          <div class="chat-messages" ref="chatScroll">
            <div v-for="(msg, idx) in chatMessages" :key="idx" class="chat-msg" :class="{ 'chat-msg--system': msg.system }">
              <span class="chat-msg-user" v-if="!msg.system">{{ msg.username }}：</span>{{ msg.content }}
            </div>
          </div>
          <div class="chat-input-row">
            <input v-model="chatInput" class="chat-input" placeholder="发送消息..." @keyup.enter="sendChatMsg" maxlength="100" />
            <button class="chat-send-btn" @click="sendChatMsg">发送</button>
          </div>
        </div>
      </div>
    </div>

    <div class="game-arena" v-if="phase === 'playing'">
      <div class="game-header">
        <div class="game-info">
          <span class="info-tag round-tag">{{ currentRound }} / {{ maxRounds }}</span>
          <span class="info-tag score-tag">
            {{ playerScore }} 分
            <span v-if="scoreFloat" class="score-float" :key="scoreFloatKey">+{{ scoreFloat }}</span>
          </span>
          <span class="info-tag exp-tag">
            {{ runningExp }} 经验
            <span v-if="expFloat" class="exp-float" :key="expFloatKey">+{{ expFloat }}</span>
          </span>
          <span class="info-tag combo-tag" v-if="currentCombo > 1" :key="'combo-' + currentCombo">{{ currentCombo }} 连击</span>
        </div>
        <div class="header-right">
          <div class="countdown-ring" v-if="turnTimeLeft > 0" :class="{ 'countdown-ring--urgent': turnTimeLeft <= 5 }">
            <svg viewBox="0 0 36 36" class="countdown-svg">
              <circle class="countdown-bg" cx="18" cy="18" r="15.9" />
              <circle class="countdown-progress" cx="18" cy="18" r="15.9" :style="{ strokeDashoffset: countdownOffset }" />
            </svg>
            <span class="countdown-text">{{ turnTimeLeft }}</span>
          </div>
          <button class="quit-btn" @click="quitGame">结束</button>
        </div>
      </div>

      <div class="players-bar" v-if="isMultiMode">
        <div v-for="p in wsPlayersScores" :key="p.user_id" class="player-chip" :class="{ 'player-chip--active': p.user_id === currentTurnUserId }">
          <div class="player-chip__avatar">{{ p.username[0] }}</div>
          <span class="player-chip__name">{{ p.username }}</span>
          <span class="player-chip__score">{{ p.score }}</span>
        </div>
      </div>

      <div class="verse-chain">
        <div class="chain-scroll" ref="chainScroll">
          <div v-for="(r, idx) in rounds" :key="idx" class="chain-item" :class="chainItemClass(r)" :style="{ animationDelay: idx * 0.05 + 's' }">
            <div class="chain-connector" v-if="idx > 0">
              <span class="connector-char">{{ getConnectorChar(idx) }}</span>
            </div>
            <div class="chain-badge">{{ r.user_id === 0 ? '题' : (isMultiMode ? r.username?.[0] || '答' : '答') }}</div>
            <div class="chain-body">
              <div class="chain-verse">
                <span class="verse-first" v-if="r.verse">{{ r.verse[0] }}</span><span v-if="r.verse">{{ r.verse.slice(1, -1) }}</span><span class="verse-last" v-if="r.verse && r.verse.length > 1">{{ r.verse[r.verse.length - 1] }}</span>
              </div>
              <div class="chain-source" v-if="r.poem_title">{{ r.author }}《{{ r.poem_title }}》</div>
              <div class="chain-player-name" v-if="isMultiMode && r.user_id !== 0">{{ r.username }}</div>
            </div>
            <div class="chain-score" v-if="r.score > 0">+{{ r.score }}</div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <template v-if="isMyTurn || !isMultiMode">
          <div class="next-char-hint">
            <span class="hint-label">请接</span>
            <span class="hint-char-box">
              <span class="hint-char">{{ nextChar }}</span>
            </span>
            <span class="hint-label">字开头的诗句</span>
          </div>
          <div class="input-row">
            <input v-model="inputVerse" class="verse-input" :placeholder="`${nextChar}...`" @keyup.enter="submitVerse" :disabled="submitting" maxlength="50" ref="verseInputRef" />
            <button class="submit-btn" @click="submitVerse" :disabled="submitting || !inputVerse.trim()">
              {{ submitting ? '...' : '接龙' }}
            </button>
          </div>
          <div class="input-actions">
            <button class="hint-btn" @click="requestHint" :disabled="hintsUsed >= 3">
              <img :src="hintLantern" class="hint-btn-icon" alt="" />
              提示 ({{ 3 - hintsUsed }})
            </button>
          </div>
          <div class="emoji-bar" v-if="isMultiMode">
            <button v-for="e in quickEmojis" :key="e" class="emoji-btn" @click="sendEmoji(e)">{{ e }}</button>
          </div>
          <div class="hint-panel" v-if="hints.length > 0">
            <div v-for="(h, idx) in hints" :key="idx" class="hint-item" @click="useHint(h)" :style="{ animationDelay: idx * 0.08 + 's' }">
              <span class="hint-verse">{{ h.verse }}</span>
              <span class="hint-source">{{ h.author }}《{{ h.poem_title }}》</span>
            </div>
          </div>
        </template>
        <div class="input-disabled-msg" v-else>
          <div class="turn-indicator turn-indicator--other">
            <span class="turn-wait-dots"><span></span><span></span><span></span></span>
            等待 {{ currentTurnUsername }} 接龙...
          </div>
        </div>
      </div>

      <div class="game-result" v-if="gameEnded" @click.self="backToSetup">
        <div class="result-card">
          <img :src="dragonSeal" class="result-seal-img" alt="" />
          <h3>游戏结束</h3>
          <div class="result-rankings" v-if="isMultiMode && multiResults.length > 0">
            <div v-for="r in multiResults" :key="r.user_id" class="result-rank-item">
              <div class="rank-num">#{{ r.rank }}</div>
              <div class="rank-info">
                <div class="rank-name">{{ r.username }}</div>
                <div class="rank-detail">{{ r.rounds_played }}回合 / {{ r.max_combo }}连击</div>
              </div>
              <div class="rank-score">
                <div class="rank-score-value">{{ r.total_score }}</div>
                <div class="rank-exp">+{{ r.exp_gained }}exp</div>
              </div>
            </div>
          </div>
          <div class="result-stats" v-else>
            <div class="result-stat">
              <span class="stat-value">{{ singleResult?.total_rounds || 0 }}</span>
              <span class="stat-label">回合</span>
            </div>
            <div class="result-stat">
              <span class="stat-value">{{ singleResult?.results[0]?.total_score || 0 }}</span>
              <span class="stat-label">得分</span>
            </div>
            <div class="result-stat">
              <span class="stat-value">{{ singleResult?.results[0]?.max_combo || 0 }}</span>
              <span class="stat-label">最大连击</span>
            </div>
            <div class="result-stat">
              <span class="stat-value">+{{ singleResult?.exp_gained || 0 }}</span>
              <span class="stat-label">经验</span>
            </div>
          </div>
          <div class="result-actions">
            <button class="action-btn primary" v-if="isMultiMode && isHost" @click="requestRematch">同房再来一局</button>
            <button class="action-btn primary" v-if="!isMultiMode" @click="restartGame">再来一局</button>
            <button class="action-btn" @click="backToSetup">返回</button>
          </div>
        </div>
      </div>
    </div>

    <div class="turn-notify" v-if="turnNotifyVisible" :key="turnNotifyKey">
      <div class="turn-notify__card" :class="{ 'turn-notify__card--mine': turnNotifyMine }">
        <span class="turn-notify__icon">{{ turnNotifyMine ? '笔' : '待' }}</span>
        <span class="turn-notify__text">{{ turnNotifyMine ? '轮到你了！' : `${currentTurnUsername} 的回合` }}</span>
      </div>
    </div>

    <div class="achievement-popup" v-if="achievementPopup" :key="achievementPopupKey">
      <div class="achievement-popup__card">
        <div class="achievement-popup__icon">章</div>
        <div class="achievement-popup__body">
          <div class="achievement-popup__title">获得成就</div>
          <div class="achievement-popup__name">{{ achievementPopup }}</div>
        </div>
      </div>
    </div>

    <div class="ws-status" v-if="isMultiMode && phase === 'playing' && wsConnectionStatus !== 'connected'">
      <span class="ws-status__dot" :class="'ws-status__dot--' + wsConnectionStatus"></span>
      <span>{{ wsConnectionStatus === 'reconnecting' ? '重连中...' : '已断开' }}</span>
    </div>

    <div class="error-toast" v-if="errorMsg" @click="errorMsg = ''">
      {{ errorMsg }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { relayApi, type RelayRoomDetail, type RelayEndResponse, type RelayLobbyItem } from '@/api/relay'
import { useRelayWebSocket, type WsPlayerInfo, type WsPlayerScore, type WsGameResult } from '@/utils/relay-ws'
import { useUserStore } from '@/store/modules/user'

import chainLinkIcon from '@/assets/icons/relay/chain-link.svg'
import dragonSeal from '@/assets/icons/relay/dragon-seal.svg'
import waveBg from '@/assets/icons/relay/wave-bg.svg'
import inkSplash from '@/assets/icons/relay/ink-splash.svg'
import hintLantern from '@/assets/icons/relay/hint-lantern.svg'

const userStore = useUserStore()
const ws = useRelayWebSocket()

const guideHidden = ref(false)
const phase = ref<'setup' | 'waiting' | 'playing'>('setup')
const gameMode = ref<'single' | 'multi'>('single')
const loading = ref(false)
const submitting = ref(false)
const errorMsg = ref('')
const inputVerse = ref('')
const chainScroll = ref<HTMLElement | null>(null)
const verseInputRef = ref<HTMLInputElement | null>(null)
const chatScroll = ref<HTMLElement | null>(null)

const currentCombo = ref(0)
const playerScore = ref(0)
const hintsUsed = ref(0)
const hints = ref<{ verse: string; poem_title: string; author: string }[]>([])
const scoreFloat = ref<number | null>(null)
const scoreFloatKey = ref(0)
const expFloat = ref<number | null>(null)
const expFloatKey = ref(0)

const currentRoomId = ref(0)
const currentRoomCode = ref('')

const gameState = ref<RelayRoomDetail | null>(null)
const singleResult = ref<RelayEndResponse | null>(null)

const wsPlayers = ref<WsPlayerInfo[]>([])
const wsPlayersScores = ref<WsPlayerScore[]>([])
const wsMaxPlayers = ref(2)
const isHost = ref(false)
const currentTurnUserId = ref<number | null>(null)
const currentTurnUsername = ref('')
const nextChar = ref('')
const currentRound = ref(0)
const maxRounds = ref(20)
const timeLimit = ref(30)
const gameEnded = ref(false)
const multiResults = ref<WsGameResult[]>([])
const rounds = ref<{ user_id: number; username?: string; verse: string; poem_title?: string | null; author?: string | null; score: number }[]>([])

const lobbyRooms = ref<RelayLobbyItem[]>([])
const showJoinInput = ref(false)
const joinCode = ref('')
const joinPassword = ref('')
const codeCopied = ref(false)

const chatMessages = ref<{ username: string; content: string; system?: boolean }[]>([])
const chatInput = ref('')

const turnTimeLeft = ref(0)
let turnTimerHandle: ReturnType<typeof setInterval> | null = null
const turnNotifyVisible = ref(false)
const turnNotifyMine = ref(false)
const turnNotifyKey = ref(0)
const achievementPopup = ref('')
const achievementPopupKey = ref(0)
const wsConnectionStatus = ref<'connected' | 'reconnecting' | 'disconnected'>('connected')
const myReady = ref(false)
const allReady = ref(false)

const runningExp = computed(() => Math.floor(playerScore.value / 2))
const isMultiMode = computed(() => gameMode.value === 'multi')
const isMyTurn = computed(() => currentTurnUserId.value === userStore.userInfo?.id)
const emptySlots = computed(() => Math.max(0, wsMaxPlayers.value - wsPlayers.value.length))
const countdownOffset = computed(() => {
  if (timeLimit.value <= 0) return 100
  const pct = turnTimeLeft.value / timeLimit.value
  return 100 - pct * 100
})

const difficulties = [
  { value: 'easy', label: '简单', desc: '不限出处' },
  { value: 'normal', label: '普通', desc: '首字匹配' },
  { value: 'hard', label: '困难', desc: '严格匹配' }
]
const roundOptions = [10, 20, 30, 50]
const timeOptions = [15, 30, 45, 60]
const playerOptions = [2, 3, 4]
const quickEmojis = ['👏', '🎉', '💪', '😂', '🤔', '😱', '🙏', '❤️']

const sendEmoji = (emoji: string) => {
  ws.sendChat(emoji)
}

const form = reactive({
  difficulty: 'normal',
  max_rounds: 20,
  time_limit: 30,
  max_players: 2,
  password: ''
})

const diffLabel = (d: string) => {
  const map: Record<string, string> = { easy: '简单', normal: '普通', hard: '困难' }
  return map[d] || d
}

const showError = (msg: string) => {
  errorMsg.value = msg
  setTimeout(() => { errorMsg.value = '' }, 3000)
}

const scrollToBottom = async () => {
  await nextTick()
  if (chainScroll.value) {
    chainScroll.value.scrollTop = chainScroll.value.scrollHeight
  }
}

const scrollChatToBottom = async () => {
  await nextTick()
  if (chatScroll.value) {
    chatScroll.value.scrollTop = chatScroll.value.scrollHeight
  }
}

const getConnectorChar = (idx: number) => {
  if (idx <= 0 || !rounds.value[idx - 1]) return ''
  const prevVerse = rounds.value[idx - 1]?.verse
  if (!prevVerse) return ''
  const clean = prevVerse.replace(/[\u3002\uff0c\uff01\uff1f\u3001\uff1b\uff1a\u201c\u201d\u2018\u2019\uff08\uff09]/g, '')
  return clean[clean.length - 1] || ''
}

const chainItemClass = (r: { user_id: number }) => {
  if (r.user_id === 0) return 'system'
  if (!isMultiMode.value) return 'player'
  return r.user_id === userStore.userInfo?.id ? 'player' : 'other-player'
}

const startTurnTimer = (seconds?: number) => {
  stopTurnTimer()
  turnTimeLeft.value = seconds || timeLimit.value
  turnTimerHandle = setInterval(() => {
    turnTimeLeft.value--
    if (turnTimeLeft.value <= 0) {
      stopTurnTimer()
    }
  }, 1000)
}

const stopTurnTimer = () => {
  if (turnTimerHandle) {
    clearInterval(turnTimerHandle)
    turnTimerHandle = null
  }
  turnTimeLeft.value = 0
}

const showTurnNotify = (isMine: boolean) => {
  turnNotifyMine.value = isMine
  turnNotifyVisible.value = true
  turnNotifyKey.value++
  setTimeout(() => { turnNotifyVisible.value = false }, 1800)
}

const showAchievement = (name: string) => {
  achievementPopup.value = name
  achievementPopupKey.value++
  setTimeout(() => { achievementPopup.value = '' }, 3500)
}

const resetGameState = () => {
  currentCombo.value = 0
  playerScore.value = 0
  hintsUsed.value = 0
  hints.value = []
  rounds.value = []
  gameEnded.value = false
  multiResults.value = []
  singleResult.value = null
  scoreFloat.value = null
  expFloat.value = null
  chatMessages.value = []
  stopTurnTimer()
  turnTimeLeft.value = 0
  turnNotifyVisible.value = false
  achievementPopup.value = ''
  myReady.value = false
  allReady.value = false
}

const startSingleGame = async () => {
  loading.value = true
  resetGameState()
  gameMode.value = 'single'
  try {
    const room = await relayApi.createRoom({
      mode: 'single', difficulty: form.difficulty,
      max_rounds: form.max_rounds, time_limit: form.time_limit
    })
    currentRoomId.value = room.id
    await relayApi.startGame(room.id)
    const detail = await relayApi.getRoomDetail(room.id)
    gameState.value = detail
    nextChar.value = detail.next_char || ''
    currentRound.value = detail.current_round
    maxRounds.value = detail.max_rounds
    rounds.value = detail.rounds.map(r => ({
      user_id: r.user_id, username: r.username, verse: r.verse,
      poem_title: r.poem_title, author: r.author, score: r.score
    }))
    phase.value = 'playing'
    startTurnTimer()
    scrollToBottom()
  } catch (e: any) {
    showError(e.response?.data?.detail || '创建游戏失败')
  } finally {
    loading.value = false
  }
}

const createMultiRoom = async () => {
  loading.value = true
  resetGameState()
  try {
    const room = await relayApi.createRoom({
      mode: 'multi', difficulty: form.difficulty,
      max_rounds: form.max_rounds, time_limit: form.time_limit,
      max_players: form.max_players,
      password: form.password || undefined
    })
    currentRoomId.value = room.id
    currentRoomCode.value = room.room_code
    isHost.value = true
    wsMaxPlayers.value = form.max_players
    wsPlayers.value = [{
      user_id: userStore.userInfo!.id,
      username: userStore.userInfo!.username,
      avatar_url: userStore.userInfo!.avatar_url || null,
      is_host: true
    }]
    timeLimit.value = form.time_limit
    maxRounds.value = form.max_rounds
    setupWsHandlers()
    ws.connect(room.id)
    phase.value = 'waiting'
  } catch (e: any) {
    showError(e.response?.data?.detail || '创建房间失败')
  } finally {
    loading.value = false
  }
}

const joinLobbyRoom = async (roomCode: string, pwd?: string) => {
  loading.value = true
  resetGameState()
  try {
    const res = await relayApi.joinRoom(roomCode, pwd || undefined)
    const data = res.data || res
    currentRoomId.value = data.room_id
    currentRoomCode.value = roomCode
    isHost.value = false
    wsPlayers.value = data.players || []
    setupWsHandlers()
    ws.connect(data.room_id)
    phase.value = 'waiting'
  } catch (e: any) {
    showError(e.response?.data?.detail || '加入房间失败')
  } finally {
    loading.value = false
  }
}

const joinRoomByCode = () => {
  if (joinCode.value.trim()) {
    joinLobbyRoom(joinCode.value.trim().toUpperCase(), joinPassword.value || undefined)
  }
}

const handleJoinLobbyRoom = (room: any) => {
  if (room.has_password) {
    const pwd = prompt('请输入房间密码')
    if (pwd === null) return
    joinLobbyRoom(room.room_code, pwd)
  } else {
    joinLobbyRoom(room.room_code)
  }
}

const quickMatch = async () => {
  loading.value = true
  resetGameState()
  try {
    const room = await relayApi.quickMatch()
    currentRoomId.value = room.id
    currentRoomCode.value = room.room_code
    isHost.value = room.host_id === userStore.userInfo?.id
    wsMaxPlayers.value = room.max_players
    maxRounds.value = room.max_rounds
    timeLimit.value = room.time_limit
    const detail = await relayApi.getRoomDetail(room.id)
    wsPlayers.value = detail.players.map(p => ({
      user_id: p.user_id, username: p.username,
      avatar_url: p.avatar_url, is_host: p.is_host
    }))
    setupWsHandlers()
    ws.connect(room.id)
    phase.value = 'waiting'
  } catch (e: any) {
    showError(e.response?.data?.detail || '快速匹配失败')
  } finally {
    loading.value = false
  }
}

const loadLobby = async () => {
  try {
    const res = await relayApi.getLobby({ page: 1, page_size: 20 })
    lobbyRooms.value = res.items
  } catch {
  }
}

const copyRoomCode = async () => {
  try {
    await navigator.clipboard.writeText(currentRoomCode.value)
    codeCopied.value = true
    setTimeout(() => { codeCopied.value = false }, 2000)
  } catch {
  }
}

const toggleReady = () => {
  ws.setReady()
}

const kickPlayer = (targetUserId: number) => {
  ws.kick(targetUserId)
}

const leaveWaitingRoom = () => {
  ws.disconnect()
  phase.value = 'setup'
}

const sendChatMsg = () => {
  if (!chatInput.value.trim()) return
  ws.sendChat(chatInput.value.trim())
  chatInput.value = ''
}

const setupWsHandlers = () => {
  ws.on('player_joined', (msg: any) => {
    wsPlayers.value = msg.players
    wsMaxPlayers.value = msg.max_players
    chatMessages.value.push({ username: '', content: `${msg.username} 加入了房间`, system: true })
    scrollChatToBottom()
  })

  ws.on('player_left', (msg: any) => {
    wsPlayers.value = msg.players
    chatMessages.value.push({ username: '', content: `${msg.username} 离开了房间`, system: true })
    scrollChatToBottom()
  })

  ws.on('player_disconnected', (msg: any) => {
    wsPlayers.value = msg.players
    chatMessages.value.push({ username: '', content: `${msg.username} 断线${msg.can_reconnect ? '（等待重连）' : ''}`, system: true })
    scrollChatToBottom()
  })

  ws.on('player_reconnected', (msg: any) => {
    wsPlayers.value = msg.players
    chatMessages.value.push({ username: '', content: `${msg.username} 重新连接`, system: true })
    scrollChatToBottom()
  })

  ws.on('ready_changed', (msg: any) => {
    wsPlayers.value = msg.players
    allReady.value = msg.all_ready
    if (msg.user_id === userStore.userInfo?.id) {
      myReady.value = msg.is_ready
    }
  })

  ws.on('kicked', (_msg: any) => {
    showError('你被房主移出了房间')
    ws.disconnect()
    resetGameState()
    phase.value = 'setup'
  })

  ws.on('player_kicked', (msg: any) => {
    wsPlayers.value = msg.players
    chatMessages.value.push({ username: '', content: `${msg.username} 被房主移出了房间`, system: true })
    scrollChatToBottom()
  })

  ws.on('game_state_sync', (msg: any) => {
    phase.value = 'playing'
    gameMode.value = 'multi'
    nextChar.value = msg.next_char
    currentRound.value = msg.current_round
    maxRounds.value = msg.max_rounds
    timeLimit.value = msg.time_limit
    currentTurnUserId.value = msg.current_turn?.user_id
    currentTurnUsername.value = msg.current_turn?.username || ''
    wsPlayers.value = msg.players || []
    rounds.value = msg.rounds || []
    wsPlayersScores.value = msg.players_scores || []
    const myScore = wsPlayersScores.value.find(p => p.user_id === userStore.userInfo?.id)
    if (myScore) playerScore.value = myScore.score
    scrollToBottom()
    startTurnTimer()
    if (isMyTurn.value) {
      showTurnNotify(true)
      nextTick(() => verseInputRef.value?.focus())
    }
  })

  ws.on('chat', (msg: any) => {
    chatMessages.value.push({ username: msg.username, content: msg.content })
    scrollChatToBottom()
  })

  ws.on('game_started', (msg: any) => {
    phase.value = 'playing'
    gameMode.value = 'multi'
    nextChar.value = msg.next_char
    currentRound.value = msg.current_round
    maxRounds.value = msg.max_rounds
    timeLimit.value = msg.time_limit
    currentTurnUserId.value = msg.current_turn?.user_id
    currentTurnUsername.value = msg.current_turn?.username || ''
    wsPlayers.value = msg.players
    rounds.value = [{
      user_id: 0, username: '系统', verse: msg.starter_verse,
      poem_title: msg.starter_poem_title, author: msg.starter_author, score: 0
    }]
    wsPlayersScores.value = wsPlayers.value.map(p => ({
      user_id: p.user_id, username: p.username, score: 0,
      combo: 0, max_combo: 0, rounds_played: 0
    }))
    scrollToBottom()
    startTurnTimer()
    if (isMyTurn.value) {
      showTurnNotify(true)
      nextTick(() => verseInputRef.value?.focus())
    } else {
      showTurnNotify(false)
    }
  })

  ws.on('verse_accepted', (msg: any) => {
    rounds.value.push({
      user_id: msg.user_id, username: msg.username, verse: msg.verse,
      poem_title: msg.poem_title, author: msg.author, score: msg.score
    })
    nextChar.value = msg.next_char
    currentRound.value = msg.current_round
    if (msg.user_id === userStore.userInfo?.id) {
      currentCombo.value = msg.combo
      scoreFloat.value = msg.score
      scoreFloatKey.value++
      const roundExp = Math.floor(msg.score / 2)
      expFloat.value = roundExp
      expFloatKey.value++
      setTimeout(() => { scoreFloat.value = null; expFloat.value = null }, 1200)
    }
    if (msg.players_scores) {
      wsPlayersScores.value = msg.players_scores
      const myScore = msg.players_scores.find((p: WsPlayerScore) => p.user_id === userStore.userInfo?.id)
      if (myScore) playerScore.value = myScore.score
    }
    if (msg.next_turn) {
      currentTurnUserId.value = msg.next_turn.user_id
      currentTurnUsername.value = msg.next_turn.username
    }
    scrollToBottom()
    if (msg.game_finished) {
      stopTurnTimer()
    } else {
      startTurnTimer()
      const nextIsMine = msg.next_turn?.user_id === userStore.userInfo?.id
      showTurnNotify(nextIsMine)
      if (nextIsMine) {
        nextTick(() => verseInputRef.value?.focus())
      }
    }
  })

  ws.on('verse_invalid', (msg: any) => {
    showError(msg.message)
    currentCombo.value = 0
  })

  ws.on('turn_timeout', (msg: any) => {
    if (msg.user_id === userStore.userInfo?.id) {
      showError('回合超时')
      currentCombo.value = 0
    }
    currentTurnUserId.value = msg.next_turn?.user_id
    currentTurnUsername.value = msg.next_turn?.username || ''
    startTurnTimer()
    const nextIsMine = msg.next_turn?.user_id === userStore.userInfo?.id
    showTurnNotify(nextIsMine)
    if (nextIsMine) {
      nextTick(() => verseInputRef.value?.focus())
    }
  })

  ws.on('hint_response', (msg: any) => {
    hints.value = msg.hints
    hintsUsed.value = msg.hint_count_used
  })

  ws.on('game_ended', (msg: any) => {
    stopTurnTimer()
    gameEnded.value = true
    multiResults.value = msg.results || []
    const myResult = multiResults.value.find(r => r.user_id === userStore.userInfo?.id)
    if (myResult) {
      playerScore.value = myResult.total_score
    }
    if (msg.new_achievements?.length) {
      msg.new_achievements.forEach((a: string, i: number) => {
        setTimeout(() => showAchievement(a), i * 1500)
      })
    }
    userStore.fetchUserInfo()
  })

  ws.on('rematch_created', (msg: any) => {
    resetGameState()
    currentRoomId.value = msg.new_room_id
    currentRoomCode.value = msg.new_room_code
    wsPlayers.value = msg.players || []
    wsMaxPlayers.value = msg.max_players
    phase.value = 'waiting'
    chatMessages.value.push({ username: '', content: '房主发起了再来一局', system: true })
  })

  ws.on('error', (msg: any) => {
    showError(msg.message)
  })

  ws.on('connected', () => {
    wsConnectionStatus.value = 'connected'
  })

  ws.on('disconnected', () => {
    wsConnectionStatus.value = 'disconnected'
  })

  ws.on('reconnecting', () => {
    wsConnectionStatus.value = 'reconnecting'
  })
}

const wsStartGame = () => {
  ws.startGame()
}

const submitVerse = async () => {
  if (!inputVerse.value.trim() || submitting.value) return
  submitting.value = true
  hints.value = []

  if (isMultiMode.value) {
    ws.submitVerse(inputVerse.value.trim())
    inputVerse.value = ''
    submitting.value = false
    return
  }

  try {
    const res = await relayApi.submitVerse(currentRoomId.value, inputVerse.value.trim())
    currentCombo.value = res.combo
    scoreFloat.value = res.score
    scoreFloatKey.value++
    const roundExp = Math.floor(res.score / 2)
    expFloat.value = roundExp
    expFloatKey.value++
    setTimeout(() => { scoreFloat.value = null; expFloat.value = null }, 1200)
    playerScore.value += res.score
    inputVerse.value = ''
    nextTick(() => { verseInputRef.value?.focus() })
    const detail = await relayApi.getRoomDetail(currentRoomId.value)
    gameState.value = detail
    nextChar.value = detail.next_char || ''
    currentRound.value = detail.current_round
    rounds.value = detail.rounds.map(r => ({
      user_id: r.user_id, username: r.username, verse: r.verse,
      poem_title: r.poem_title, author: r.author, score: r.score
    }))
    scrollToBottom()
    if (detail.status === 'finished') {
      stopTurnTimer()
      await handleSingleGameEnd()
    } else {
      startTurnTimer()
    }
  } catch (e: any) {
    currentCombo.value = 0
    showError(e.response?.data?.detail || '接龙失败')
  } finally {
    submitting.value = false
  }
}

const requestHint = async () => {
  if (hintsUsed.value >= 3) return
  if (isMultiMode.value) {
    ws.requestHint()
    return
  }
  try {
    const res = await relayApi.getHint(currentRoomId.value)
    hints.value = res.hints
    hintsUsed.value = res.hint_count_used
  } catch (e: any) {
    showError(e.response?.data?.detail || '获取提示失败')
  }
}

const useHint = (hint: { verse: string }) => {
  inputVerse.value = hint.verse
  hints.value = []
}

const handleSingleGameEnd = async () => {
  try {
    const res = await relayApi.endGame(currentRoomId.value)
    singleResult.value = res
    gameEnded.value = true
    stopTurnTimer()
    if (res.new_achievements?.length) {
      res.new_achievements.forEach((a: string, i: number) => {
        setTimeout(() => showAchievement(a), i * 1500)
      })
    }
    await userStore.fetchUserInfo()
  } catch {
    const detail = await relayApi.getRoomDetail(currentRoomId.value)
    gameState.value = detail
  }
}

const quitGame = async () => {
  if (isMultiMode.value) {
    ws.endGame()
    return
  }
  try {
    const res = await relayApi.endGame(currentRoomId.value)
    singleResult.value = res
    gameEnded.value = true
    stopTurnTimer()
    if (res.new_achievements?.length) {
      res.new_achievements.forEach((a: string, i: number) => {
        setTimeout(() => showAchievement(a), i * 1500)
      })
    }
    await userStore.fetchUserInfo()
  } catch (e: any) {
    showError(e.response?.data?.detail || '结束失败')
  }
}

const requestRematch = () => {
  ws.rematch()
}

const restartGame = () => {
  if (isMultiMode.value) {
    ws.disconnect()
    resetGameState()
    phase.value = 'setup'
    gameMode.value = 'multi'
  } else {
    resetGameState()
    gameState.value = null
    startSingleGame()
  }
}

const backToSetup = () => {
  if (isMultiMode.value) {
    ws.disconnect()
  }
  resetGameState()
  gameState.value = null
  phase.value = 'setup'
}

watch(gameMode, (val) => {
  if (val === 'multi') {
    loadLobby()
  }
})

onMounted(() => {
})

onUnmounted(() => {
  ws.disconnect()
})
</script>

<style>
@import './styles/relay.css';
</style>
