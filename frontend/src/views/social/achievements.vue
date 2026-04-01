<template>
  <div class="achievements-page">
    <nav class="page-nav">
      <div class="nav-inner">
        <AppBackButton label="返回上一页" fallback-to="/profile" class="nav-back" />
        <div class="title-block">
          <span class="title-sub">Achievement Hall</span>
          <h1 class="page-title">成就殿堂</h1>
        </div>
        <button class="nav-cta" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">全部成就</button>
      </div>
    </nav>

    <div class="achievements-content">
      <aside class="side-column" v-if="summary">
        <section class="hero-card">
          <div class="hero-copy">
            <span class="section-kicker">青衿功名册</span>
            <h2 class="hero-title">已点亮 {{ summary.total_unlocked }} 枚诗印</h2>
            <p class="hero-desc">成就奖励会直接计入等级经验，你在个人中心看到的品阶会与这里同步推进。</p>
          </div>

          <div class="hero-ring-wrap">
            <div class="summary-ring">
              <svg viewBox="0 0 80 80" class="ring-svg">
                <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.14)" stroke-width="5" />
                <circle cx="40" cy="40" r="34" fill="none" stroke="url(#heroRingGradient)" stroke-width="5" stroke-linecap="round" :stroke-dasharray="ringDash" stroke-dashoffset="0" transform="rotate(-90 40 40)" class="ring-progress" />
                <defs>
                  <linearGradient id="heroRingGradient" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#f0d29b" />
                    <stop offset="100%" stop-color="#d4553d" />
                  </linearGradient>
                </defs>
              </svg>
              <span class="ring-text">{{ summary.completion_rate }}%</span>
            </div>

            <div class="hero-totals">
              <div v-for="item in heroStats" :key="item.label" class="hero-total-card">
                <div class="hero-total-top">
                  <span class="hero-total-label">{{ item.label }}</span>
                  <span class="hero-total-mark">{{ item.mark }}</span>
                </div>
                <strong>{{ item.value }}</strong>
                <span class="hero-total-note">{{ item.note }}</span>
              </div>
            </div>
          </div>
        </section>

        <section class="rank-card">
          <div class="rank-head">
            <div class="rank-icon-shell" :style="{ borderColor: rankInfo.color }">
              <img :src="rankInfo.icon" alt="" class="rank-icon" />
            </div>
            <div class="rank-copy">
              <span class="section-kicker">当前品阶</span>
              <h3>Lv.{{ summary.current_level }} · {{ rankInfo.name }}</h3>
              <p>{{ rankInfo.desc }}</p>
            </div>
          </div>

          <div class="rank-progress-card">
            <div class="rank-progress-top">
              <span>当前经验 {{ summary.current_exp }}</span>
              <span>{{ expProgress.percent }}%</span>
            </div>
            <div class="rank-progress-bar">
              <div class="rank-progress-fill" :style="{ width: expProgress.percent + '%', background: rankInfo.color }"></div>
            </div>
            <div class="rank-progress-bottom">
              <span>{{ expProgress.current }} / {{ expProgress.total }}</span>
              <span v-if="nextRank">距{{ nextRank.name }}还差 {{ remainingExp }} 经验</span>
              <span v-else>已达最高品阶</span>
            </div>
          </div>
        </section>

        <section class="filter-card">
          <div class="filter-head">
            <div>
              <span class="section-kicker">卷册分类</span>
              <h3>{{ categoryLabel(activeCategory) }}</h3>
            </div>
            <span class="filter-tip">按成长方向筛选</span>
          </div>

          <div class="filter-list">
            <button
              v-for="filter in categoryFilters"
              :key="filter.key"
              class="filter-chip"
              :class="{ active: activeCategory === filter.key }"
              @click="activeCategory = filter.key"
            >
              <div class="filter-chip-top">
                <span>{{ filter.label }}</span>
                <strong>{{ filter.completion }}%</strong>
              </div>
              <div class="filter-chip-bottom">
                <span>{{ filter.unlocked }} / {{ filter.total }}</span>
                <span>已收卷</span>
              </div>
            </button>
          </div>
        </section>
      </aside>

      <main class="main-column">
        <section class="board-hero" v-if="summary">
          <div>
            <span class="section-kicker">成就总览</span>
            <h2 class="board-title">把你的诗学成长，排成一册可以随时翻阅的功名卷</h2>
            <p class="board-desc">这里既能查看当前冲刺进度，也能一口气浏览全部成就目录，领奖与等级反馈会在同一处完成。</p>
            <div class="board-shortcuts">
              <button class="board-shortcut board-shortcut--strong" @click="activeTab = 'all'">查看全部成就</button>
              <button class="board-shortcut" @click="activeTab = 'unlocked'">查看已获成就</button>
            </div>
          </div>
          <div class="tab-bar">
            <button class="tab-btn" :class="{ active: activeTab === 'progress' }" @click="activeTab = 'progress'">进度图谱</button>
            <button class="tab-btn" :class="{ active: activeTab === 'unlocked' }" @click="activeTab = 'unlocked'">已得诗印</button>
            <button class="tab-btn" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">全卷目录</button>
          </div>
        </section>

        <section v-if="activeTab === 'progress'" class="progress-stack" :class="{ 'desktop-fixed': isDesktopProgressFixed }">
          <div class="progress-grid" :style="progressGridStyle">
            <article
              v-for="(item, idx) in pagedProgressItems"
              :key="item.achievement_id"
              class="progress-panel"
              :class="[item.rarity, { unlocked: item.is_unlocked }]"
              :style="{ animationDelay: idx * 0.04 + 's' }"
            >
              <div class="progress-tier-strip">
                <span class="progress-tier-label">{{ rarityToneLabel(item.rarity) }}</span>
              </div>

              <div class="progress-panel-top">
                <div class="seal-wrap">
                  <div class="seal-icon" :class="[item.rarity, { unlocked: item.is_unlocked }]">{{ sealText(item.name) }}</div>
                  <span class="seal-category">{{ categoryLabel(item.category) }}</span>
                </div>
                <div class="progress-panel-main">
                  <div class="progress-panel-head">
                    <h3>{{ item.name }}</h3>
                    <div class="panel-badges">
                      <span class="status-tag" :class="{ unlocked: item.is_unlocked }">{{ item.is_unlocked ? '已达成' : '进行中' }}</span>
                      <span class="rarity-tag" :class="item.rarity">{{ rarityLabel(item.rarity) }}</span>
                    </div>
                  </div>
                  <p class="progress-panel-desc">{{ item.description }}</p>
                </div>
              </div>

              <div class="progress-meta-row">
                <span>{{ conditionText(item) }}</span>
                <strong>{{ item.current_value }} / {{ item.target_value }}</strong>
              </div>

              <div class="progress-bar">
                <div class="progress-fill" :class="item.rarity" :style="{ width: item.percentage + '%', animationDelay: idx * 0.05 + 's' }"></div>
              </div>

              <div class="reward-row">
                <span>+{{ item.exp_reward }} 经验</span>
                <span>+{{ item.points_reward }} 积分</span>
                <span>{{ Math.round(item.percentage) }}%</span>
              </div>
            </article>

            <div v-if="!pagedProgressItems.length" class="empty-state">
              <p>当前筛选下暂无成就进度</p>
              <p class="empty-state-hint">切换左侧卷册分类查看其他方向的成就</p>
            </div>
          </div>

          <div v-if="progressTotalPages > 1" class="progress-pagination">
            <button
              v-for="page in progressPageNumbers"
              :key="page"
              class="progress-page-btn"
              :class="{ active: page === progressPage }"
              @click="setProgressPage(page)"
            >
              {{ page }}
            </button>
          </div>
        </section>

        <section v-if="activeTab === 'unlocked'" class="timeline-list">
          <article
            v-for="(item, idx) in filteredUnlockedItems"
            :key="item.id"
            class="timeline-card"
            :class="item.rarity"
            :style="{ animationDelay: idx * 0.04 + 's' }"
          >
            <div class="timeline-marker">
              <div class="timeline-seal" :class="item.rarity">{{ sealText(item.name) }}</div>
            </div>
            <div class="timeline-body">
              <div class="timeline-head">
                <div>
                  <div class="timeline-title-row">
                    <h3>{{ item.name }}</h3>
                    <span class="rarity-tag" :class="item.rarity">{{ rarityLabel(item.rarity) }}</span>
                  </div>
                  <p>{{ item.description }}</p>
                </div>
                <div class="timeline-reward">
                  <strong>+{{ item.exp_reward }}</strong>
                  <span>经验入卷</span>
                </div>
              </div>
              <div class="timeline-meta">
                <span>{{ categoryLabel(item.category) }}</span>
                <span>{{ formatDate(item.unlocked_at) }}</span>
              </div>
            </div>
          </article>

          <div v-if="!filteredUnlockedItems.length" class="empty-state">
            <p>该卷册下暂未解锁成就</p>
            <p class="empty-state-hint">完成学习、创作、挑战等活动即可解锁对应成就</p>
            <div class="empty-state-actions">
              <router-link to="/poems" class="empty-state-btn">去学习</router-link>
              <router-link to="/works/create" class="empty-state-btn">去创作</router-link>
              <router-link to="/games" class="empty-state-btn">去挑战</router-link>
            </div>
          </div>
        </section>

        <section v-if="activeTab === 'all'" class="catalog-layout">
          <article v-for="cat in filteredCategories" :key="cat.category" class="catalog-section">
            <header class="catalog-header">
              <div>
                <span class="section-kicker">{{ categoryLabel(cat.category) }}</span>
                <h3>{{ cat.category_name }}</h3>
              </div>
              <span class="catalog-count">{{ cat.achievements.length }} 枚</span>
            </header>

            <div class="catalog-cards">
              <div
                v-for="a in cat.achievements"
                :key="a.id"
                class="catalog-card"
                :class="[a.rarity, { unlocked: unlockedIdSet.has(a.id) }]"
              >
                <div class="catalog-card-top">
                  <div class="catalog-seal">{{ sealText(a.name) }}</div>
                  <span class="rarity-tag" :class="a.rarity">{{ rarityLabel(a.rarity) }}</span>
                </div>
                <div class="catalog-name">{{ a.name }}</div>
                <div class="catalog-desc">{{ a.description }}</div>
                <div class="catalog-meta">
                  <span>门槛 {{ a.condition_value }}</span>
                  <span>{{ unlockedIdSet.has(a.id) ? '已收录' : '待达成' }}</span>
                </div>
                <div class="catalog-reward">+{{ a.exp_reward }} 经验 · +{{ a.points_reward }} 积分</div>
              </div>
            </div>
          </article>

          <div v-if="!filteredCategories.length" class="empty-state">
            <p>暂无该类别成就目录</p>
            <p class="empty-state-hint">试试切换到“全部卷册”查看所有成就</p>
          </div>
        </section>
      </main>
    </div>

    <transition name="reveal-fade">
      <div v-if="activeReveal" class="reveal-mask" @click.self="closeReveal">
        <div class="reveal-panel" :class="activeReveal.rarity">
          <div class="reveal-orbit"></div>
          <span class="section-kicker">新成就入卷</span>
          <div class="reveal-seal" :class="activeReveal.rarity">{{ sealText(activeReveal.name) }}</div>
          <h3>{{ activeReveal.name }}</h3>
          <p>{{ activeReveal.description }}</p>
          <div class="reveal-rewards">
            <span>+{{ activeReveal.exp_reward }} 经验</span>
            <span>+{{ activeReveal.points_reward }} 积分</span>
          </div>
          <div class="reveal-footer">
            <span>{{ revealIndex + 1 }} / {{ revealQueue.length }}</span>
            <button class="reveal-btn" @click="nextReveal">{{ revealIndex < revealQueue.length - 1 ? '继续揭榜' : '收起诗印' }}</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  achievementApi,
  type AchievementCategory,
  type AchievementMineResponse,
  type AchievementProgressItem,
  type UserAchievementItem
} from '@/api/achievement'
import AppBackButton from '@/components/AppBackButton.vue'
import { useUserStore } from '@/store/modules/user'
import { getExpProgress, getRankByExp, getNextRank } from '@/utils/levels'

type AchievementViewTab = 'progress' | 'unlocked' | 'all'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const readQueryString = (value: unknown) => {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value[0] || ''
  return ''
}

const resolveTab = (value: unknown): AchievementViewTab => {
  const tab = readQueryString(value)
  return tab === 'all' || tab === 'unlocked' || tab === 'progress' ? tab : 'progress'
}

const categoryLabelMap: Record<string, string> = {
  all: '全部卷册',
  growth: '青云有阶',
  learning: '学海无涯',
  creation: '妙笔生花',
  social: '高山流水',
  challenge: '过关斩将',
  relay: '珠联璧合'
}

const conditionLabelMap: Record<string, string> = {
  poems_read: '阅读',
  poems_favorited: '收藏',
  works_published: '发布',
  works_liked_received: '获赞',
  followers_count: '粉丝',
  following_count: '关注',
  challenges_completed: '挑战',
  relay_games: '接龙',
  relay_max_combo: '连击',
  user_level: '等级'
}

const categoryOrder = ['growth', 'learning', 'creation', 'social', 'challenge', 'relay']

const activeTab = ref<AchievementViewTab>(resolveTab(route.query.tab))
const activeCategory = ref('all')
const progressItems = ref<AchievementProgressItem[]>([])
const unlockedItems = ref<UserAchievementItem[]>([])
const allCategories = ref<AchievementCategory[]>([])
const summary = ref<AchievementMineResponse | null>(null)
const revealQueue = ref<UserAchievementItem[]>([])
const revealIndex = ref(0)
const viewportWidth = ref(typeof window === 'undefined' ? 1440 : window.innerWidth)
const progressPage = ref(1)

const syncViewportWidth = () => {
  if (typeof window === 'undefined') return
  viewportWidth.value = window.innerWidth
}

const ringDash = computed(() => {
  const circumference = 2 * Math.PI * 34
  const rate = summary.value ? summary.value.completion_rate / 100 : 0
  return `${circumference * rate} ${circumference * (1 - rate)}`
})

const rankInfo = computed(() => getRankByExp(summary.value?.current_exp ?? 0))
const nextRank = computed(() => getNextRank(summary.value?.current_level ?? rankInfo.value.level))
const expProgress = computed(() => getExpProgress(summary.value?.current_exp ?? 0))
const activeReveal = computed(() => revealQueue.value[revealIndex.value] ?? null)
const remainingExp = computed(() => {
  if (!summary.value?.next_level_exp) return 0
  return Math.max(summary.value.next_level_exp - summary.value.current_exp, 0)
})
const unlockedIdSet = computed(() => new Set(unlockedItems.value.map(item => item.id)))
const heroStats = computed(() => {
  if (!summary.value) return []
  return [
    {
      label: '已解锁',
      value: `${summary.value.total_unlocked} / ${summary.value.total_achievements}`,
      note: summary.value.total_achievements > 0 ? `收录率 ${summary.value.completion_rate}%` : '卷册整理中',
      mark: '印'
    },
    {
      label: '成就经验',
      value: `${summary.value.total_exp_rewarded}`,
      note: nextRank.value ? `距${nextRank.value.name}还差 ${remainingExp.value} 经验` : '已达最高品阶',
      mark: '阶'
    },
    {
      label: '成就积分',
      value: `${summary.value.total_points_rewarded}`,
      note: summary.value.total_points_rewarded > 0 ? '已计入个人积分' : '等待首次入卷',
      mark: '赏'
    }
  ]
})

const categoryFilters = computed(() => {
  const filters = [
    {
      key: 'all',
      label: categoryLabelMap.all,
      total: progressItems.value.length,
      unlocked: unlockedItems.value.length,
      completion: summary.value?.completion_rate ?? 0
    }
  ]

  for (const category of categoryOrder) {
    const items = progressItems.value.filter(item => item.category === category)
    if (!items.length) continue
    const unlocked = items.filter(item => item.is_unlocked).length
    filters.push({
      key: category,
      label: categoryLabelMap[category] ?? category,
      total: items.length,
      unlocked,
      completion: Math.round((unlocked / items.length) * 100)
    })
  }

  return filters
})

const filteredProgressItems = computed(() => {
  return progressItems.value
    .filter(item => activeCategory.value === 'all' || item.category === activeCategory.value)
    .slice()
    .sort((a, b) => Number(b.is_unlocked) - Number(a.is_unlocked) || b.percentage - a.percentage || a.target_value - b.target_value)
})

const isDesktopProgressFixed = computed(() => viewportWidth.value > 1180)

const progressPageSize = computed(() => {
  if (viewportWidth.value <= 640) return 3
  if (viewportWidth.value <= 1180) return 4
  return 9
})

const progressTotalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredProgressItems.value.length / progressPageSize.value))
})

const progressPageNumbers = computed(() => {
  return Array.from({ length: progressTotalPages.value }, (_, index) => index + 1)
})

const pagedProgressItems = computed(() => {
  const start = (progressPage.value - 1) * progressPageSize.value
  return filteredProgressItems.value.slice(start, start + progressPageSize.value)
})

const progressGridStyle = computed<Record<string, string>>(() => {
  return {
    rowGap: isDesktopProgressFixed.value ? '22px' : '0px'
  }
})

const filteredUnlockedItems = computed(() => {
  return unlockedItems.value.filter(item => activeCategory.value === 'all' || item.category === activeCategory.value)
})

const filteredCategories = computed(() => {
  return allCategories.value
    .filter(cat => cat.achievements.length > 0)
    .filter(cat => activeCategory.value === 'all' || cat.category === activeCategory.value)
    .map(cat => ({
      ...cat,
      achievements: [...cat.achievements].sort((a, b) => a.condition_value - b.condition_value)
    }))
})

const rarityLabel = (r: string) => {
  const map: Record<string, string> = { common: '普通', rare: '稀有', epic: '史诗', legendary: '传说' }
  return map[r] || r
}

const rarityToneLabel = (r: string) => {
  const map: Record<string, string> = { common: '素卷', rare: '玉章', epic: '金册', legendary: '御诰' }
  return map[r] || r
}

const formatDate = (t: string) => {
  const d = new Date(t)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const sealText = (name: string) => name.slice(0, 2)

const categoryLabel = (category: string) => categoryLabelMap[category] ?? category

const conditionText = (item: AchievementProgressItem) => {
  return `${conditionLabelMap[item.condition_type] ?? '达成'} ${item.target_value}`
}

const queueNewlyUnlocked = (items: UserAchievementItem[]) => {
  if (!items.length) return
  const merged = new Map<number, UserAchievementItem>()
  for (const item of revealQueue.value) {
    merged.set(item.id, item)
  }
  for (const item of items) {
    merged.set(item.id, item)
  }
  revealQueue.value = Array.from(merged.values()).sort(
    (a, b) => new Date(b.unlocked_at).getTime() - new Date(a.unlocked_at).getTime()
  )
  revealIndex.value = 0
}

const nextReveal = () => {
  if (revealIndex.value < revealQueue.value.length - 1) {
    revealIndex.value += 1
    return
  }
  closeReveal()
}

const closeReveal = () => {
  revealQueue.value = []
  revealIndex.value = 0
}

const setProgressPage = (page: number) => {
  progressPage.value = Math.min(Math.max(page, 1), progressTotalPages.value)
}

watch(
  () => route.query.tab,
  (value) => {
    const nextTab = resolveTab(value)
    if (nextTab !== activeTab.value) {
      activeTab.value = nextTab
    }
  }
)

watch(activeTab, (tab) => {
  const currentTab = readQueryString(route.query.tab)
  if (tab === 'progress' && !currentTab) return
  if (currentTab === tab) return
  router.replace({
    path: '/achievements',
    query: tab === 'progress' ? {} : { tab }
  })
})

watch([activeCategory, activeTab, progressPageSize], () => {
  progressPage.value = 1
})

watch(progressTotalPages, (total) => {
  if (progressPage.value > total) {
    progressPage.value = total
  }
})

const loadData = async () => {
  try {
    const [progressRes, unlockedRes, allRes] = await Promise.all([
      achievementApi.getProgress(),
      achievementApi.getMyAchievements(),
      achievementApi.getAllAchievements()
    ])

    progressItems.value = progressRes.progress
    unlockedItems.value = unlockedRes.unlocked
    summary.value = unlockedRes
    allCategories.value = allRes.categories

    const mergedNewlyUnlocked = [...unlockedRes.newly_unlocked, ...progressRes.newly_unlocked]
    queueNewlyUnlocked(mergedNewlyUnlocked)

    if (mergedNewlyUnlocked.length > 0) {
      await userStore.fetchUserInfo()
    }
  } catch (error) {
    console.error('加载成就数据失败:', error)
  }
}

onMounted(() => {
  syncViewportWidth()
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', syncViewportWidth)
  }
  activeTab.value = resolveTab(route.query.tab)
  void loadData()
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', syncViewportWidth)
  }
})
</script>

<style scoped>
.achievements-page {
  position: relative;
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(206, 129, 85, 0.16), transparent 28%),
    radial-gradient(circle at top right, rgba(120, 87, 52, 0.16), transparent 24%),
    linear-gradient(180deg, #f6efe3 0%, #efe3cf 100%);
  overflow: hidden;
}

.achievements-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(120, 87, 52, 0.04) 1px, transparent 1px),
    linear-gradient(180deg, rgba(120, 87, 52, 0.04) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.6), transparent 82%);
  pointer-events: none;
}

.page-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(40, 29, 20, 0.78);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(240, 210, 155, 0.18);
}

.nav-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 18px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.nav-back {
  flex-shrink: 0;
}

.title-block {
  text-align: center;
}

.title-sub {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(240, 210, 155, 0.78);
}

.page-title {
  font-family: var(--font-title);
  font-size: 26px;
  letter-spacing: 0.32em;
  color: #fff6e8;
}

.nav-cta {
  padding: 10px 16px;
  border-radius: 999px;
  border: 1px solid rgba(240, 210, 155, 0.22);
  background: rgba(255, 255, 255, 0.06);
  color: #fff2d8;
  font-size: 13px;
  transition: all 0.2s ease;
}

.nav-cta.active,
.nav-cta:hover {
  background: rgba(240, 210, 155, 0.18);
  border-color: rgba(240, 210, 155, 0.4);
}

.achievements-content {
  position: relative;
  z-index: 1;
  max-width: 1440px;
  margin: 0 auto;
  padding: 30px 32px 48px;
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.side-column {
  position: sticky;
  top: 96px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-card,
.rank-card,
.filter-card,
.board-hero,
.progress-panel,
.timeline-card,
.catalog-section,
.reveal-panel {
  border: 1px solid rgba(124, 90, 55, 0.14);
  box-shadow: 0 18px 40px rgba(73, 47, 26, 0.08);
}

.hero-card {
  padding: 24px;
  border-radius: 28px;
  background:
    linear-gradient(145deg, rgba(60, 39, 24, 0.98), rgba(106, 63, 38, 0.92)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02));
  color: #fdf4e7;
}

.hero-copy,
.rank-copy,
.filter-head,
.catalog-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-kicker {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(240, 210, 155, 0.14);
  color: #f0d29b;
  font-size: 11px;
  letter-spacing: 0.12em;
}

.hero-title,
.board-title {
  font-family: var(--font-title);
  line-height: 1.25;
}

.hero-title {
  font-size: 28px;
  letter-spacing: 0.08em;
}

.hero-desc,
.board-desc,
.rank-copy p,
.timeline-head p,
.catalog-desc,
.progress-panel-desc,
.reveal-panel p {
  font-size: 14px;
  line-height: 1.7;
  color: rgba(250, 240, 226, 0.72);
}

.hero-ring-wrap {
  margin-top: 24px;
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 16px;
  align-items: center;
}

.summary-ring {
  position: relative;
  width: 88px;
  height: 88px;
}

.ring-svg {
  width: 100%;
  height: 100%;
}

.ring-progress {
  transition: stroke-dasharray 0.8s ease;
}

.ring-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-title);
  font-size: 18px;
  color: #fff5dd;
}

.hero-totals {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.hero-total-card {
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.11), rgba(255, 255, 255, 0.05));
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-rows: auto auto;
  column-gap: 14px;
  row-gap: 4px;
  align-items: center;
}

.hero-total-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.hero-total-label,
.rank-progress-top,
.rank-progress-bottom,
.filter-tip,
.filter-chip-bottom,
.progress-meta-row,
.reward-row,
.timeline-meta,
.catalog-meta,
.catalog-count,
.reveal-footer {
  font-size: 12px;
}

.hero-total-card strong {
  grid-column: 2 / 3;
  grid-row: 1 / 3;
  align-self: center;
  font-size: 24px;
  color: #fff7e8;
  white-space: nowrap;
}

.hero-total-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  background: rgba(240, 210, 155, 0.14);
  color: #f0d29b;
  font-family: var(--font-title);
  font-size: 12px;
}

.hero-total-note {
  color: rgba(255, 242, 220, 0.6);
  font-size: 12px;
  line-height: 1.6;
}

.rank-card,
.filter-card,
.board-hero,
.progress-panel,
.timeline-card,
.catalog-section {
  background: rgba(255, 251, 245, 0.82);
  backdrop-filter: blur(14px);
}

.rank-card,
.filter-card {
  padding: 20px;
  border-radius: 24px;
}

.rank-head {
  display: flex;
  gap: 14px;
  align-items: center;
}

.rank-icon-shell {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  border: 1px solid;
  background: rgba(255, 255, 255, 0.62);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
  flex-shrink: 0;
}

.rank-icon {
  width: 40px;
  height: 40px;
}

.rank-copy h3,
.filter-head h3,
.catalog-header h3,
.progress-panel-head h3,
.timeline-title-row h3,
.reveal-panel h3 {
  font-family: var(--font-title);
  color: #2f2118;
}

.rank-copy h3,
.filter-head h3 {
  font-size: 22px;
}

.rank-copy p {
  color: rgba(47, 33, 24, 0.6);
}

.rank-progress-card {
  margin-top: 18px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(125, 89, 55, 0.07);
}

.rank-progress-top,
.rank-progress-bottom,
.progress-meta-row,
.reward-row,
.timeline-meta,
.catalog-meta,
.reveal-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: rgba(47, 33, 24, 0.62);
}

.rank-progress-bar,
.progress-bar {
  position: relative;
  overflow: hidden;
  height: 8px;
  border-radius: 999px;
  background: rgba(125, 89, 55, 0.12);
}

.rank-progress-bar {
  margin: 12px 0 10px;
}

.rank-progress-fill,
.progress-fill {
  height: 100%;
  border-radius: inherit;
  animation: barGrow 0.9s ease backwards;
}

.filter-head {
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.filter-tip {
  color: rgba(47, 33, 24, 0.45);
}

.filter-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-chip {
  width: 100%;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(124, 90, 55, 0.1);
  background: rgba(255, 255, 255, 0.6);
  text-align: left;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.filter-chip:hover,
.filter-chip.active {
  transform: translateY(-1px);
  border-color: rgba(180, 109, 57, 0.26);
  box-shadow: 0 10px 24px rgba(140, 93, 56, 0.08);
}

.filter-chip.active {
  background: linear-gradient(135deg, rgba(212, 85, 61, 0.12), rgba(240, 210, 155, 0.18));
}

.filter-chip-top,
.catalog-card-top,
.progress-panel-top,
.progress-panel-head,
.timeline-head,
.timeline-title-row,
.panel-badges {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.filter-chip-top strong {
  color: #8e4b2f;
}

.main-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.board-hero {
  padding: 24px 26px;
  border-radius: 28px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 24px;
  align-items: end;
}

.board-title {
  max-width: 760px;
  font-size: 34px;
  color: #2f2118;
}

.board-desc {
  max-width: 720px;
  color: rgba(47, 33, 24, 0.58);
}

.board-shortcuts {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.board-shortcut {
  min-height: 44px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(124, 90, 55, 0.14);
  background: rgba(255, 255, 255, 0.66);
  color: rgba(47, 33, 24, 0.72);
  font-size: 14px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.board-shortcut:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(125, 89, 55, 0.08);
}

.board-shortcut--strong {
  background: linear-gradient(135deg, #d97757, #c86445);
  border-color: rgba(217, 119, 87, 0.26);
  color: #fff7ec;
}

.tab-bar {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.tab-btn {
  padding: 12px 18px;
  border-radius: 999px;
  border: 1px solid rgba(124, 90, 55, 0.12);
  background: rgba(255, 255, 255, 0.72);
  color: rgba(47, 33, 24, 0.65);
  font-size: 14px;
  transition: all 0.2s ease;
}

.tab-btn.active,
.tab-btn:hover {
  background: #3e2c1e;
  color: #fff2dd;
  border-color: #3e2c1e;
}

.progress-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.progress-stack.desktop-fixed {
  min-height: 720px;
  justify-content: space-between;
}

.progress-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  align-items: stretch;
  gap: 18px;
}

.progress-pagination {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
}

.progress-page-btn {
  min-width: 40px;
  height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(124, 90, 55, 0.16);
  background: rgba(255, 255, 255, 0.74);
  color: rgba(47, 33, 24, 0.68);
  font-size: 13px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.progress-page-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(124, 90, 55, 0.28);
  box-shadow: 0 10px 20px rgba(125, 89, 55, 0.08);
}

.progress-page-btn.active {
  background: linear-gradient(135deg, #3e2c1e, #5f4330);
  border-color: rgba(62, 44, 30, 0.68);
  color: #fff2dd;
  box-shadow: 0 12px 24px rgba(62, 44, 30, 0.16);
}

.progress-tier-strip {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(var(--rarity-rgb), 0.14);
}

.progress-tier-label {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid var(--rarity-accent-border);
  background: var(--rarity-accent-bg);
  color: var(--rarity-color);
  font-size: 11px;
  letter-spacing: 0.08em;
}

.progress-panel.rare .progress-tier-strip {
  border-bottom-style: dashed;
}

.progress-panel.epic .progress-tier-strip::after,
.progress-panel.legendary .progress-tier-strip::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(var(--rarity-rgb), 0.74), transparent);
}

.progress-panel.legendary .progress-tier-strip::before {
  content: '';
  position: absolute;
  top: -8px;
  right: -2px;
  width: 80px;
  height: 28px;
  background: radial-gradient(circle at center, rgba(var(--rarity-rgb), 0.18), transparent 70%);
  pointer-events: none;
}

.progress-panel,
.timeline-card,
.catalog-section {
  border-radius: 24px;
  animation: cardRise 0.45s ease backwards;
}

.progress-panel,
.timeline-card,
.catalog-card,
.reveal-panel,
.seal-icon,
.timeline-seal,
.reveal-seal {
  --rarity-color: #7d5937;
  --rarity-rgb: 125, 89, 55;
  --rarity-border: rgba(124, 90, 55, 0.18);
  --rarity-surface: linear-gradient(180deg, rgba(255, 251, 245, 0.96), rgba(243, 235, 223, 0.92));
  --rarity-surface-strong: linear-gradient(160deg, rgba(255, 252, 247, 0.98), rgba(245, 237, 224, 0.96));
  --rarity-mist:
    radial-gradient(circle at 84% 0%, rgba(145, 109, 78, 0.16), transparent 34%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.18), transparent 38%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.1), transparent 68%);
  --rarity-accent-bg: linear-gradient(135deg, rgba(125, 89, 55, 0.08), rgba(255, 255, 255, 0.84));
  --rarity-accent-border: rgba(125, 89, 55, 0.16);
  --rarity-seal-bg:
    radial-gradient(circle at 30% 28%, rgba(255, 255, 255, 0.96), transparent 36%),
    linear-gradient(155deg, rgba(255, 255, 255, 0.92), rgba(247, 241, 233, 0.72)),
    linear-gradient(135deg, rgba(125, 89, 55, 0.1), rgba(255, 255, 255, 0));
  --rarity-strong-bg: linear-gradient(135deg, #7d5937, #5a3e28);
  --rarity-strong-shadow: rgba(125, 89, 55, 0.28);
}

.progress-panel,
.timeline-card,
.catalog-card,
.reveal-panel {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  border: 1px solid var(--rarity-border);
  background: var(--rarity-surface);
  box-shadow: 0 18px 40px rgba(73, 47, 26, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.46);
}

.progress-panel::before,
.timeline-card::before,
.catalog-card::before,
.reveal-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: var(--rarity-mist);
  pointer-events: none;
  z-index: 0;
}

.progress-panel::after,
.timeline-card::after,
.catalog-card::after,
.reveal-panel::after {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  border: 1px solid rgba(255, 255, 255, 0.34);
  pointer-events: none;
  z-index: 0;
}

.progress-panel > *,
.timeline-card > *,
.catalog-card > *,
.reveal-panel > * {
  position: relative;
  z-index: 1;
}

.progress-panel {
  padding: 20px;
}

.progress-panel-top {
  align-items: flex-start;
}

.progress-panel-head {
  align-items: flex-start;
}

.panel-badges {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.progress-panel.unlocked {
  background: var(--rarity-surface-strong);
}

.progress-panel.common,
.timeline-card.common,
.catalog-card.common,
.reveal-panel.common,
.seal-icon.common,
.timeline-seal.common,
.reveal-seal.common {
  --rarity-color: #7d5937;
  --rarity-rgb: 125, 89, 55;
  --rarity-border: rgba(124, 90, 55, 0.2);
  --rarity-surface: linear-gradient(180deg, rgba(255, 251, 245, 0.97), rgba(242, 233, 220, 0.93));
  --rarity-surface-strong: linear-gradient(160deg, rgba(255, 252, 247, 0.99), rgba(244, 236, 224, 0.96));
  --rarity-mist:
    radial-gradient(circle at 78% 0%, rgba(145, 109, 78, 0.18), transparent 34%),
    linear-gradient(135deg, rgba(125, 89, 55, 0.05), transparent 42%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.18), transparent 68%);
  --rarity-accent-bg: linear-gradient(135deg, rgba(125, 89, 55, 0.08), rgba(255, 255, 255, 0.84));
  --rarity-accent-border: rgba(125, 89, 55, 0.16);
  --rarity-seal-bg:
    radial-gradient(circle at 28% 26%, rgba(255, 255, 255, 0.96), transparent 34%),
    linear-gradient(160deg, rgba(255, 255, 255, 0.92), rgba(248, 242, 234, 0.74)),
    linear-gradient(135deg, rgba(125, 89, 55, 0.12), rgba(255, 255, 255, 0));
  --rarity-strong-bg: linear-gradient(135deg, #866142, #5e412b);
  --rarity-strong-shadow: rgba(125, 89, 55, 0.26);
}

.progress-panel.rare,
.timeline-card.rare,
.catalog-card.rare,
.reveal-panel.rare,
.seal-icon.rare,
.timeline-seal.rare,
.reveal-seal.rare {
  --rarity-color: #476f68;
  --rarity-rgb: 71, 111, 104;
  --rarity-border: rgba(71, 111, 104, 0.24);
  --rarity-surface: linear-gradient(180deg, rgba(246, 251, 249, 0.98), rgba(231, 243, 238, 0.94));
  --rarity-surface-strong: linear-gradient(160deg, rgba(248, 252, 250, 0.99), rgba(233, 246, 241, 0.97));
  --rarity-mist:
    radial-gradient(circle at 82% 0%, rgba(111, 166, 151, 0.22), transparent 34%),
    radial-gradient(circle at 0% 100%, rgba(61, 114, 104, 0.12), transparent 32%),
    linear-gradient(140deg, rgba(255, 255, 255, 0.18), transparent 42%);
  --rarity-accent-bg: linear-gradient(135deg, rgba(71, 111, 104, 0.12), rgba(255, 255, 255, 0.88));
  --rarity-accent-border: rgba(71, 111, 104, 0.18);
  --rarity-seal-bg:
    radial-gradient(circle at 28% 24%, rgba(255, 255, 255, 0.98), transparent 34%),
    linear-gradient(160deg, rgba(245, 252, 250, 0.94), rgba(228, 242, 237, 0.78)),
    linear-gradient(135deg, rgba(71, 111, 104, 0.16), rgba(255, 255, 255, 0));
  --rarity-strong-bg: linear-gradient(135deg, #5c877d, #365951);
  --rarity-strong-shadow: rgba(71, 111, 104, 0.28);
}

.progress-panel.epic,
.timeline-card.epic,
.catalog-card.epic,
.reveal-panel.epic,
.seal-icon.epic,
.timeline-seal.epic,
.reveal-seal.epic {
  --rarity-color: #9a753d;
  --rarity-rgb: 154, 117, 61;
  --rarity-border: rgba(154, 117, 61, 0.26);
  --rarity-surface: linear-gradient(180deg, rgba(255, 251, 242, 0.98), rgba(247, 236, 209, 0.95));
  --rarity-surface-strong: linear-gradient(160deg, rgba(255, 252, 244, 0.99), rgba(249, 239, 214, 0.97));
  --rarity-mist:
    radial-gradient(circle at 82% 0%, rgba(222, 189, 116, 0.3), transparent 32%),
    radial-gradient(circle at 16% 100%, rgba(168, 126, 63, 0.12), transparent 32%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.22), rgba(255, 243, 209, 0.04) 42%, transparent 76%);
  --rarity-accent-bg: linear-gradient(135deg, rgba(154, 117, 61, 0.12), rgba(255, 250, 239, 0.92));
  --rarity-accent-border: rgba(154, 117, 61, 0.2);
  --rarity-seal-bg:
    radial-gradient(circle at 28% 24%, rgba(255, 255, 255, 0.98), transparent 34%),
    linear-gradient(160deg, rgba(255, 251, 245, 0.96), rgba(250, 237, 211, 0.82)),
    linear-gradient(135deg, rgba(214, 173, 94, 0.18), rgba(255, 255, 255, 0));
  --rarity-strong-bg: linear-gradient(135deg, #c99b52, #815826);
  --rarity-strong-shadow: rgba(154, 117, 61, 0.32);
}

.progress-panel.legendary,
.timeline-card.legendary,
.catalog-card.legendary,
.reveal-panel.legendary,
.seal-icon.legendary,
.timeline-seal.legendary,
.reveal-seal.legendary {
  --rarity-color: #b94e31;
  --rarity-rgb: 185, 78, 49;
  --rarity-border: rgba(185, 78, 49, 0.28);
  --rarity-surface: linear-gradient(180deg, rgba(255, 248, 244, 0.98), rgba(248, 229, 218, 0.95));
  --rarity-surface-strong: linear-gradient(160deg, rgba(255, 249, 245, 0.99), rgba(249, 231, 221, 0.97));
  --rarity-mist:
    radial-gradient(circle at 84% 0%, rgba(231, 147, 108, 0.34), transparent 32%),
    radial-gradient(circle at 10% 100%, rgba(201, 106, 72, 0.16), transparent 32%),
    linear-gradient(135deg, rgba(255, 248, 226, 0.26), rgba(255, 255, 255, 0.04) 40%, transparent 76%);
  --rarity-accent-bg: linear-gradient(135deg, rgba(185, 78, 49, 0.14), rgba(255, 248, 242, 0.92));
  --rarity-accent-border: rgba(185, 78, 49, 0.22);
  --rarity-seal-bg:
    radial-gradient(circle at 28% 24%, rgba(255, 255, 255, 0.98), transparent 34%),
    linear-gradient(160deg, rgba(255, 250, 246, 0.96), rgba(249, 229, 219, 0.82)),
    linear-gradient(135deg, rgba(216, 124, 87, 0.2), rgba(255, 255, 255, 0));
  --rarity-strong-bg: linear-gradient(135deg, #d46e44, #7b311f);
  --rarity-strong-shadow: rgba(185, 78, 49, 0.34);
}

.progress-panel.epic::before,
.timeline-card.epic::before,
.catalog-card.epic::before,
.reveal-panel.epic::before {
  animation: raritySheen 8s ease-in-out infinite;
}

.progress-panel.legendary::before,
.timeline-card.legendary::before,
.catalog-card.legendary::before,
.reveal-panel.legendary::before {
  animation: rarityPulse 6s ease-in-out infinite;
}

.seal-wrap,
.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.seal-icon,
.timeline-seal,
.catalog-seal,
.reveal-seal {
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-title);
  font-weight: 700;
  color: var(--rarity-color);
  background: var(--rarity-seal-bg);
  border: 1px solid rgba(var(--rarity-rgb), 0.38);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.84),
    0 12px 26px rgba(var(--rarity-rgb), 0.18),
    0 0 0 8px rgba(var(--rarity-rgb), 0.05);
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.52);
}

.seal-icon {
  width: 60px;
  height: 60px;
  border-radius: 20px;
  font-size: 20px;
}

.seal-icon.unlocked {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.88),
    0 16px 32px rgba(var(--rarity-rgb), 0.22),
    0 0 0 10px rgba(var(--rarity-rgb), 0.06);
}

.seal-category {
  font-size: 11px;
  color: rgba(47, 33, 24, 0.48);
}

.progress-panel-main,
.timeline-body {
  flex: 1;
}

.progress-panel-head h3,
.timeline-title-row h3,
.catalog-name {
  font-size: 22px;
}

.progress-panel-desc,
.catalog-desc {
  color: rgba(47, 33, 24, 0.56);
}

.timeline-head p,
.reveal-panel p {
  color: rgba(47, 33, 24, 0.62);
}

.rarity-tag,
.status-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 11px;
}

.rarity-tag {
  color: var(--rarity-color, #7d5937);
  background: var(--rarity-accent-bg);
  border: 1px solid var(--rarity-accent-border);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.status-tag {
  color: rgba(47, 33, 24, 0.5);
  background: rgba(125, 89, 55, 0.08);
}

.status-tag.unlocked {
  color: #3e6d56;
  background: rgba(62, 109, 86, 0.12);
}

.progress-meta-row {
  margin: 16px 0 10px;
}

.progress-meta-row strong {
  color: var(--rarity-color);
}

.progress-fill {
  box-shadow: 0 0 14px rgba(var(--rarity-rgb), 0.22);
}

.progress-fill.common {
  background: linear-gradient(90deg, #9a7454, #6f4f34);
}

.progress-fill.rare {
  background: linear-gradient(90deg, #7cb0a1, #476f68);
}

.progress-fill.epic {
  background: linear-gradient(90deg, #e3c17d, #9a753d);
}

.progress-fill.legendary {
  box-shadow: 0 0 18px rgba(var(--rarity-rgb), 0.26);
  background: linear-gradient(90deg, #ed9a73, #b94e31);
}

.reward-row {
  margin-top: 12px;
  flex-wrap: wrap;
}

.reward-row span {
  padding: 7px 10px;
  border-radius: 999px;
  background: var(--rarity-accent-bg);
  border: 1px solid var(--rarity-accent-border);
  color: var(--rarity-color);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.68);
}

.timeline-list,
.catalog-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.timeline-card {
  display: grid;
  grid-template-columns: 84px minmax(0, 1fr);
  gap: 16px;
  padding: 20px;
  background: var(--rarity-surface-strong);
}

.timeline-seal,
.catalog-seal {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  font-size: 18px;
}

.timeline-head {
  align-items: flex-start;
}

.timeline-reward {
  min-width: 96px;
  padding: 12px 14px;
  border-radius: 18px;
  background: var(--rarity-accent-bg);
  border: 1px solid var(--rarity-accent-border);
  color: var(--rarity-color);
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.74);
}

.timeline-reward strong {
  font-size: 24px;
  color: var(--rarity-color);
}

.catalog-section {
  padding: 20px;
}

.catalog-header {
  flex-direction: row;
  align-items: end;
  justify-content: space-between;
  margin-bottom: 14px;
}

.catalog-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.catalog-card {
  padding: 18px;
  border-radius: 22px;
  border: 1px solid var(--rarity-border);
  background: var(--rarity-surface);
  box-shadow: 0 14px 30px rgba(140, 93, 56, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.46);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.catalog-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 34px rgba(140, 93, 56, 0.1), 0 0 0 1px rgba(var(--rarity-rgb), 0.08);
}

.catalog-card.unlocked {
  background: var(--rarity-surface-strong);
}

.catalog-card-top {
  align-items: center;
  margin-bottom: 12px;
}

.catalog-name {
  margin-bottom: 8px;
  color: #2f2118;
}

.catalog-reward {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 16px;
  font-size: 13px;
  color: var(--rarity-color);
  background: var(--rarity-accent-bg);
  border: 1px solid var(--rarity-accent-border);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.68);
}

.empty-state {
  padding: 48px 20px;
  border-radius: 24px;
  text-align: center;
  color: rgba(47, 33, 24, 0.52);
  background: rgba(255, 255, 255, 0.54);
  border: 1px dashed rgba(124, 90, 55, 0.18);
}

.reveal-mask {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(33, 23, 15, 0.66);
  backdrop-filter: blur(10px);
}

.reveal-panel {
  position: relative;
  width: min(520px, 100%);
  padding: 34px 28px 24px;
  border-radius: 30px;
  background: var(--rarity-surface-strong);
  box-shadow: 0 28px 60px rgba(33, 23, 15, 0.2), 0 0 42px rgba(var(--rarity-rgb), 0.16);
  overflow: hidden;
  text-align: center;
}

.reveal-orbit {
  position: absolute;
  inset: -40px;
  border-radius: 50%;
  border: 1px solid rgba(var(--rarity-rgb), 0.14);
  box-shadow: 0 0 0 18px rgba(var(--rarity-rgb), 0.04);
  animation: orbitSpin 10s linear infinite;
}

.reveal-seal {
  width: 92px;
  height: 92px;
  margin: 18px auto 16px;
  border-radius: 28px;
  font-size: 28px;
}

.reveal-rewards {
  margin: 18px 0 22px;
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.reveal-rewards span {
  padding: 10px 14px;
  border-radius: 999px;
  background: var(--rarity-accent-bg);
  border: 1px solid var(--rarity-accent-border);
  color: var(--rarity-color);
  font-size: 14px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.reveal-btn {
  padding: 11px 18px;
  border-radius: 999px;
  border: none;
  background: var(--rarity-strong-bg);
  color: #fff2dd;
  font-size: 14px;
  box-shadow: 0 12px 24px var(--rarity-strong-shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.reveal-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px var(--rarity-strong-shadow);
}

.reveal-fade-enter-active,
.reveal-fade-leave-active {
  transition: opacity 0.24s ease;
}

.reveal-fade-enter-from,
.reveal-fade-leave-to {
  opacity: 0;
}

@keyframes cardRise {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes barGrow {
  from {
    width: 0 !important;
  }
}

@keyframes orbitSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes raritySheen {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
    opacity: 0.72;
  }
  50% {
    transform: translate3d(-2%, 2%, 0);
    opacity: 1;
  }
}

@keyframes rarityPulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.78;
  }
  50% {
    transform: scale(1.04);
    opacity: 1;
  }
}

@media (max-width: 1180px) {
  .achievements-content {
    grid-template-columns: 1fr;
  }

  .side-column {
    position: static;
    order: 2;
  }

  .main-column {
    order: 1;
  }

  .board-hero {
    grid-template-columns: 1fr;
  }

  .tab-bar {
    justify-content: flex-start;
  }
}

@media (max-width: 820px) {
  .nav-inner,
  .achievements-content {
    padding-left: 18px;
    padding-right: 18px;
  }

  .nav-inner {
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .title-block {
    order: -1;
    width: 100%;
  }

  .hero-ring-wrap {
    grid-template-columns: 1fr;
  }

  .hero-totals {
    grid-template-columns: 1fr;
  }

  .timeline-card {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-title {
    font-size: 22px;
    letter-spacing: 0.18em;
  }

  .hero-title,
  .board-title {
    font-size: 26px;
  }

  .progress-grid,
  .catalog-cards {
    grid-template-columns: 1fr;
  }

  .progress-panel-top,
  .timeline-head,
  .catalog-card-top,
  .filter-chip-top,
  .progress-panel-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .reward-row,
  .timeline-meta,
  .catalog-meta,
  .reveal-footer,
  .rank-progress-top,
  .rank-progress-bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}

.empty-state-hint {
  font-size: 13px;
  color: rgba(47, 33, 24, 0.45);
  margin-top: 6px;
  line-height: 1.6;
}

.empty-state-actions {
  display: flex;
  gap: 10px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.empty-state-btn {
  padding: 8px 20px;
  border-radius: 999px;
  font-size: 13px;
  font-family: var(--font-title);
  letter-spacing: 0.06em;
  text-decoration: none;
  background: rgba(255, 251, 245, 0.9);
  border: 1px solid rgba(124, 90, 55, 0.16);
  color: rgba(47, 33, 24, 0.7);
  transition: all 0.2s ease;
}

.empty-state-btn:hover {
  border-color: rgba(212, 85, 61, 0.3);
  color: #d4553d;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(212, 85, 61, 0.08);
}
</style>
