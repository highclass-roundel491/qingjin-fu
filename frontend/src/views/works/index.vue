<template>
  <div class="works-page">
    <div class="ink-bg">
      <div class="ink-wash ink-wash--1"></div>
      <div class="ink-wash ink-wash--2"></div>
    </div>

    <nav class="page-nav">
      <router-link to="/" class="nav-back">← 首页</router-link>
      <span class="nav-title">作品展示墙</span>
      <div class="nav-right">
        <router-link v-if="userStore.isLogin" to="/works/drafts" class="btn-drafts">
          <span class="btn-drafts__icon">笿</span>
          <span class="btn-drafts__text">草稿箱</span>
          <span v-if="draftCount > 0" class="btn-drafts__badge">{{ draftCount }}</span>
        </router-link>
        <router-link to="/works/rankings" class="btn-rankings">🏆 排行榜</router-link>
        <router-link to="/works/create" class="btn-create">+ 开始创作</router-link>
      </div>
    </nav>

    <main class="page-body">
      <section class="intro-panel">
        <div class="intro-panel__main">
          <span class="intro-panel__badge">{{ introBadge }}</span>
          <h1 class="intro-panel__title">{{ introTitle }}</h1>
          <p class="intro-panel__desc">{{ introDescription }}</p>
        </div>
        <div class="intro-panel__actions">
          <button type="button" class="intro-panel__action intro-panel__action--primary" @click="handleIntroPrimary">{{ introPrimaryLabel }}</button>
          <button type="button" class="intro-panel__action" @click="handleIntroSecondary">{{ introSecondaryLabel }}</button>
        </div>
      </section>

      <div class="controls-bar">
        <div class="sort-tabs">
          <button
            v-for="s in sortOptions"
            :key="s.value"
            class="sort-tab"
            :class="{ 'sort-tab--active': currentSort === s.value }"
            @click="changeSort(s.value)"
          >{{ s.label }}</button>
        </div>
        <div class="genre-filter">
          <button
            class="filter-chip"
            :class="{ 'filter-chip--active': !currentGenre }"
            @click="changeGenre('')"
          >全部</button>
          <button
            v-for="g in genreList"
            :key="g"
            class="filter-chip"
            :class="{ 'filter-chip--active': currentGenre === g }"
            @click="changeGenre(g)"
          >{{ g }}</button>
        </div>
      </div>

      <div class="results-strip">
        <div class="results-strip__headline">{{ resultsHeadline }}</div>
        <div class="results-strip__chips">
          <span class="results-strip__chip">排序：{{ currentSortLabel }}</span>
          <span class="results-strip__chip">体裁：{{ currentGenreLabel }}</span>
          <span v-if="userStore.isLogin" class="results-strip__chip">草稿：{{ draftCount }} 篇</span>
        </div>
      </div>

      <div v-if="loading && works.length === 0" class="loading-state">
        <div class="loading-dot"></div>
        <span>加载中…</span>
      </div>

      <div v-else-if="works.length === 0" class="empty-state">
        <div class="empty-glyph">墨</div>
        <h3 class="empty-state__title">{{ emptyTitle }}</h3>
        <p class="empty-state__desc">{{ emptyDescription }}</p>
        <div class="empty-state__actions">
          <button type="button" class="empty-action" @click="handleEmptyPrimary">{{ emptyPrimaryLabel }}</button>
          <button type="button" class="empty-secondary" @click="handleEmptySecondary">{{ emptySecondaryLabel }}</button>
        </div>
      </div>

      <div v-else class="works-grid">
        <article
          v-for="work in works"
          :key="work.id"
          class="work-card"
          @click="goDetail(work.id)"
        >
          <div class="work-card__seal">{{ work.genre.charAt(0) }}</div>
          <div class="work-card__header">
            <div class="work-card__author">
              <UserAvatar
                :username="work.username"
                :avatar="work.avatar_url"
                size="small"
              />
              <span class="work-card__author-name">{{ work.username }}</span>
            </div>
            <span v-if="work.ai_total_score" class="work-card__score">{{ work.ai_total_score }}分</span>
          </div>
          <h3 class="work-card__title">{{ work.title }}</h3>
          <p class="work-card__preview">{{ truncateContent(work.content) }}</p>
          <div class="work-card__genre">{{ work.genre }}</div>
          <div class="work-card__footer">
            <button
              class="work-card__like"
              :class="{ 'work-card__like--active': work.is_liked }"
              @click.stop="toggleLike(work)"
            >
              ♥ {{ work.like_count }}
            </button>
            <span class="work-card__views">{{ work.view_count }} 阅读</span>
          </div>
        </article>
      </div>

      <div v-if="hasMore" class="load-more">
        <button class="btn-load-more" @click="loadMore" :disabled="loading">
          {{ loading ? '加载中…' : '加载更多' }}
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { worksApi, type WorkItem } from '@/api/works'
import { useUserStore } from '@/store/modules/user'
import UserAvatar from '@/components/UserAvatar.vue'

const router = useRouter()
const userStore = useUserStore()
const draftCount = ref(0)

const sortOptions = [
  { value: 'new', label: '最新' },
  { value: 'hot', label: '最热' },
  { value: 'score', label: '高分' },
]

const genreList = ['五言绝句', '七言绝句', '五言律诗', '七言律诗', '词', '自由体']

const works = ref<WorkItem[]>([])
const currentSort = ref('new')
const currentGenre = ref('')
const page = ref(1)
const total = ref(0)
const loading = ref(false)

const hasMore = computed(() => works.value.length < total.value)

const hasActiveFilters = computed(() => Boolean(currentGenre.value) || currentSort.value !== 'new')

const currentSortLabel = computed(() => {
  return sortOptions.find(option => option.value === currentSort.value)?.label || '最新'
})

const currentGenreLabel = computed(() => currentGenre.value || '全部')

const introBadge = computed(() => {
  if (!userStore.isLogin) return '初到作品墙'
  if (draftCount.value > 0) return '续写新作'
  return '作品漫游'
})

const introTitle = computed(() => {
  if (!userStore.isLogin) {
    return '先看看同伴都在写什么，再决定你的第一笔'
  }

  if (draftCount.value > 0) {
    return '你的草稿还在等下一句，不妨顺手把它写完'
  }

  return '逛逛作品墙，感受别人的笔意，也写下你的这一篇'
})

const introDescription = computed(() => {
  if (!userStore.isLogin) {
    return '这里汇集了大家公开发布的诗词作品。你可以先逛作品墙、看排行榜；等准备好留下自己的痕迹，再注册开启卷宗。'
  }

  if (draftCount.value > 0) {
    return '你已经有可继续完善的草稿，也可以先浏览作品墙找灵感，再回去润色、发布。'
  }

  return '如果刚写完第一篇，可以回来看看大家的表达方式；如果还没开始，也可以先逛一圈再进入创作页。'
})

const introPrimaryLabel = computed(() => {
  if (!userStore.isLogin) return '注册后开始创作'
  if (draftCount.value > 0) return '回草稿箱继续'
  return '开始创作'
})

const introSecondaryLabel = computed(() => {
  if (userStore.isLogin && draftCount.value > 0) return '发布一篇新作'
  return '看看排行榜'
})

const resultsHeadline = computed(() => {
  if (hasActiveFilters.value) {
    return `当前筛选下共有 ${total.value} 篇作品`
  }

  return `作品墙已陈列 ${total.value} 篇作品`
})

const emptyTitle = computed(() => {
  if (hasActiveFilters.value) {
    return '当前筛选下还没有匹配作品'
  }

  if (!userStore.isLogin) {
    return '作品墙正在静候更多新作'
  }

  return draftCount.value > 0 ? '先把草稿打磨成作品吧' : '这面作品墙正在等你题下第一笔'
})

const emptyDescription = computed(() => {
  if (hasActiveFilters.value) {
    return '可以切回全部体裁或默认排序，也可以直接去写一篇新作，成为这组筛选里的第一位作者。'
  }

  if (!userStore.isLogin) {
    return '先看看排行榜和大家的表达方式，等你注册后，也能把自己的作品挂上这面墙。'
  }

  if (draftCount.value > 0) {
    return '你已经有可继续完善的草稿了，把它补完并发布后，就能出现在这里。'
  }

  return '如果你刚完成首页和创作页体验，现在正适合把第一篇作品写出来，再回来看看它如何陈列在作品墙。'
})

const emptyPrimaryLabel = computed(() => {
  if (hasActiveFilters.value) return '清除筛选'
  if (!userStore.isLogin) return '先注册再创作'
  if (draftCount.value > 0) return '去草稿箱'
  return '去写第一篇'
})

const emptySecondaryLabel = computed(() => {
  if (hasActiveFilters.value && userStore.isLogin) return '去写新作'
  return '看看排行榜'
})

async function fetchWorks(reset = false) {
  if (reset) {
    page.value = 1
    works.value = []
  }
  loading.value = true
  try {
    const res = await worksApi.getWorks({
      sort: currentSort.value,
      genre: currentGenre.value || undefined,
      page: page.value,
      page_size: 12
    })
    if (reset) {
      works.value = res.items
    } else {
      works.value.push(...res.items)
    }
    total.value = res.total
  } catch {}
  loading.value = false
}

function changeSort(val: string) {
  currentSort.value = val
  fetchWorks(true)
}

function changeGenre(val: string) {
  currentGenre.value = val
  fetchWorks(true)
}

function loadMore() {
  page.value++
  fetchWorks()
}

function goToCreate() {
  router.push('/works/create')
}

function goToDrafts() {
  router.push('/works/drafts')
}

function goToRankings() {
  router.push('/works/rankings')
}

function goToRegister() {
  router.push('/register')
}

function clearFilters() {
  currentSort.value = 'new'
  currentGenre.value = ''
  fetchWorks(true)
}

function handleIntroPrimary() {
  if (!userStore.isLogin) {
    goToRegister()
    return
  }

  if (draftCount.value > 0) {
    goToDrafts()
    return
  }

  goToCreate()
}

function handleIntroSecondary() {
  if (userStore.isLogin && draftCount.value > 0) {
    goToCreate()
    return
  }

  goToRankings()
}

function handleEmptyPrimary() {
  if (hasActiveFilters.value) {
    clearFilters()
    return
  }

  if (!userStore.isLogin) {
    goToRegister()
    return
  }

  if (draftCount.value > 0) {
    goToDrafts()
    return
  }

  goToCreate()
}

function handleEmptySecondary() {
  if (hasActiveFilters.value && userStore.isLogin) {
    goToCreate()
    return
  }

  goToRankings()
}

function goDetail(id: number) {
  router.push(`/works/${id}`)
}

function truncateContent(content: string) {
  const lines = content.split('\n').filter(l => l.trim())
  const preview = lines.slice(0, 2).join('　')
  return preview.length > 40 ? preview.slice(0, 40) + '…' : preview
}

async function toggleLike(work: WorkItem) {
  try {
    if (work.is_liked) {
      await worksApi.unlikeWork(work.id)
      work.is_liked = false
      work.like_count = Math.max(0, work.like_count - 1)
    } else {
      await worksApi.likeWork(work.id)
      work.is_liked = true
      work.like_count++
    }
  } catch {}
}

onMounted(async () => {
  fetchWorks(true)
  if (userStore.isLogin) {
    try {
      const res = await worksApi.getMyWorks({ status: 'draft', page_size: 1 })
      draftCount.value = res.total
    } catch {}
  }
})
</script>

<style scoped>
.works-page {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(170deg, #f6f1e8 0%, #fdfefe 40%, #f0ebe2 100%);
}

.ink-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.ink-wash {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}

.ink-wash--1 {
  width: 500px;
  height: 500px;
  top: -150px;
  left: -100px;
  background: radial-gradient(circle, rgba(192,57,43,0.3), transparent 70%);
}

.ink-wash--2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  right: -80px;
  background: radial-gradient(circle, rgba(22,160,133,0.25), transparent 70%);
}

.page-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 32px;
  background: rgba(253,254,254,0.88);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(44,62,80,0.06);
}

.nav-back {
  font-size: 0.92rem;
  color: var(--color-ink-medium);
  text-decoration: none;
}

.nav-back:hover {
  color: var(--color-vermilion);
}

.nav-title {
  font-family: var(--font-poem);
  font-size: 1.15rem;
  letter-spacing: 0.2em;
  color: var(--color-ink-dark);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-drafts {
  position: relative;
  height: 36px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  font-size: 0.86rem;
  text-decoration: none;
  background: rgba(44,62,80,0.06);
  color: var(--color-ink-medium);
  border: 1px solid rgba(44,62,80,0.08);
  transition: all var(--transition-fast);
}

.btn-drafts:hover {
  background: rgba(44,62,80,0.1);
  border-color: rgba(44,62,80,0.14);
  color: var(--color-ink-dark);
}

.btn-drafts__icon {
  font-family: var(--font-poem);
  font-size: 0.92rem;
  opacity: 0.7;
}

.btn-drafts__text {
  font-weight: 500;
}

.btn-drafts__badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  background: var(--color-vermilion);
  color: #fff;
  line-height: 1;
}

.btn-rankings {
  height: 36px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 999px;
  font-size: 0.86rem;
  font-weight: 500;
  text-decoration: none;
  background: rgba(196,151,56,0.08);
  color: #C49738;
  border: 1px solid rgba(196,151,56,0.18);
  transition: all var(--transition-fast);
}

.btn-rankings:hover {
  background: rgba(196,151,56,0.14);
  border-color: rgba(196,151,56,0.3);
}

.btn-create {
  height: 36px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  border-radius: 999px;
  font-size: 0.88rem;
  font-weight: 600;
  text-decoration: none;
  background: linear-gradient(135deg, var(--color-vermilion), #b73325);
  color: #fff;
  box-shadow: 0 4px 14px rgba(192,57,43,0.2);
  transition: all var(--transition-fast);
}

.btn-create:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(192,57,43,0.28);
}

.page-body {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 28px 32px;
}

.intro-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 24px 26px;
  margin-bottom: 20px;
  border-radius: 26px;
  border: 1px solid rgba(44,62,80,0.07);
  background:
    radial-gradient(circle at top right, rgba(192,57,43,0.08), transparent 38%),
    linear-gradient(135deg, rgba(255,255,255,0.84), rgba(250,245,238,0.92));
  box-shadow: 0 18px 40px rgba(44,62,80,0.06);
}

.intro-panel__main {
  flex: 1;
}

.intro-panel__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(192,57,43,0.1);
  color: var(--color-vermilion);
  font-size: 0.74rem;
  letter-spacing: 0.12em;
}

.intro-panel__title {
  margin-top: 12px;
  font-family: var(--font-title);
  font-size: 1.5rem;
  line-height: 1.35;
  color: var(--color-ink-dark);
}

.intro-panel__desc {
  margin-top: 8px;
  font-size: 0.92rem;
  line-height: 1.8;
  color: rgba(52,73,94,0.68);
}

.intro-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.intro-panel__action {
  min-height: 38px;
  padding: 0 18px;
  border-radius: 999px;
  border: 1px solid rgba(44,62,80,0.1);
  background: rgba(255,255,255,0.76);
  color: var(--color-ink-dark);
  font-size: 0.86rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.intro-panel__action:hover {
  transform: translateY(-1px);
  border-color: rgba(192,57,43,0.16);
  color: var(--color-vermilion);
}

.intro-panel__action--primary {
  border-color: transparent;
  background: linear-gradient(135deg, var(--color-vermilion), #b73325);
  color: #fff;
  box-shadow: 0 8px 18px rgba(192,57,43,0.2);
}

.intro-panel__action--primary:hover {
  color: #fff;
  box-shadow: 0 12px 22px rgba(192,57,43,0.26);
}

.controls-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 28px;
}

.results-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
  padding: 14px 18px;
  border-radius: 18px;
  background: rgba(255,255,255,0.64);
  border: 1px solid rgba(44,62,80,0.06);
}

.results-strip__headline {
  font-size: 0.9rem;
  color: var(--color-ink-dark);
}

.results-strip__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.results-strip__chip {
  min-height: 28px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: rgba(44,62,80,0.05);
  color: rgba(52,73,94,0.66);
  font-size: 0.76rem;
}

.sort-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: 14px;
  background: rgba(255,255,255,0.6);
  border: 1px solid rgba(44,62,80,0.06);
}

.sort-tab {
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 0.88rem;
  color: var(--color-ink-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
  background: transparent;
}

.sort-tab:hover {
  color: var(--color-ink-dark);
}

.sort-tab--active {
  background: var(--color-ink-dark);
  color: #fff;
  box-shadow: 0 2px 8px rgba(44,62,80,0.15);
}

.genre-filter {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-chip {
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 0.82rem;
  border: 1px solid rgba(44,62,80,0.1);
  background: rgba(255,255,255,0.5);
  color: var(--color-ink-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-chip:hover {
  border-color: rgba(192,57,43,0.2);
}

.filter-chip--active {
  background: rgba(192,57,43,0.08);
  border-color: var(--color-vermilion);
  color: var(--color-vermilion);
}

.works-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.work-card {
  position: relative;
  padding: 24px;
  border-radius: 20px;
  background: rgba(255,255,255,0.82);
  border: 1px solid rgba(44,62,80,0.07);
  box-shadow: 0 12px 32px rgba(44,62,80,0.06);
  cursor: pointer;
  transition: all var(--transition-normal);
  overflow: hidden;
}

.work-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 48px rgba(44,62,80,0.12);
  border-color: rgba(192,57,43,0.12);
}

.work-card__seal {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-family: var(--font-poem);
  font-size: 0.9rem;
  color: rgba(192,57,43,0.65);
  background: rgba(255,247,244,0.7);
  border: 1px solid rgba(192,57,43,0.12);
  transform: rotate(6deg);
}

.work-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.work-card__author {
  display: flex;
  align-items: center;
  gap: 8px;
}

.work-card__author-name {
  font-size: 0.85rem;
  color: var(--color-ink-medium);
}

.work-card__score {
  font-size: 0.82rem;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(22,160,133,0.1);
  color: var(--color-cyan);
  font-weight: 600;
}

.work-card__title {
  font-family: var(--font-title);
  font-size: 1.15rem;
  color: var(--color-ink-dark);
  margin-bottom: 10px;
  line-height: 1.4;
}

.work-card__preview {
  font-family: var(--font-poem);
  font-size: 0.92rem;
  line-height: 1.8;
  color: rgba(44,62,80,0.72);
  margin-bottom: 12px;
  min-height: 2.6em;
}

.work-card__genre {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  background: rgba(44,62,80,0.05);
  color: rgba(52,73,94,0.65);
  margin-bottom: 14px;
}

.work-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 14px;
  border-top: 1px solid rgba(44,62,80,0.06);
}

.work-card__like {
  font-size: 0.85rem;
  color: rgba(52,73,94,0.6);
  cursor: pointer;
  transition: color var(--transition-fast);
  border: none;
  background: transparent;
  padding: 0;
}

.work-card__like:hover,
.work-card__like--active {
  color: var(--color-vermilion);
}

.work-card__views {
  font-size: 0.82rem;
  color: rgba(52,73,94,0.5);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 80px 0;
  color: rgba(52,73,94,0.5);
  font-size: 0.92rem;
}

.loading-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-vermilion);
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(0.8); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 0;
  gap: 14px;
  text-align: center;
}

.empty-glyph {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(44,62,80,0.04);
  font-family: var(--font-poem);
  font-size: 2rem;
  color: rgba(44,62,80,0.18);
}

.empty-state p {
  color: rgba(52,73,94,0.5);
}

.empty-state__title {
  font-family: var(--font-title);
  font-size: 1.22rem;
  color: var(--color-ink-dark);
}

.empty-state__desc {
  max-width: 560px;
  color: rgba(52,73,94,0.62);
  line-height: 1.8;
}

.empty-state__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.empty-action {
  margin-top: 8px;
  padding: 10px 24px;
  border-radius: 999px;
  background: var(--color-vermilion);
  color: #fff;
  font-size: 0.9rem;
  transition: all var(--transition-fast);
  border: none;
  cursor: pointer;
}

.empty-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(192,57,43,0.25);
}

.empty-secondary {
  margin-top: 8px;
  padding: 10px 24px;
  border-radius: 999px;
  background: rgba(255,255,255,0.76);
  color: var(--color-ink-medium);
  font-size: 0.9rem;
  transition: all var(--transition-fast);
  border: 1px solid rgba(44,62,80,0.12);
  cursor: pointer;
}

.empty-secondary:hover {
  transform: translateY(-1px);
  border-color: rgba(192,57,43,0.16);
  color: var(--color-vermilion);
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

.btn-load-more {
  padding: 12px 32px;
  border-radius: 999px;
  font-size: 0.9rem;
  border: 1px solid rgba(44,62,80,0.12);
  background: rgba(255,255,255,0.7);
  color: var(--color-ink-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-load-more:hover:not(:disabled) {
  background: rgba(255,255,255,0.95);
  border-color: rgba(192,57,43,0.2);
}

.btn-load-more:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .works-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .works-grid {
    grid-template-columns: 1fr;
  }

  .page-body {
    padding: 20px 16px;
  }

  .intro-panel,
  .intro-panel__actions,
  .empty-state__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .controls-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .intro-panel__action,
  .empty-action,
  .empty-secondary {
    width: 100%;
  }
}
</style>
