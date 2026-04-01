<template>
  <div class="poems-page">
    <div class="ink-wash-bg"></div>

    <nav class="poems-nav" :class="{ scrolled: isScrolled }">
      <div class="nav-inner">
        <div class="nav-left">
          <button class="back-btn" @click="goHome">
            <span class="back-arrow">←</span>
            <span>返回</span>
          </button>
          <span class="nav-title">诗词学堂</span>
        </div>
        <div class="nav-right">
          <template v-if="userStore.isLogin && userStore.userInfo">
            <UserAvatar
              :username="userStore.userInfo.username"
              :avatar="userStore.userInfo.avatar_url"
              :clickable="true"
            />
          </template>
          <template v-else>
            <button class="back-btn" @click="$router.push('/login')">登录</button>
          </template>
        </div>
      </div>
    </nav>

    <div class="poems-content">
      <div class="page-header">
        <div class="header-seal">诗</div>
        <div class="page-header__content">
          <h1 class="page-title">诗词学堂</h1>
          <p class="page-subtitle">万首唐诗宋词，尽在指尖</p>
          <div class="header-line">
            <span class="header-line-segment"></span>
            <span class="header-line-dot"></span>
            <span class="header-line-segment"></span>
          </div>
        </div>
      </div>

      <section class="catalog-panel">
        <div class="catalog-panel__aside">
          <div class="catalog-panel__heading">
            <p class="catalog-panel__eyebrow">CATALOG FILTERS</p>
            <h2 class="catalog-panel__title">卷轴检索台</h2>
          </div>

          <p class="catalog-panel__note">
            关键词检索与书目筛选分开使用，切换模式时会自动清空另一组条件。
          </p>

          <div v-if="activeConditions.length" class="active-conditions">
            <span class="active-conditions__label">当前书目</span>
            <span v-for="item in activeConditions" :key="item" class="active-conditions__chip">{{ item }}</span>
          </div>

          <div class="catalog-panel__actions">
            <button type="button" class="catalog-panel__random" @click="openRandomPoem" :disabled="loadingRandomPoem">
              {{ loadingRandomPoem ? '寻卷中' : '随机读诗' }}
            </button>
            <button
              v-if="hasActiveConditions"
              type="button"
              class="catalog-panel__reset"
              @click="resetFilters"
            >
              清空条件
            </button>
          </div>
        </div>

        <div class="catalog-panel__main">
          <div class="catalog-panel__search">
            <div class="search-box">
              <span class="search-icon">寻</span>
              <input
                v-model="searchKeyword"
                class="search-input"
                :placeholder="searchPlaceholder"
                @keyup.enter="handleSearch"
              />
            </div>

            <div class="search-tools">
              <div class="search-type-group">
                <button
                  v-for="t in searchTypes"
                  :key="t.value"
                  class="search-type-btn"
                  :class="{ active: searchType === t.value }"
                  @click="searchType = t.value"
                >{{ t.label }}</button>
              </div>
              <button type="button" class="search-submit-btn" @click="handleSearch">检索</button>
            </div>
          </div>

          <div class="facet-rows">
            <div class="facet-row">
              <span class="facet-row__label">朝代</span>
              <div class="facet-row__tags">
                <button
                  class="facet-chip"
                  :class="{ active: !filters.dynasty }"
                  @click="setDynasty('')"
                >全部</button>
                <button
                  v-for="d in dynasties"
                  :key="d"
                  class="facet-chip"
                  :class="{ active: filters.dynasty === d }"
                  @click="setDynasty(d)"
                >{{ d }}</button>
              </div>
            </div>
            <div class="facet-row">
              <span class="facet-row__label">题材</span>
              <div class="facet-row__tags">
                <button
                  class="facet-chip"
                  :class="{ active: !filters.category }"
                  @click="setCategory('')"
                >全部</button>
                <button
                  v-for="c in presetCategories"
                  :key="c"
                  class="facet-chip"
                  :class="{ active: filters.category === c }"
                  @click="setCategory(c)"
                >{{ c }}</button>
              </div>
            </div>
            <div class="facet-row">
              <span class="facet-row__label">体裁</span>
              <div class="facet-row__tags">
                <button
                  class="facet-chip"
                  :class="{ active: !filters.genre }"
                  @click="setGenre('')"
                >全部</button>
                <button
                  v-for="g in presetGenres"
                  :key="g"
                  class="facet-chip"
                  :class="{ active: filters.genre === g }"
                  @click="setGenre(g)"
                >{{ g }}</button>
              </div>
            </div>
            <div class="facet-row">
              <span class="facet-row__label">作者</span>
              <div class="facet-row__tags facet-row__tags--scrollable">
                <button
                  class="facet-chip"
                  :class="{ active: !activeAuthorSelection }"
                  @click="clearAuthorSelection"
                >不限</button>
                <button
                  v-for="a in presetAuthors"
                  :key="a"
                  class="facet-chip"
                  :class="{ active: activeAuthorSelection === a }"
                  @click="searchByAuthor(a)"
                >{{ a }}</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="results-info" v-if="total > 0 || hasActiveConditions">
        <span class="results-count">共 <em>{{ total.toLocaleString() }}</em> 首诗词</span>
        <span class="results-mode">{{ resultDescriptor }}</span>
      </div>

      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <span class="loading-text">正在加载诗词...</span>
      </div>

      <div v-else-if="poems.length === 0" class="empty-state">
        <div class="empty-icon">卷</div>
        <p class="empty-text">{{ emptyStateText }}</p>
        <button class="empty-action" @click="resetFilters">清除筛选</button>
      </div>

      <div v-else class="poems-grid">
        <div
          v-for="poem in poems"
          :key="poem.id"
          class="poem-card"
          @click="goToDetail(poem.id)"
        >
          <div class="poem-card-header">
            <h3 class="poem-card-title">{{ poem.title }}</h3>
            <span class="poem-card-dynasty">{{ poem.dynasty }}</span>
          </div>
          <div class="poem-card-author">{{ poem.author }}</div>
          <div v-if="poem.category || poem.genre" class="poem-card-labels">
            <span v-if="poem.category" class="poem-card-label">{{ poem.category }}</span>
            <span v-if="poem.genre" class="poem-card-label poem-card-label--secondary">{{ poem.genre }}</span>
          </div>
          <div class="poem-card-content">{{ formatContent(poem.content) }}</div>
          <div class="poem-card-footer">
            <span class="poem-stat">
              <span class="poem-stat-icon">阅</span>
              {{ poem.view_count }}
            </span>
            <span class="poem-stat">
              <span class="poem-stat-icon">藏</span>
              {{ poem.favorite_count }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button class="page-btn" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">‹</button>
        <template v-for="p in paginationRange" :key="p">
          <button v-if="p !== '...'" class="page-btn" :class="{ active: p === currentPage }" @click="goPage(p as number)">{{ p }}</button>
          <span v-else class="page-ellipsis">...</span>
        </template>
        <button class="page-btn" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">›</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { poemApi, type Poem } from '@/api/poem'
import { poetApi, type PoetListItem } from '@/api/poet'
import { useUserStore } from '@/store/modules/user'
import UserAvatar from '@/components/UserAvatar.vue'

type SearchType = 'title' | 'author' | 'content'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const poems = ref<Poem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const isScrolled = ref(false)
const loadingRandomPoem = ref(false)
const searchKeyword = ref('')
const searchType = ref<SearchType>('title')
const filters = ref({
  dynasty: '',
  category: '',
  genre: ''
})

const dynasties = ['唐', '宋']
const presetCategories = ['山水', '田园', '边塞', '思乡', '送别', '咏物', '怀古', '抒情']
const presetGenres = ['五言绝句', '七言绝句', '五言律诗', '七言律诗', '词', '曲']
const fallbackAuthors = ['李白', '杜甫', '王维', '白居易', '苏轼', '李清照', '辛弃疾', '李商隐']
const dynamicAuthors = ref<string[]>([...fallbackAuthors])
const presetAuthors = computed(() => dynamicAuthors.value)

const searchTypes: Array<{ label: string; value: SearchType }> = [
  { label: '标题', value: 'title' as const },
  { label: '作者', value: 'author' as const },
  { label: '内容', value: 'content' as const }
]

const searchPlaceholder = computed(() => {
  const map: Record<string, string> = {
    title: '搜索诗词标题...',
    author: '搜索作者...',
    content: '搜索诗句内容...'
  }
  return map[searchType.value]
})

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const hasKeywordSearch = computed(() => Boolean(searchKeyword.value.trim()))

const hasActiveConditions = computed(() => {
  return Boolean(
    searchKeyword.value.trim() ||
    filters.value.dynasty ||
    filters.value.category ||
    filters.value.genre
  )
})

const activeAuthorSelection = computed(() => {
  if (searchType.value !== 'author') return ''
  return searchKeyword.value.trim()
})

const getSearchTypeLabel = (value: SearchType) => {
  return searchTypes.find(item => item.value === value)?.label || '标题'
}

const activeConditions = computed(() => {
  if (hasKeywordSearch.value) {
    return [`${getSearchTypeLabel(searchType.value)}检索`, `关键词：${searchKeyword.value.trim()}`]
  }

  const items: string[] = []

  if (filters.value.dynasty) items.push(`${filters.value.dynasty}代`)
  if (filters.value.category) items.push(filters.value.category)
  if (filters.value.genre) items.push(filters.value.genre)

  return items
})

const resultDescriptor = computed(() => {
  if (hasKeywordSearch.value) {
    return `按${getSearchTypeLabel(searchType.value)}检索`
  }

  if (activeConditions.value.length) {
    return activeConditions.value.join(' · ')
  }

  return '默认书目'
})

const emptyStateText = computed(() => {
  if (hasKeywordSearch.value) return '未找到匹配的诗词卷目'
  if (hasActiveConditions.value) return '当前筛选条件下暂无诗词'
  return '未找到相关诗词'
})

const paginationRange = computed(() => {
  const range: (number | string)[] = []
  const tp = totalPages.value
  const cp = currentPage.value

  if (tp <= 7) {
    for (let i = 1; i <= tp; i++) range.push(i)
    return range
  }

  range.push(1)
  if (cp > 3) range.push('...')

  const start = Math.max(2, cp - 1)
  const end = Math.min(tp - 1, cp + 1)

  for (let i = start; i <= end; i++) range.push(i)

  if (cp < tp - 2) range.push('...')
  range.push(tp)

  return range
})

const formatContent = (content: string) => {
  return content.replace(/\n/g, ' ').substring(0, 80)
}

const readQueryString = (value: unknown) => {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value[0] || ''
  return ''
}

const isSearchType = (value: string): value is SearchType => {
  return ['title', 'author', 'content'].includes(value)
}

const syncRouteQuery = () => {
  const query: Record<string, string> = {}
  const keyword = searchKeyword.value.trim()

  if (keyword) {
    query.q = keyword
    query.searchType = searchType.value
  } else {
    if (filters.value.dynasty) query.dynasty = filters.value.dynasty
    if (filters.value.category) query.category = filters.value.category
    if (filters.value.genre) query.genre = filters.value.genre
  }

  if (currentPage.value > 1) {
    query.page = String(currentPage.value)
  }

  router.replace({ query })
}

const loadPoems = async () => {
  loading.value = true
  const keyword = searchKeyword.value.trim()
  syncRouteQuery()

  try {
    if (keyword) {
      const data = await poemApi.search({
        keyword,
        search_type: searchType.value,
        page: currentPage.value,
        page_size: pageSize
      })
      poems.value = data.items
      total.value = data.total
    } else {
      const params: Record<string, any> = {
        page: currentPage.value,
        page_size: pageSize
      }
      if (filters.value.dynasty) params.dynasty = filters.value.dynasty
      if (filters.value.category) params.category = filters.value.category
      if (filters.value.genre) params.genre = filters.value.genre

      const data = await poemApi.getList(params)
      poems.value = data.items
      total.value = data.total
    }
  } catch (error) {
    console.error('加载诗词失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  currentPage.value = 1

  if (keyword) {
    searchKeyword.value = keyword
    filters.value = {
      dynasty: '',
      category: '',
      genre: ''
    }
  }

  loadPoems()
}

const loadPopularPoets = async (dynasty?: string) => {
  try {
    const res = await poetApi.getPoets({
      page: 1,
      page_size: 12,
      dynasty: dynasty || undefined
    })
    if (res.items.length > 0) {
      dynamicAuthors.value = res.items.map((p: PoetListItem) => p.name)
    } else {
      dynamicAuthors.value = [...fallbackAuthors]
    }
  } catch {
    dynamicAuthors.value = [...fallbackAuthors]
  }
}

const setDynasty = (dynasty: string) => {
  filters.value.dynasty = dynasty
  searchKeyword.value = ''
  currentPage.value = 1
  loadPoems()
  loadPopularPoets(dynasty)
}

const setCategory = (category: string) => {
  filters.value.category = category
  searchKeyword.value = ''
  currentPage.value = 1
  loadPoems()
}

const setGenre = (genre: string) => {
  filters.value.genre = genre
  searchKeyword.value = ''
  currentPage.value = 1
  loadPoems()
}

const searchByAuthor = (author: string) => {
  searchType.value = 'author'
  searchKeyword.value = author
  currentPage.value = 1
  filters.value = {
    dynasty: '',
    category: '',
    genre: ''
  }
  loadPoems()
}

const clearAuthorSelection = () => {
  if (!activeAuthorSelection.value) {
    return
  }

  searchKeyword.value = ''
  searchType.value = 'title'
  currentPage.value = 1
  loadPoems()
}

const resetFilters = () => {
  filters.value = { dynasty: '', category: '', genre: '' }
  searchKeyword.value = ''
  searchType.value = 'title'
  currentPage.value = 1
  loadPoems()
}

const openRandomPoem = async () => {
  try {
    loadingRandomPoem.value = true
    const randomPoem = await poemApi.getRandom(filters.value.dynasty || undefined)
    router.push(`/poems/${randomPoem.id}`)
  } catch (error) {
    console.error('随机诗词加载失败:', error)
  } finally {
    loadingRandomPoem.value = false
  }
}

const goPage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadPoems()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const goToDetail = (id: number) => {
  router.push(`/poems/${id}`)
}

const goHome = () => {
  router.push('/')
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 20
}

onMounted(() => {
  const queryPage = Number(readQueryString(route.query.page))
  if (Number.isInteger(queryPage) && queryPage > 0) {
    currentPage.value = queryPage
  }

  const queryKeyword = readQueryString(route.query.q).trim()

  if (queryKeyword) {
    searchKeyword.value = queryKeyword

    const querySearchType = readQueryString(route.query.searchType)
    if (isSearchType(querySearchType)) {
      searchType.value = querySearchType
    }
  } else {
    filters.value.dynasty = readQueryString(route.query.dynasty)
    filters.value.category = readQueryString(route.query.category)
    filters.value.genre = readQueryString(route.query.genre)
  }

  loadPoems()
  loadPopularPoets(filters.value.dynasty || undefined)
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped src="./styles/list.css"></style>
