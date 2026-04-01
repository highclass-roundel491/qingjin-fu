<template>
  <div class="tc-page">
    <div class="tc-deco tc-deco--orb-left"></div>
    <div class="tc-deco tc-deco--orb-right"></div>
    <div class="tc-deco tc-deco--ink-top"></div>
    <div class="tc-deco tc-deco--ink-bottom"></div>
    <div class="tc-container">
      <nav class="tc-nav">
        <router-link to="/games" class="tc-back">&larr; 返回游戏</router-link>
        <div class="tc-nav-links">
          <router-link to="/games/timed/history" class="tc-nav-link">历史</router-link>
          <router-link to="/games/timed/rankings" class="tc-nav-link">排行</router-link>
        </div>
      </nav>

      <div v-if="phase === 'welcome'" class="tc-welcome">
        <div class="tc-welcome__header">
          <img :src="hourglassIcon" class="tc-welcome__icon" alt="" />
          <h1 class="tc-welcome__title">限时挑战</h1>
          <p class="tc-welcome__subtitle">博闻强识 · 分秒必争</p>
        </div>

        <div class="tc-rules">
          <div class="tc-rule-card">
            <img :src="scrollIcon" class="tc-rule-card__icon" alt="" />
            <div class="tc-rule-card__title">知识问答</div>
            <div class="tc-rule-card__desc">从诗词库随机出题，考查诗句补全、作者判断等</div>
          </div>
          <div class="tc-rule-card">
            <img :src="lightningIcon" class="tc-rule-card__icon" alt="" />
            <div class="tc-rule-card__title">限时作答</div>
            <div class="tc-rule-card__desc">每题限时，答得越快分数越高</div>
          </div>
          <div class="tc-rule-card">
            <img :src="trophyIcon" class="tc-rule-card__icon" alt="" />
            <div class="tc-rule-card__title">连击加分</div>
            <div class="tc-rule-card__desc">连续答对获得额外加分，挑战最高连击</div>
          </div>
        </div>

        <div class="tc-setup">
          <div class="tc-setup__row">
            <div class="tc-setup__label">难度选择</div>
            <div class="tc-setup__options">
              <button
                v-for="d in difficultyOptions"
                :key="d.value"
                class="tc-opt-btn"
                :class="{ 'tc-opt-btn--active': form.difficulty === d.value }"
                @click="form.difficulty = d.value"
              >{{ d.label }}</button>
            </div>
          </div>
          <div class="tc-setup__row">
            <div class="tc-setup__label">题目数量</div>
            <div class="tc-setup__options">
              <button
                v-for="c in countOptions"
                :key="c"
                class="tc-opt-btn"
                :class="{ 'tc-opt-btn--active': form.question_count === c }"
                @click="form.question_count = c"
              >{{ c }}题</button>
            </div>
          </div>
          <div class="tc-setup__row">
            <div class="tc-setup__label">题型</div>
            <div class="tc-setup__options">
              <button
                v-for="t in typeOptions"
                :key="t.value"
                class="tc-opt-btn"
                :class="{ 'tc-opt-btn--active': form.question_type === t.value }"
                @click="form.question_type = t.value"
              >{{ t.label }}</button>
            </div>
          </div>
        </div>

        <button class="tc-start-btn" @click="startGame" :disabled="loading">
          {{ loading ? '准备中...' : '开始挑战' }}
        </button>

        <div v-if="historyStats.total_games > 0" class="tc-history-preview">
          <div class="tc-stat-mini">
            <span class="tc-stat-mini__value">{{ historyStats.total_games }}</span>
            <span class="tc-stat-mini__label">总场次</span>
          </div>
          <div class="tc-stat-mini">
            <span class="tc-stat-mini__value">{{ historyStats.best_score }}</span>
            <span class="tc-stat-mini__label">最高分</span>
          </div>
          <div class="tc-stat-mini">
            <span class="tc-stat-mini__value">{{ historyStats.best_accuracy }}%</span>
            <span class="tc-stat-mini__label">最佳正确率</span>
          </div>
        </div>
      </div>

      <div v-if="phase === 'playing'" class="tc-game">
        <div class="tc-game-header">
          <div class="tc-game-meta">
            <div class="tc-meta-item">
              <span class="tc-meta-item__label">进度</span>
              <span class="tc-meta-item__value">{{ answeredCount + 1 }}/{{ totalQuestions }}</span>
            </div>
            <div class="tc-meta-item tc-meta-item--score">
              <span class="tc-meta-item__label">得分</span>
              <span class="tc-meta-item__value">{{ totalScore }}</span>
            </div>
            <div class="tc-meta-item">
              <span class="tc-meta-item__label">正确</span>
              <span class="tc-meta-item__value">{{ correctCount }}</span>
            </div>
          </div>
          <div v-if="combo >= 2" class="tc-combo" :class="{ 'tc-combo--hot': combo >= 4 }">
            {{ combo }}连击
          </div>
        </div>

        <div class="tc-timer-bar">
          <div
            class="tc-timer-bar__fill"
            :class="{ 'tc-timer-bar__fill--warning': timeLeft <= 5 }"
            :style="{ width: timerPercent + '%' }"
          ></div>
        </div>

        <div v-if="currentQuestion" class="tc-question-card" :key="currentQuestion.index">
          <div class="tc-question-card__badge">{{ questionTypeLabel }}</div>
          <div class="tc-question-card__timer" :class="{ 'tc-question-card__timer--warning': timeLeft <= 5 }">
            <img :src="hourglassIcon" class="tc-question-card__timer-icon" alt="" />
            <span>{{ timeLeft }}s</span>
          </div>
          <div class="tc-question-card__text">{{ currentQuestion.question_text }}</div>

          <div v-if="currentQuestion.hint && !selectedAnswer" class="tc-hint-area">
            <button v-if="!hintRevealed" class="tc-hint-btn" @click="revealHint">
              <span class="tc-hint-btn__icon">💡</span>
              <span>查看提示</span>
            </button>
            <div v-else class="tc-hint-text">{{ currentQuestion.hint }}</div>
          </div>

          <div class="tc-options">
            <button
              v-for="opt in currentQuestion.options"
              :key="opt.key"
              class="tc-option"
              :class="optionClass(opt.key)"
              :disabled="!!selectedAnswer"
              @click="selectOption(opt.key)"
            >
              <span class="tc-option__key">{{ opt.key }}</span>
              <span class="tc-option__text">{{ opt.text }}</span>
            </button>
          </div>
        </div>

        <div v-if="feedback" class="tc-feedback" :class="feedback.correct ? 'tc-feedback--correct' : 'tc-feedback--wrong'">
          <div class="tc-feedback__title">{{ feedback.correct ? '答对了' : '答错了' }}</div>
          <div class="tc-feedback__detail">正确答案：{{ feedback.correctAnswer }}</div>
          <div v-if="feedback.poemTitle" class="tc-feedback__source">
            {{ feedback.poemAuthor }} · 《{{ feedback.poemTitle }}》
          </div>
          <div v-if="feedback.poemContent" class="tc-feedback__poem">
            <div v-for="(line, li) in feedback.poemContent.split('\n').filter((l: string) => l.trim())" :key="li" class="tc-feedback__poem-line">{{ line.trim() }}</div>
          </div>
          <div v-if="feedback.score > 0" class="tc-feedback__score">+{{ feedback.score }}分</div>
        </div>

        <div v-if="feedback && !gameFinished" class="tc-auto-next">
          {{ autoNextCountdown }}s 后自动下一题
          <button class="tc-next-btn" @click="goNext">立即下一题</button>
        </div>
        <button v-if="!feedback" class="tc-quit-btn" @click="quitGame">
          放弃挑战
        </button>
      </div>

      <div v-if="phase === 'result' && result" class="tc-result-overlay" @click.self="backToWelcome">
        <div class="tc-result">
          <img :src="trophyIcon" class="tc-result__icon" alt="" />
          <h2 class="tc-result__title">{{ resultTitle }}</h2>

          <div class="tc-result__stats">
            <div class="tc-result-stat">
              <span class="tc-result-stat__label">正确率</span>
              <span class="tc-result-stat__value">{{ result.accuracy }}%</span>
            </div>
            <div class="tc-result-stat">
              <span class="tc-result-stat__label">总分</span>
              <span class="tc-result-stat__value">{{ result.total_score }}</span>
            </div>
            <div class="tc-result-stat">
              <span class="tc-result-stat__label">最高连击</span>
              <span class="tc-result-stat__value">{{ result.max_combo }}</span>
            </div>
            <div class="tc-result-stat">
              <span class="tc-result-stat__label">用时</span>
              <span class="tc-result-stat__value">{{ formatDuration(result.duration) }}</span>
            </div>
          </div>

          <div v-if="result.exp_gained > 0" class="tc-result__exp">
            获得经验 +{{ result.exp_gained }}
          </div>

          <div v-if="result.answers && result.answers.length > 0" class="tc-result__answers">
            <div
              v-for="a in result.answers"
              :key="a.index"
              class="tc-result__answer-item"
            >
              <span class="tc-result__answer-num">{{ a.index + 1 }}.</span>
              <span class="tc-result__answer-text">{{ a.question_text }}</span>
              <span
                class="tc-result__answer-mark"
                :class="a.is_correct ? 'tc-result__answer-mark--correct' : 'tc-result__answer-mark--wrong'"
              >{{ a.is_correct ? '+' + a.score : 'x' }}</span>
            </div>
          </div>

          <div class="tc-result__cross">
            <router-link to="/poems" class="tc-cross-link">去诗词课堂研读</router-link>
            <router-link to="/challenge" class="tc-cross-link">妙笔挑战</router-link>
            <router-link to="/works/create" class="tc-cross-link">去创作一首</router-link>
          </div>

          <div class="tc-result__actions">
            <button class="tc-result-btn tc-result-btn--primary" @click="startGame">再来一局</button>
            <button class="tc-result-btn" @click="backToWelcome">返回</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { timedChallengeApi, type TimedQuestion, type TimedChallengeResult } from '@/api/timed-challenge'
import { useUserStore } from '@/store/modules/user'
import { ElMessage } from 'element-plus'

import hourglassIcon from '@/assets/icons/timed/hourglass-timer.svg'
import lightningIcon from '@/assets/icons/timed/lightning-bolt.svg'
import scrollIcon from '@/assets/icons/timed/scroll-question.svg'
import trophyIcon from '@/assets/icons/timed/trophy-result.svg'

const userStore = useUserStore()

const difficultyOptions = [
  { value: 'easy', label: '初阶 · 20s' },
  { value: 'medium', label: '进阶 · 15s' },
  { value: 'hard', label: '大家 · 10s' },
]
const countOptions = [5, 10, 15, 20]
const typeOptions = [
  { value: 'mixed', label: '综合' },
  { value: 'fill_verse', label: '诗句补全' },
  { value: 'author_guess', label: '作者判断' },
  { value: 'verse_match', label: '对句匹配' },
]

const typeLabels: Record<string, string> = {
  fill_verse: '诗句补全',
  author_guess: '作者判断',
  verse_match: '对句匹配',
  mixed: '综合',
}

const form = ref({
  difficulty: 'medium',
  question_count: 10,
  question_type: 'mixed',
})

const phase = ref<'welcome' | 'playing' | 'result'>('welcome')
const loading = ref(false)
const sessionId = ref(0)
const totalQuestions = ref(10)
const timePerQuestion = ref(15)
const currentQuestion = ref<TimedQuestion | null>(null)
const selectedAnswer = ref<string | null>(null)
const hintRevealed = ref(false)
const feedback = ref<{
  correct: boolean
  correctAnswer: string
  score: number
  poemTitle?: string
  poemAuthor?: string
  poemContent?: string
} | null>(null)
const answeredCount = ref(0)
const correctCount = ref(0)
const totalScore = ref(0)
const combo = ref(0)
const timeLeft = ref(15)
const gameFinished = ref(false)
const result = ref<TimedChallengeResult | null>(null)
const historyStats = ref({ total_games: 0, best_score: 0, best_accuracy: 0 })

let timer: ReturnType<typeof setInterval> | null = null
let autoNextTimer: ReturnType<typeof setTimeout> | null = null
let autoNextCountdownTimer: ReturnType<typeof setInterval> | null = null
let questionStartTime = 0
const autoNextCountdown = ref(2)
const pendingQuestion = ref<TimedQuestion | null>(null)

const timerPercent = computed(() => {
  if (timePerQuestion.value === 0) return 100
  return Math.max(0, (timeLeft.value / timePerQuestion.value) * 100)
})

const questionTypeLabel = computed(() => {
  if (!currentQuestion.value) return ''
  return typeLabels[currentQuestion.value.question_type] || currentQuestion.value.question_type
})

const resultTitle = computed(() => {
  if (!result.value) return ''
  if (result.value.accuracy >= 80) return '博闻强识'
  if (result.value.accuracy >= 60) return '学有所成'
  if (result.value.accuracy >= 40) return '初窥门径'
  return '来日方长'
})

const optionClass = (key: string) => {
  if (!selectedAnswer.value) return {}
  const isSelected = selectedAnswer.value === key
  const isCorrect = feedback.value && key === getCorrectKey()
  return {
    'tc-option--selected': isSelected && !feedback.value,
    'tc-option--correct': feedback.value && isCorrect,
    'tc-option--wrong': feedback.value && isSelected && !feedback.value?.correct,
    'tc-option--disabled': !!selectedAnswer.value,
  }
}

const getCorrectKey = () => {
  if (!feedback.value || !currentQuestion.value) return ''
  const opt = currentQuestion.value.options.find(o => o.text === feedback.value!.correctAnswer)
  return opt?.key || ''
}

const formatDuration = (seconds: number): string => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

const startTimer = () => {
  stopTimer()
  timeLeft.value = timePerQuestion.value
  questionStartTime = Date.now()
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
  if (!selectedAnswer.value) {
    submitAnswer('TIMEOUT')
  }
}

const loadHistory = async () => {
  try {
    const res = await timedChallengeApi.getHistory({ page: 1, page_size: 1 })
    historyStats.value = {
      total_games: res.total_games,
      best_score: res.best_score,
      best_accuracy: res.best_accuracy,
    }
  } catch {
    // ignore
  }
}

const startGame = async () => {
  try {
    loading.value = true
    feedback.value = null
    selectedAnswer.value = null
    hintRevealed.value = false
    gameFinished.value = false
    result.value = null
    pendingQuestion.value = null

    const res = await timedChallengeApi.start({
      difficulty: form.value.difficulty,
      question_count: form.value.question_count,
      question_type: form.value.question_type,
    })

    sessionId.value = res.session_id
    totalQuestions.value = res.total_questions
    timePerQuestion.value = res.time_per_question
    currentQuestion.value = res.first_question
    answeredCount.value = 0
    correctCount.value = 0
    totalScore.value = 0
    combo.value = 0

    phase.value = 'playing'
    startTimer()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '开始挑战失败')
  } finally {
    loading.value = false
  }
}

const selectOption = (key: string) => {
  if (selectedAnswer.value) return
  selectedAnswer.value = key
  stopTimer()
  submitAnswer(key)
}

const submitAnswer = async (answer: string) => {
  const timeSpent = Math.round((Date.now() - questionStartTime) / 1000)
  try {
    const res = await timedChallengeApi.answer({
      session_id: sessionId.value,
      question_index: currentQuestion.value!.index,
      answer: answer,
      time_spent: timeSpent,
    })

    if (answer === 'TIMEOUT') {
      selectedAnswer.value = 'TIMEOUT'
    }

    feedback.value = {
      correct: res.is_correct,
      correctAnswer: res.correct_answer,
      score: res.score_gained,
      poemTitle: res.poem_title,
      poemAuthor: res.poem_author,
      poemContent: res.poem_content,
    }

    totalScore.value = res.total_score
    correctCount.value = res.correct_count
    answeredCount.value = res.answered_count
    combo.value = res.combo

    if (res.is_finished) {
      gameFinished.value = true
      setTimeout(() => showResult(), 1500)
    } else if (res.next_question) {
      pendingQuestion.value = res.next_question
      scheduleAutoNext()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交答案失败')
  }
}

const clearAutoNext = () => {
  if (autoNextTimer) { clearTimeout(autoNextTimer); autoNextTimer = null }
  if (autoNextCountdownTimer) { clearInterval(autoNextCountdownTimer); autoNextCountdownTimer = null }
}

const scheduleAutoNext = () => {
  clearAutoNext()
  autoNextCountdown.value = 2
  autoNextCountdownTimer = setInterval(() => {
    autoNextCountdown.value = Math.max(0, autoNextCountdown.value - 1)
  }, 1000)
  autoNextTimer = setTimeout(() => {
    clearAutoNext()
    goNext()
  }, 2000)
}

const revealHint = () => {
  hintRevealed.value = true
}

const goNext = () => {
  clearAutoNext()
  if (pendingQuestion.value) {
    currentQuestion.value = pendingQuestion.value
    pendingQuestion.value = null
  }
  feedback.value = null
  selectedAnswer.value = null
  hintRevealed.value = false
  startTimer()
}

const showResult = async () => {
  try {
    const res = await timedChallengeApi.end(sessionId.value)
    result.value = res
    phase.value = 'result'
    stopTimer()
    await userStore.fetchUserInfo()
    await loadHistory()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取结果失败')
  }
}

const quitGame = async () => {
  stopTimer()
  await showResult()
}

const backToWelcome = () => {
  phase.value = 'welcome'
  result.value = null
  feedback.value = null
  selectedAnswer.value = null
  pendingQuestion.value = null
  gameFinished.value = false
  stopTimer()
  clearAutoNext()
}

onMounted(() => {
  loadHistory()
})

onUnmounted(() => {
  stopTimer()
  clearAutoNext()
})
</script>

<style>
@import './styles/timed-challenge.css';
</style>
