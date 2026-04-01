<template>
  <div class="rankings-page">
    <div class="ink-bg">
      <div class="ink-wash ink-wash--1"></div>
      <div class="ink-wash ink-wash--2"></div>
      <div class="ink-wash ink-wash--3"></div>
    </div>

    <nav class="page-nav">
      <router-link to="/works" class="nav-back">返回作品墙</router-link>
      <span class="nav-title">创作排行榜</span>
      <div class="nav-right-placeholder"></div>
    </nav>

    <main class="page-body">
      <div class="ranking-hero">
        <div class="hero-ornament"></div>
        <div class="hero-seal-panel">
          <img :src="rankSealIcon" alt="排行榜印记" class="hero-seal-image" />
          <p class="hero-kicker">诗词创作排行榜</p>
        </div>
        <div class="hero-copy">
          <div class="hero-title-row">
            <h1 class="hero-title">{{ currentBoard.title }}</h1>
            <div class="hero-divider"></div>
          </div>
          <p class="hero-subtitle">{{ currentBoard.hint }}</p>
        </div>
      </div>

      <div class="board-switcher">
        <button
          v-for="board in boardTabs"
          :key="board.value"
          type="button"
          class="board-switcher__tab"
          :class="{ 'board-switcher__tab--active': activeBoard === board.value }"
          @click="switchBoard(board.value)"
        >
          <img :src="board.icon" alt="" aria-hidden="true" class="board-switcher__icon" />
          <span class="board-switcher__content">
            <span class="board-switcher__label">{{ board.label }}</span>
            <span class="board-switcher__hint">{{ board.hint }}</span>
          </span>
        </button>
      </div>

      <section class="board-panel">
        <div class="board-panel__head">
          <div class="board-panel__copy">
            <p class="board-panel__eyebrow">{{ currentPeriodLabel }}</p>
            <h2 class="board-panel__title">{{ currentBoard.title }}</h2>
          </div>
          <div class="board-panel__meta">
            <span v-if="activeBoard === 'works'" class="board-meta-pill">{{ currentRankingTypeLabel }}</span>
            <span v-if="activeBoard === 'works' && currentGenre" class="board-meta-pill">{{ currentGenre }}</span>
            <button
              v-if="activeBoard === 'works'"
              type="button"
              class="board-meta-pill board-meta-pill--button"
              :class="{ 'board-meta-pill--active': showGenrePanel }"
              @click="toggleGenreFilters"
            >体裁筛选</button>
          </div>
        </div>

        <div class="control-row">
          <div class="control-strip">
            <button
              v-for="period in availablePeriods"
              :key="period.value"
              type="button"
              class="control-chip"
              :class="{ 'control-chip--active': currentPeriod === period.value }"
              @click="changePeriod(period.value)"
            >{{ period.label }}</button>
          </div>
        </div>

        <div v-if="activeBoard === 'works'" class="control-row control-row--secondary">
          <div class="control-strip">
            <button
              v-for="type in rankingTypes"
              :key="type.value"
              type="button"
              class="control-chip control-chip--soft"
              :class="{ 'control-chip--active': currentRankingType === type.value }"
              @click="changeRankingType(type.value)"
            >{{ type.label }}</button>
          </div>
        </div>

        <div v-if="showGenrePanel" class="control-row control-row--secondary">
          <div class="control-strip control-strip--wrap">
            <button
              v-for="g in genreList"
              :key="g"
              type="button"
              class="control-chip control-chip--ghost"
              :class="{ 'control-chip--active': currentGenre === g }"
              @click="changeGenre(g)"
            >{{ g }}</button>
            <button
              type="button"
              class="control-chip control-chip--ghost"
              :class="{ 'control-chip--active': !currentGenre }"
              @click="changeGenre('')"
            >全部体裁</button>
          </div>
        </div>
      </section>

      <div v-if="loading && displayList.length === 0" class="loading-state">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <span class="spinner-char">榜</span>
        </div>
        <span class="loading-text">排行榜加载中…</span>
      </div>

      <div v-else-if="displayList.length === 0" class="empty-state">
        <div class="empty-seal">空</div>
        <p class="empty-text">暂无排行数据</p>
        <p class="empty-hint">{{ getEmptyHint() }}</p>
        <div class="empty-actions">
          <router-link v-if="activeBoard !== 'dailyWord'" to="/works/create" class="empty-action-btn empty-action-btn--primary">去创作</router-link>
          <router-link to="/works" class="empty-action-btn">浏览作品墙</router-link>
        </div>
      </div>

      <template v-else>
        <section
          v-if="activeBoard === 'works' && featuredWork"
          class="featured-card featured-card--interactive"
          @click="goWorkDetail(featuredWork.work_id)"
        >
          <div class="featured-card__eyebrow">
            <span class="featured-card__icon" :style="createMaskStyle(crownIcon)"></span>
            <span>本期领衔作品</span>
          </div>
          <div class="featured-card__body">
            <div class="featured-card__main">
              <h3 class="featured-card__title">{{ featuredWork.title }}</h3>
              <p class="featured-card__desc">{{ getPreviewLine(featuredWork.content) }}</p>
              <div class="featured-card__meta">
                <UserAvatar :username="featuredWork.username" :avatar="featuredWork.avatar_url" size="small" />
                <span>{{ featuredWork.username }}</span>
                <span class="featured-card__tag">{{ featuredWork.genre }}</span>
              </div>
            </div>
            <div class="featured-card__stats">
              <span class="metric-pill metric-pill--solid">综合 {{ featuredWork.composite_score.toFixed(1) }}</span>
              <span class="metric-pill">AI {{ formatScore(featuredWork.ai_total_score) }}</span>
              <span class="metric-pill metric-pill--icon">
                <span class="metric-pill__icon" :style="createMaskStyle(heatIcon)"></span>
                <span>{{ featuredWork.like_count }}</span>
              </span>
            </div>
          </div>
        </section>

        <section v-if="activeBoard === 'users' && featuredUser" class="featured-card">
          <div class="featured-card__eyebrow">
            <span class="featured-card__icon" :style="createMaskStyle(crownIcon)"></span>
            <span>本期领衔创作者</span>
          </div>
          <div class="featured-card__body">
            <div class="featured-card__main">
              <div class="featured-card__meta featured-card__meta--wide">
                <UserAvatar :username="featuredUser.username" :avatar="featuredUser.avatar_url" size="medium" />
                <div>
                  <h3 class="featured-card__title">{{ featuredUser.username }}</h3>
                  <p class="featured-card__desc">{{ currentPeriodLabel }}内保持稳定发布与传播表现</p>
                  <div class="ranking-user-rank">
                    <UserRank :level="featuredUser.level" :exp="featuredUser.exp" compact />
                    <span class="ranking-user-exp">{{ featuredUser.exp }} 文采</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="featured-card__stats">
              <span class="metric-pill">作品 {{ featuredUser.work_count }}</span>
              <span class="metric-pill metric-pill--icon">
                <span class="metric-pill__icon" :style="createMaskStyle(heatIcon)"></span>
                <span>{{ featuredUser.total_likes }}</span>
              </span>
              <span class="metric-pill metric-pill--solid">均分 {{ formatScore(featuredUser.avg_score) }}</span>
            </div>
          </div>
        </section>

        <section v-if="activeBoard === 'dailyWord' && featuredWord" class="featured-card">
          <div class="featured-card__eyebrow">
            <span class="featured-card__icon" :style="createMaskStyle(crownIcon)"></span>
            <span>本期高频意象</span>
          </div>
          <div class="featured-card__body">
            <div class="featured-card__main">
              <div class="featured-card__meta featured-card__meta--wide">
                <div class="featured-card__word">{{ featuredWord.word }}</div>
                <div>
                  <h3 class="featured-card__title">{{ featuredWord.pinyin }}</h3>
                  <p class="featured-card__desc">{{ featuredWord.description }}</p>
                </div>
              </div>
            </div>
            <div class="featured-card__stats">
              <span class="metric-pill metric-pill--solid">热度 {{ featuredWord.heat_score }}</span>
              <span class="metric-pill">引用 {{ featuredWord.usage_count }}</span>
              <span class="metric-pill">创作者 {{ featuredWord.creator_count }}</span>
            </div>
          </div>
        </section>

        <div v-if="activeBoard === 'works'" class="ranking-stack">
          <button
            v-for="(item, index) in workListItems"
            :key="item.work_id"
            type="button"
            class="ranking-card ranking-card--interactive"
            :style="{ animationDelay: `${index * 0.04}s` }"
            @click="goWorkDetail(item.work_id)"
          >
            <span class="ranking-card__rank" :class="getRankClass(item.rank)">{{ item.rank }}</span>
            <div class="ranking-card__body">
              <div class="ranking-card__main">
                <h3 class="ranking-card__title">{{ item.title }}</h3>
                <p class="ranking-card__desc">{{ getPreviewLine(item.content) }}</p>
                <div class="ranking-card__meta">
                  <UserAvatar :username="item.username" :avatar="item.avatar_url" size="small" />
                  <span>{{ item.username }}</span>
                  <span class="ranking-card__tag">{{ item.genre }}</span>
                </div>
              </div>
              <div class="ranking-card__stats">
                <span class="metric-pill metric-pill--solid">综合 {{ item.composite_score.toFixed(1) }}</span>
                <span class="metric-pill">AI {{ formatScore(item.ai_total_score) }}</span>
                <span class="metric-pill metric-pill--icon">
                  <span class="metric-pill__icon" :style="createMaskStyle(heatIcon)"></span>
                  <span>{{ item.like_count }}</span>
                </span>
              </div>
            </div>
          </button>
        </div>

        <div v-if="activeBoard === 'users'" class="ranking-stack">
          <article
            v-for="(item, index) in userListItems"
            :key="item.user_id"
            class="ranking-card"
            :style="{ animationDelay: `${index * 0.04}s` }"
          >
            <span class="ranking-card__rank" :class="getRankClass(item.rank)">{{ item.rank }}</span>
            <div class="ranking-card__body">
              <div class="ranking-card__main ranking-card__main--compact">
                <div class="ranking-card__meta ranking-card__meta--single">
                  <UserAvatar :username="item.username" :avatar="item.avatar_url" size="small" />
                  <div>
                    <h3 class="ranking-card__title">{{ item.username }}</h3>
                    <p class="ranking-card__desc">{{ currentPeriodLabel }}在榜创作者</p>
                    <div class="ranking-user-rank">
                      <UserRank :level="item.level" :exp="item.exp" compact />
                      <span class="ranking-user-exp">{{ item.exp }} 文采</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="ranking-card__stats">
                <span class="metric-pill">作品 {{ item.work_count }}</span>
                <span class="metric-pill metric-pill--icon">
                  <span class="metric-pill__icon" :style="createMaskStyle(heatIcon)"></span>
                  <span>{{ item.total_likes }}</span>
                </span>
                <span class="metric-pill metric-pill--solid">均分 {{ formatScore(item.avg_score) }}</span>
              </div>
            </div>
          </article>
        </div>

        <div v-if="activeBoard === 'dailyWord'" class="ranking-stack">
          <article
            v-for="(item, index) in dailyWordListItems"
            :key="item.word_id"
            class="ranking-card"
            :style="{ animationDelay: `${index * 0.04}s` }"
          >
            <span class="ranking-card__rank" :class="getRankClass(item.rank)">{{ item.rank }}</span>
            <div class="ranking-card__body">
              <div class="ranking-card__main">
                <div class="ranking-card__meta ranking-card__meta--single">
                  <div class="ranking-card__word-mark">{{ item.word }}</div>
                  <div>
                    <h3 class="ranking-card__title">{{ item.pinyin }} · {{ item.category }}</h3>
                    <p class="ranking-card__desc">{{ item.description }}</p>
                  </div>
                </div>
              </div>
              <div class="ranking-card__stats">
                <span class="metric-pill metric-pill--solid">热度 {{ item.heat_score }}</span>
                <span class="metric-pill">引用 {{ item.usage_count }}</span>
                <span class="metric-pill">创作者 {{ item.creator_count }}</span>
              </div>
            </div>
          </article>
        </div>
      </template>

      <div v-if="hasMore" class="load-more">
        <button class="btn-load-more" @click="loadMore" :disabled="loading">
          {{ loading ? '加载中…' : '查看更多' }}
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import './styles/rankings-page.css'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { worksApi, type WorkRankingItem, type WorkPieceRankingItem } from '@/api/works'
import UserAvatar from '@/components/UserAvatar.vue'
import UserRank from '@/components/UserRank.vue'
import {
  getMockDailyWordRankingResponse,
  getMockUserRankingResponse,
  getMockWorkRankingResponse,
  type DailyWordRankingItem,
  type RankingPeriodValue,
  type WorkRankingTypeValue
} from './rankings.data'

const router = useRouter()
const pageSize = 20
const crownIcon = '/icons/rankings/crown.svg'
const dailyWordBoardIcon = '/icons/rankings/board-daily-word.svg'
const heatIcon = '/icons/rankings/heat.svg'
const rankSealIcon = '/icons/rankings/rank-seal.svg'
const userBoardIcon = '/icons/rankings/board-users.svg'
const workBoardIcon = '/icons/rankings/board-works.svg'

type BoardValue = 'works' | 'users' | 'dailyWord'

interface PeriodOption {
  value: RankingPeriodValue
  label: string
}

interface BoardTab {
  value: BoardValue
  label: string
  title: string
  hint: string
  icon: string
  periods: PeriodOption[]
}

const boardTabs: BoardTab[] = [
  {
    value: 'works',
    label: '作品榜',
    title: '作品风云榜',
    hint: '聚合综合分、AI 评分与传播热度，保留创作表现的核心辨识度。',
    icon: workBoardIcon,
    periods: [
      { value: 'all', label: '总榜' },
      { value: 'monthly', label: '月榜' },
      { value: 'weekly', label: '周榜' },
      { value: 'daily', label: '日榜' }
    ]
  },
  {
    value: 'users',
    label: '创作者榜',
    title: '创作者榜',
    hint: '突出稳定产出与传播表现，用更轻的结构看清谁在持续创作。',
    icon: userBoardIcon,
    periods: [
      { value: 'all', label: '总榜' },
      { value: 'weekly', label: '周榜' },
      { value: 'daily', label: '日榜' }
    ]
  },
  {
    value: 'dailyWord',
    label: '每日一词榜',
    title: '每日一词榜',
    hint: '展示平台高频意象与用词趋势，为后续更多榜单扩展预留统一入口。',
    icon: dailyWordBoardIcon,
    periods: [
      { value: 'daily', label: '日榜' },
      { value: 'weekly', label: '周榜' },
      { value: 'all', label: '总览' }
    ]
  }
]

const defaultBoard = boardTabs[0] as BoardTab

const rankingTypes: Array<{ value: WorkRankingTypeValue; label: string }> = [
  { value: 'composite', label: '综合榜' },
  { value: 'ai_score', label: 'AI评分榜' },
  { value: 'popularity', label: '人气榜' }
]

const genreList = ['五言绝句', '七言绝句', '五言律诗', '七言律诗', '词', '自由体']

const activeBoard = ref<BoardValue>('works')
const currentRankingType = ref<WorkRankingTypeValue>('composite')
const currentPeriod = ref<RankingPeriodValue>('all')
const currentGenre = ref('')
const showGenreFilters = ref(false)
const workRankings = ref<WorkPieceRankingItem[]>([])
const userRankings = ref<WorkRankingItem[]>([])
const dailyWordRankings = ref<DailyWordRankingItem[]>([])
const page = ref(1)
const total = ref(0)
const loading = ref(false)

const currentBoard = computed<BoardTab>(() => boardTabs.find((board) => board.value === activeBoard.value) ?? defaultBoard)
const availablePeriods = computed<PeriodOption[]>(() => currentBoard.value.periods)
const currentRankingTypeLabel = computed(() => rankingTypes.find((item) => item.value === currentRankingType.value)?.label ?? '综合榜')
const currentPeriodLabel = computed(() => availablePeriods.value.find((item) => item.value === currentPeriod.value)?.label ?? availablePeriods.value[0]!.label)
const displayList = computed(() => {
  if (activeBoard.value === 'works') {
    return workRankings.value
  }

  if (activeBoard.value === 'users') {
    return userRankings.value
  }

  return dailyWordRankings.value
})
const hasMore = computed(() => activeBoard.value !== 'dailyWord' && displayList.value.length < total.value)
const featuredWork = computed(() => workRankings.value[0] ?? null)
const workListItems = computed(() => workRankings.value.slice(featuredWork.value ? 1 : 0))
const featuredUser = computed(() => userRankings.value[0] ?? null)
const userListItems = computed(() => userRankings.value.slice(featuredUser.value ? 1 : 0))
const featuredWord = computed(() => dailyWordRankings.value[0] ?? null)
const dailyWordListItems = computed(() => dailyWordRankings.value.slice(featuredWord.value ? 1 : 0))
const showGenrePanel = computed(() => activeBoard.value === 'works' && (showGenreFilters.value || Boolean(currentGenre.value)))

function getRankClass(rank: number) {
  if (rank <= 3) {
    return `rank--${rank}`
  }

  return 'rank--default'
}

function createMaskStyle(icon: string) {
  return {
    '--icon-url': `url(${icon})`
  } as Record<string, string>
}

function getPreviewLine(content: string) {
  return content.split('\n').find((line) => line.trim()) ?? content
}

function formatScore(score: number | null | undefined) {
  return typeof score === 'number' ? score.toFixed(1) : '待评'
}

function getEmptyHint() {
  if (activeBoard.value === 'dailyWord') {
    return '每日一词榜用于承接平台热词与意象趋势'
  }

  if (activeBoard.value === 'users') {
    return '创作者榜会根据已发布作品自动生成'
  }

  return '发布作品后将自动进入排行榜'
}

function normalizePeriodForBoard(period: RankingPeriodValue) {
  const matched = availablePeriods.value.find((item) => item.value === period)
  return matched ? matched.value : availablePeriods.value[0]!.value
}

function applyWorkResult(items: WorkPieceRankingItem[], totalCount: number, reset: boolean) {
  if (reset) {
    workRankings.value = items
  } else {
    workRankings.value.push(...items)
  }

  total.value = totalCount
}

function applyUserResult(items: WorkRankingItem[], totalCount: number, reset: boolean) {
  if (reset) {
    userRankings.value = items
  } else {
    userRankings.value.push(...items)
  }

  total.value = totalCount
}

function applyDailyWordResult(items: DailyWordRankingItem[], totalCount: number, reset: boolean) {
  if (reset) {
    dailyWordRankings.value = items
  } else {
    dailyWordRankings.value.push(...items)
  }

  total.value = totalCount
}

async function fetchData(reset = false) {
  if (reset) {
    page.value = 1
    workRankings.value = []
    userRankings.value = []
    dailyWordRankings.value = []
  }

  loading.value = true

  try {
    if (activeBoard.value === 'works') {
      const fallback = getMockWorkRankingResponse({
        rankingType: currentRankingType.value,
        period: currentPeriod.value,
        genre: currentGenre.value || undefined,
        page: page.value,
        pageSize
      })
      const res = await worksApi.getWorkPieceRankings({
        ranking_type: currentRankingType.value,
        period: currentPeriod.value,
        genre: currentGenre.value || undefined,
        page: page.value,
        page_size: pageSize
      })
      const useFallback = res.items.length === 0 && page.value === 1
      applyWorkResult(useFallback ? fallback.items : res.items, useFallback ? fallback.total : res.total, reset)
      return
    }

    if (activeBoard.value === 'users') {
      const fallback = getMockUserRankingResponse({
        period: currentPeriod.value,
        page: page.value,
        pageSize
      })
      const apiPeriod = currentPeriod.value === 'monthly' ? 'all' : currentPeriod.value
      const res = await worksApi.getRankings({
        period: apiPeriod,
        page: page.value,
        page_size: pageSize
      })
      const useFallback = res.items.length === 0 && page.value === 1
      applyUserResult(useFallback ? fallback.items : res.items, useFallback ? fallback.total : res.total, reset)
      return
    }

    const fallback = getMockDailyWordRankingResponse({
      period: currentPeriod.value,
      page: page.value,
      pageSize
    })
    applyDailyWordResult(fallback.items, fallback.total, reset)
  } catch {
    if (activeBoard.value === 'works') {
      const fallback = getMockWorkRankingResponse({
        rankingType: currentRankingType.value,
        period: currentPeriod.value,
        genre: currentGenre.value || undefined,
        page: page.value,
        pageSize
      })
      applyWorkResult(fallback.items, fallback.total, reset)
    } else if (activeBoard.value === 'users') {
      const fallback = getMockUserRankingResponse({
        period: currentPeriod.value,
        page: page.value,
        pageSize
      })
      applyUserResult(fallback.items, fallback.total, reset)
    } else {
      const fallback = getMockDailyWordRankingResponse({
        period: currentPeriod.value,
        page: page.value,
        pageSize
      })
      applyDailyWordResult(fallback.items, fallback.total, reset)
    }
  } finally {
    loading.value = false
  }
}

function switchBoard(val: BoardValue) {
  activeBoard.value = val
  currentPeriod.value = normalizePeriodForBoard(currentPeriod.value)

  if (val !== 'works') {
    showGenreFilters.value = false
  }

  fetchData(true)
}

function changeRankingType(val: WorkRankingTypeValue) {
  currentRankingType.value = val
  fetchData(true)
}

function changePeriod(val: RankingPeriodValue) {
  currentPeriod.value = val
  fetchData(true)
}

function changeGenre(val: string) {
  currentGenre.value = val

  if (!val) {
    showGenreFilters.value = false
  }

  fetchData(true)
}

function toggleGenreFilters() {
  showGenreFilters.value = !showGenreFilters.value
}

function loadMore() {
  page.value += 1
  fetchData()
}

function goWorkDetail(id: number) {
  router.push(`/works/${id}`)
}

onMounted(() => {
  currentPeriod.value = normalizePeriodForBoard(currentPeriod.value)
  fetchData(true)
})
</script>
