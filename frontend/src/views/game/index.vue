<template>
  <div class="fhl-page">
    <div class="fhl-floating-petals">
      <div class="fhl-petal"></div>
      <div class="fhl-petal"></div>
      <div class="fhl-petal"></div>
      <div class="fhl-petal"></div>
      <div class="fhl-petal"></div>
    </div>
    <img :src="mountainBg" class="fhl-bg-mountains" alt="" />
    <img :src="cloudDeco" class="fhl-bg-cloud fhl-bg-cloud--left" alt="" />
    <img :src="cloudDeco" class="fhl-bg-cloud fhl-bg-cloud--right" alt="" />

    <div class="fhl-container">
      <div v-if="!gameStarted" class="fhl-welcome">
        <div class="fhl-welcome__header">
          <img :src="flowerIcon" class="fhl-welcome__icon" alt="" />
          <h1 class="fhl-welcome__title">飞花令</h1>
          <p class="fhl-welcome__subtitle">诗词对弈 · 以诗会友</p>
        </div>

        <div class="fhl-rules">
          <div class="fhl-rule-card">
            <img :src="scrollIcon" class="fhl-rule-card__icon" alt="" />
            <div class="fhl-rule-card__title">游戏规则</div>
            <div class="fhl-rule-card__desc">连续答对指定数量的诗句即可通关</div>
          </div>
          <div class="fhl-rule-card">
            <img :src="swordsIcon" class="fhl-rule-card__icon" alt="" />
            <div class="fhl-rule-card__title">闯关模式</div>
            <div class="fhl-rule-card__desc">选择难度，挑战你的诗词储备</div>
          </div>
          <div class="fhl-rule-card">
            <img :src="hourglassIcon" class="fhl-rule-card__icon" alt="" />
            <div class="fhl-rule-card__title">限时作答</div>
            <div class="fhl-rule-card__desc">每回合30秒，答错或超时即失败</div>
          </div>
        </div>

        <div class="fhl-keyword-setup">
          <div v-if="initialKeyword" class="fhl-kw-banner">
            <span class="fhl-kw-banner__label">来自诗词学堂的令字</span>
            <span class="fhl-kw-banner__char">{{ initialKeyword }}</span>
            <button type="button" class="fhl-kw-banner__clear" @click="initialKeyword = ''">清除</button>
          </div>
          <div v-else class="fhl-kw-custom-row">
            <label class="fhl-kw-custom__label">自定义令字</label>
            <input
              v-model="customKeywordInput"
              type="text"
              maxlength="1"
              class="fhl-kw-custom__input"
              placeholder="留空则随机"
            />
          </div>
        </div>

        <div class="fhl-difficulty">
          <div class="fhl-difficulty__label">选择难度</div>
          <div class="fhl-difficulty__options">
            <button
              v-for="d in difficulties"
              :key="d.value"
              class="fhl-diff-btn"
              :class="{ 'fhl-diff-btn--active': selectedDifficulty === d.value }"
              @click="selectedDifficulty = d.value"
            >
              {{ d.label }}
            </button>
          </div>
        </div>

        <button class="fhl-start-btn" @click="startNewGame" :disabled="isBusy">
          {{ startButtonLabel }}
        </button>

        <div v-if="history.length > 0" class="fhl-history">
          <div class="fhl-history__title">历史战绩</div>
          <div class="fhl-history__stats">
            <div class="fhl-stat">
              <span class="fhl-stat__value">{{ totalGames }}</span>
              <span class="fhl-stat__label">总场次</span>
            </div>
            <div class="fhl-stat">
              <span class="fhl-stat__value">{{ winRate }}%</span>
              <span class="fhl-stat__label">胜率</span>
            </div>
            <div class="fhl-stat">
              <span class="fhl-stat__value">{{ bestScore }}</span>
              <span class="fhl-stat__label">最高分</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="fhl-game">
        <div class="fhl-game-header">
          <div class="fhl-keyword">
            <span class="fhl-keyword__label">令字</span>
            <span class="fhl-keyword__char">{{ keyword }}</span>
          </div>
          <div class="fhl-game-meta">
            <div v-if="comboCount >= 2" class="fhl-combo" :class="{ 'fhl-combo--hot': comboCount >= 4 }">
              {{ comboCount }}连
            </div>
            <div class="fhl-meta-item">
              <span class="fhl-meta-item__label">进度</span>
              <span class="fhl-meta-item__value">{{ userRoundCount }}/{{ targetRounds }}</span>
            </div>
            <div class="fhl-meta-item fhl-meta-item--score">
              <span class="fhl-meta-item__label">我方</span>
              <span class="fhl-meta-item__value">{{ userScore }}</span>
              <span v-if="scoreFloat" class="fhl-score-float" :key="scoreFloat.id">+{{ scoreFloat.value }}</span>
            </div>
            <div class="fhl-meta-item fhl-meta-item--ai">
              <span class="fhl-meta-item__label">AI</span>
              <span class="fhl-meta-item__value">{{ aiScore }}</span>
            </div>
          </div>
        </div>

        <div class="fhl-progress">
          <div class="fhl-progress__bar" :style="{ width: progressPercent + '%' }"></div>
        </div>

        <div class="fhl-board">
          <div class="fhl-board__list" ref="roundsList">
            <div v-if="rounds.length === 0" class="fhl-board__empty">
              <img :src="inkBrushIcon" class="fhl-board__empty-icon" alt="" />
              <span class="fhl-board__empty-text">落笔之处，皆是诗意</span>
            </div>
            <template v-for="round in rounds" :key="round.round_number + '-' + round.player">
              <div
                class="fhl-round"
                :class="{
                  'fhl-round--correct': round.isNew,
                  'fhl-round--ai': round.player === 'ai'
                }"
              >
                <div class="fhl-round__header">
                  <span class="fhl-round__player" :class="{ 'fhl-round__player--ai': round.player === 'ai' }">
                    {{ round.player === 'ai' ? 'AI' : '我' }}
                  </span>
                  <span class="fhl-round__number">第 {{ round.round_number }} 回合</span>
                </div>
                <div class="fhl-round__content" v-html="highlightKeyword(round.poem_content)"></div>
                <div class="fhl-round__bottom">
                  <span v-if="round.author" class="fhl-round__meta">
                    {{ round.dynasty }} · {{ round.author }} · 《{{ round.title }}》
                  </span>
                  <span v-if="round.player === 'ai'" class="fhl-round__verified" :class="{ 'fhl-round__verified--ok': round.verified }">
                    {{ round.verified ? '典籍有据' : '待考' }}
                  </span>
                  <span v-if="round.scoreGained" class="fhl-round__score">+{{ round.scoreGained }}</span>
                </div>
              </div>
            </template>
            <div v-if="aiThinking" class="fhl-round fhl-round--ai fhl-round--thinking">
              <div class="fhl-round__header">
                <span class="fhl-round__player fhl-round__player--ai">AI</span>
                <span class="fhl-round__number">思索中...</span>
              </div>
              <div class="fhl-round__content fhl-thinking-dots">···</div>
            </div>
          </div>
        </div>

        <div class="fhl-input-area">
          <div class="fhl-timer" :class="{ 'fhl-timer--warning': timeLeft <= 10 }">
            <img :src="hourglassIcon" class="fhl-timer__icon" alt="" />
            <span class="fhl-timer__text">{{ timeLeft }}s</span>
            <div class="fhl-timer__bar" :style="{ width: `${(timeLeft / 30) * 100}%` }"></div>
          </div>

          <div class="fhl-input-row">
            <input
              ref="poemInputRef"
              v-model="userInput"
              type="text"
              class="fhl-poem-input"
              placeholder="请输入包含令字的诗句..."
              @keyup.enter="submitPoem"
              :disabled="inputDisabled"
            />
            <div class="fhl-action-btns">
              <button class="fhl-btn fhl-btn--hint" @click="getHint" :disabled="inputDisabled">
                <img :src="lanternIcon" class="fhl-btn__icon" alt="" />
                提示
              </button>
              <button class="fhl-btn fhl-btn--submit" @click="submitPoem" :disabled="!userInput.trim() || inputDisabled">
                {{ submitting ? '判定中...' : '提交' }}
              </button>
              <button class="fhl-btn fhl-btn--quit" @click="surrender" :disabled="inputDisabled">
                放弃
              </button>
            </div>
          </div>

          <div v-if="hintText" class="fhl-hint-display">
            <span class="fhl-hint-display__text">{{ hintText }}</span>
            <span class="fhl-hint-display__cost">-3</span>
          </div>
          <div v-if="errorMessage" class="fhl-error">{{ errorMessage }}</div>
        </div>
      </div>

      <div v-if="gameResult" class="fhl-result-overlay" @click.self="dismissResult">
        <div class="fhl-result">
          <img :src="sealIcon" class="fhl-result__seal" alt="" />
          <img
            v-if="gameResult.result === 'win'"
            :src="trophyIcon"
            class="fhl-result__icon fhl-result__icon--win"
            alt=""
          />
          <img
            v-else-if="gameResult.result === 'draw'"
            :src="sealIcon"
            class="fhl-result__icon fhl-result__icon--draw"
            alt=""
          />
          <img
            v-else
            :src="flowerIcon"
            class="fhl-result__icon fhl-result__icon--lose"
            alt=""
          />

          <h2 class="fhl-result__title" :class="{
            'fhl-result__title--win': gameResult.result === 'win',
            'fhl-result__title--lose': gameResult.result === 'lose',
            'fhl-result__title--draw': gameResult.result === 'draw'
          }">
            {{ gameResult.result === 'win' ? '诗才盖世' : gameResult.result === 'draw' ? '棋逢对手' : '来日方长' }}
          </h2>
          <p class="fhl-result__subtitle">
            {{ gameResult.user_score }} : {{ gameResult.ai_score }}
          </p>

          <div class="fhl-result__stats">
            <div class="fhl-result-stat">
              <span class="fhl-result-stat__label">通关进度</span>
              <span class="fhl-result-stat__value">{{ gameResult.user_round_count }}/{{ targetRounds }}</span>
            </div>
            <div class="fhl-result-stat">
              <span class="fhl-result-stat__label">我方得分</span>
              <span class="fhl-result-stat__value">{{ gameResult.user_score }}</span>
            </div>
            <div class="fhl-result-stat">
              <span class="fhl-result-stat__label">AI得分</span>
              <span class="fhl-result-stat__value">{{ gameResult.ai_score }}</span>
            </div>
            <div class="fhl-result-stat">
              <span class="fhl-result-stat__label">用时</span>
              <span class="fhl-result-stat__value">{{ formatDuration(gameResult.duration) }}</span>
            </div>
          </div>

          <div v-if="gameResult.rounds && gameResult.rounds.length > 0" class="fhl-result__rounds">
            <div
              v-for="r in gameResult.rounds"
              :key="r.round_number + '-' + r.player"
              class="fhl-result__round-item"
              :class="{ 'fhl-result__round-item--ai': r.player === 'ai' }"
            >
              <span class="fhl-result__round-tag" :class="{ 'fhl-result__round-tag--ai': r.player === 'ai' }">
                {{ r.player === 'ai' ? 'AI' : '我' }}
              </span>
              <span class="fhl-result__round-poem">{{ r.poem_content }}</span>
              <span v-if="r.author" class="fhl-result__round-source">{{ r.author }}</span>
            </div>
          </div>

          <div class="fhl-result__cross">
            <router-link v-if="fromPoemId" :to="`/poems/${fromPoemId}`" class="fhl-cross-link">返回《{{ fromPoemTitle }}》</router-link>
            <router-link to="/poems" class="fhl-cross-link">去诗词课堂研读</router-link>
            <router-link to="/challenge" class="fhl-cross-link">妙笔挑战</router-link>
            <router-link to="/works/create" class="fhl-cross-link">去创作一首</router-link>
          </div>

          <div class="fhl-result__actions">
            <button class="fhl-result-btn fhl-result-btn--primary" @click="startNewGame" :disabled="isBusy">
              {{ loading ? '准备中...' : '再来一局' }}
            </button>
            <button class="fhl-result-btn" @click="backToHome" :disabled="isBusy">返回</button>
          </div>
        </div>
      </div>

      <div v-if="blockingMessage" class="fhl-state-layer">
        <div class="fhl-state-layer__panel">
          <span class="fhl-state-layer__spinner"></span>
          <div class="fhl-state-layer__title">{{ blockingMessage }}</div>
          <div class="fhl-state-layer__desc">{{ blockingSubMessage }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { feiHuaLingApi, type GameResult as GameResultType, type RoundHistory } from '@/api/feihualing'
import { ElMessage } from 'element-plus'

import flowerIcon from '@/assets/icons/feihualing/flower-petal.svg'
import scrollIcon from '@/assets/icons/feihualing/scroll-rules.svg'
import swordsIcon from '@/assets/icons/feihualing/crossed-swords.svg'
import hourglassIcon from '@/assets/icons/feihualing/hourglass.svg'
import lanternIcon from '@/assets/icons/feihualing/lantern-hint.svg'
import trophyIcon from '@/assets/icons/feihualing/trophy-win.svg'
import sealIcon from '@/assets/icons/feihualing/seal-stamp.svg'
import inkBrushIcon from '@/assets/icons/feihualing/ink-brush.svg'
import mountainBg from '@/assets/icons/feihualing/mountain-bg.svg'
import cloudDeco from '@/assets/icons/feihualing/cloud-deco.svg'

interface ExtendedRound extends RoundHistory {
  isNew?: boolean
  scoreGained?: number
  verified?: boolean
}

const route = useRoute()
const initialKeyword = ref((route.query.keyword as string) || '')
const customKeywordInput = ref('')
const fromPoemId = ref((route.query.from_poem as string) || '')
const fromPoemTitle = ref((route.query.from_title as string) || '')

const difficulties = [
  { value: 5, label: '初阶 · 5关' },
  { value: 10, label: '进阶 · 10关' },
  { value: 15, label: '大家 · 15关' }
]

const gameStarted = ref(false)
const loading = ref(false)
const submitting = ref(false)
const gameId = ref('')
const keyword = ref('')
const userScore = ref(0)
const aiScore = ref(0)
const roundNumber = ref(0)
const userRoundCount = ref(0)
const targetRounds = ref(10)
const rounds = ref<ExtendedRound[]>([])
const userInput = ref('')
const timeLeft = ref(30)
const errorMessage = ref('')
const hintText = ref('')
const comboCount = ref(0)
const aiThinking = ref(false)
const scoreFloat = ref<{ value: number; id: number } | null>(null)
const gameResult = ref<GameResultType | null>(null)
const history = ref<any[]>([])
const roundsList = ref<HTMLElement>()
const poemInputRef = ref<HTMLInputElement>()
const selectedDifficulty = ref(10)

const effectiveKeyword = computed(() => {
  if (initialKeyword.value) return initialKeyword.value
  if (customKeywordInput.value.trim()) return customKeywordInput.value.trim()
  return ''
})

const startBtnText = computed(() => {
  if (effectiveKeyword.value) return `以「${effectiveKeyword.value}」开始闯关`
  return '开始闯关'
})
const isBusy = computed(() => loading.value || submitting.value)
const inputDisabled = computed(() => !!gameResult.value || isBusy.value)
const startButtonLabel = computed(() => loading.value ? '准备中...' : startBtnText.value)
const blockingMessage = computed(() => {
  if (loading.value) return '飞花令铺陈中'
  if (submitting.value) return '判卷与接句中'
  return ''
})
const blockingSubMessage = computed(() => {
  if (loading.value) return '正在抽取令字、布置首局'
  if (submitting.value) return '已停表，正在校验诗句并等待 AI 回合'
  return ''
})

let timer: ReturnType<typeof setInterval> | null = null
let errorTimer: ReturnType<typeof setTimeout> | null = null
let floatId = 0

const totalGames = computed(() => history.value.length)
const winRate = computed(() => {
  if (totalGames.value === 0) return 0
  const wins = history.value.filter(g => g.result === 'win').length
  return Math.round((wins / totalGames.value) * 100)
})
const bestScore = computed(() => {
  if (history.value.length === 0) return 0
  return Math.max(...history.value.map(g => g.user_score || 0))
})

const progressPercent = computed(() => {
  if (targetRounds.value === 0) return 0
  return Math.round((userRoundCount.value / targetRounds.value) * 100)
})

const showError = (msg: string) => {
  errorMessage.value = msg
  if (errorTimer) clearTimeout(errorTimer)
  errorTimer = setTimeout(() => { errorMessage.value = '' }, 4000)
}

const showScoreFloat = (gained: number) => {
  floatId++
  scoreFloat.value = { value: gained, id: floatId }
  setTimeout(() => {
    if (scoreFloat.value?.id === floatId) scoreFloat.value = null
  }, 1200)
}

const highlightKeyword = (text: string): string => {
  if (!keyword.value) return text
  const escaped = keyword.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return text.replace(
    new RegExp(escaped, 'g'),
    `<span class="fhl-round__keyword">${keyword.value}</span>`
  )
}

const formatDuration = (seconds: number): string => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

const startNewGame = async () => {
  if (isBusy.value) return
  try {
    loading.value = true
    gameResult.value = null
    errorMessage.value = ''
    hintText.value = ''
    stopTimer()
    const kw = effectiveKeyword.value || undefined
    initialKeyword.value = ''
    customKeywordInput.value = ''
    const response = await feiHuaLingApi.startGame(selectedDifficulty.value, kw)
    gameId.value = response.game_id
    keyword.value = response.keyword
    targetRounds.value = response.target_rounds
    gameStarted.value = true
    userScore.value = 0
    aiScore.value = 0
    roundNumber.value = 0
    userRoundCount.value = 0
    rounds.value = []
    userInput.value = ''
    comboCount.value = 0
    aiThinking.value = false

    if (response.ai_first_round) {
      const ai = response.ai_first_round
      aiThinking.value = true
      await nextTick()

      await new Promise(resolve => setTimeout(resolve, 600))
      aiThinking.value = false

      rounds.value.push({
        round_number: ai.round_number,
        player: 'ai',
        poem_content: ai.verse,
        author: ai.author,
        title: ai.poem_title,
        dynasty: ai.dynasty,
        created_at: new Date().toISOString(),
        isNew: true,
        verified: ai.verified
      })
      aiScore.value = response.ai_score
      roundNumber.value = ai.round_number

      setTimeout(() => {
        const r = rounds.value.find(x => x.round_number === ai.round_number && x.player === 'ai')
        if (r) r.isNew = false
      }, 800)

      await nextTick()
      scrollToBottom()
    }

    startTimer()
    await nextTick()
    poemInputRef.value?.focus()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '开始游戏失败')
  } finally {
    loading.value = false
  }
}

const startTimer = () => {
  timeLeft.value = 30
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    timeLeft.value--
    if (timeLeft.value <= 0) {
      handleTimeout()
    }
  }, 1000)
}

const stopTimer = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

const handleTimeout = () => {
  stopTimer()
  comboCount.value = 0
  endGame('timeout')
}

const submitPoem = async () => {
  if (!userInput.value.trim() || submitting.value) return

  const responseTime = 30 - timeLeft.value
  errorMessage.value = ''
  hintText.value = ''
  stopTimer()
  submitting.value = true

  try {
    const response = await feiHuaLingApi.submitPoem({
      game_id: gameId.value,
      poem_content: userInput.value.trim(),
      response_time: responseTime,
      target_rounds: targetRounds.value
    })

    if (!response.valid) {
      showError(response.message)
      comboCount.value = 0
      startTimer()
      await nextTick()
      poemInputRef.value?.focus()
      return
    }

    comboCount.value = response.combo
    userRoundCount.value = response.user_round_count

    const userRoundNum = response.round_number
    rounds.value.push({
      round_number: userRoundNum,
      player: 'user',
      poem_content: userInput.value.trim(),
      author: response.poem_author,
      title: response.poem_title,
      dynasty: response.poem_dynasty,
      created_at: new Date().toISOString(),
      isNew: true,
      scoreGained: response.score_gained
    })

    setTimeout(() => {
      const r = rounds.value.find(x => x.round_number === userRoundNum && x.player === 'user')
      if (r) r.isNew = false
    }, 600)

    if (response.score_gained > 0) {
      showScoreFloat(response.score_gained)
    }

    userScore.value = response.user_score
    aiScore.value = response.ai_score
    roundNumber.value = response.round_number
    userInput.value = ''

    await nextTick()
    scrollToBottom()

    if (!response.continue_game) {
      await endGame('win')
      return
    }

    aiThinking.value = true
    await nextTick()
    scrollToBottom()

    await new Promise(resolve => setTimeout(resolve, 800))

    aiThinking.value = false

    if (response.ai_round) {
      const ai = response.ai_round
      rounds.value.push({
        round_number: ai.round_number,
        player: 'ai',
        poem_content: ai.verse,
        author: ai.author,
        title: ai.poem_title,
        dynasty: ai.dynasty,
        created_at: new Date().toISOString(),
        isNew: true,
        verified: ai.verified
      })
      roundNumber.value = ai.round_number
      aiScore.value = response.ai_score

      setTimeout(() => {
        const r = rounds.value.find(x => x.round_number === ai.round_number && x.player === 'ai')
        if (r) r.isNew = false
      }, 800)

      await nextTick()
      scrollToBottom()
    } else if (response.ai_failed) {
      showError('AI词穷了，轮到你继续！')
    }

    poemInputRef.value?.focus()
    startTimer()
  } catch (error: any) {
    showError(error.response?.data?.detail || '提交失败')
    startTimer()
  } finally {
    submitting.value = false
  }
}

const getHint = async () => {
  try {
    errorMessage.value = ''
    const response = await feiHuaLingApi.getHint(gameId.value)
    hintText.value = `${response.hint} —— ${response.author}`
    if (response.hint_cost > 0) {
      userScore.value = Math.max(0, userScore.value - response.hint_cost)
    }
  } catch (error: any) {
    showError(error.response?.data?.detail || '获取提示失败')
  }
}

const surrender = async () => {
  stopTimer()
  comboCount.value = 0
  await endGame('surrender')
}

const endGame = async (reason: string) => {
  try {
    const result = await feiHuaLingApi.endGame({
      game_id: gameId.value,
      reason
    })
    gameResult.value = result
    await loadHistory()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '结束游戏失败')
  }
}

const dismissResult = () => {
  backToHome()
}

const backToHome = () => {
  gameStarted.value = false
  gameResult.value = null
  stopTimer()
}

const scrollToBottom = () => {
  if (roundsList.value) {
    roundsList.value.scrollTop = roundsList.value.scrollHeight
  }
}

const loadHistory = async () => {
  try {
    const response = await feiHuaLingApi.getHistory({ page: 1, page_size: 10 })
    history.value = response.items
  } catch (error) {
    console.error('加载历史失败:', error)
  }
}

onMounted(() => {
  loadHistory()
})

onUnmounted(() => {
  stopTimer()
  if (errorTimer) clearTimeout(errorTimer)
})
</script>

<style>
@import './styles/feihualing.css';

.fhl-state-layer {
  position: fixed;
  inset: 0;
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at top, rgba(255, 248, 239, 0.2), transparent 42%),
    rgba(18, 17, 16, 0.52);
  backdrop-filter: blur(8px);
  animation: fhl-fade-in 0.24s ease;
}

.fhl-state-layer__panel {
  width: min(360px, 100%);
  padding: 28px 24px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 251, 245, 0.94), rgba(246, 240, 231, 0.9));
  box-shadow: 0 24px 70px rgba(18, 17, 16, 0.22);
  text-align: center;
}

.fhl-state-layer__spinner {
  width: 48px;
  height: 48px;
  margin: 0 auto 18px;
  display: block;
  border: 2px solid rgba(18, 17, 16, 0.1);
  border-top-color: var(--color-vermilion);
  border-right-color: var(--color-gold);
  border-radius: 50%;
  animation: fhl-rotate 0.9s linear infinite;
}

.fhl-state-layer__title {
  font-family: var(--font-poem);
  font-size: 26px;
  letter-spacing: 3px;
  color: var(--color-ink-dark);
}

.fhl-state-layer__desc {
  margin-top: 8px;
  font-size: 13px;
  letter-spacing: 1px;
  color: var(--color-ink-medium);
}

.fhl-result-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@keyframes fhl-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
