<template>
  <div class="graph-page" ref="pageRef">
    <div class="graph-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M10 12L6 8L10 4"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <span>返回</span>
        </button>
        <div class="page-title-group">
          <span class="page-seal">文脉星图</span>
          <span class="page-subtitle">诗云关系星云网络</span>
        </div>
      </div>

      <div class="header-right">
        <div class="search-box" ref="searchBoxRef">
          <svg class="search-icon" width="14" height="14" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5" />
            <path d="M11 11L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
          <input
            v-model="searchKeyword"
            type="text"
            class="search-input"
            placeholder="搜索诗人..."
            @keydown.enter="searchAndFocus"
            @keydown.down.prevent="highlightNext"
            @keydown.up.prevent="highlightPrev"
            @keydown.escape="searchKeyword = ''"
            @focus="searchFocused = true"
          />

          <transition name="dropdown">
            <div v-if="searchFocused && searchKeyword" class="search-results">
              <template v-if="searchMatches.length > 0">
                <div
                  v-for="(match, index) in searchMatches"
                  :key="match.name"
                  class="search-result-item"
                  :class="{ highlighted: index === highlightedIndex }"
                  @click="navigateToAuthor(match.name, match.dynasty || '')"
                  @mouseenter="highlightedIndex = index"
                >
                  <span class="search-result-name">{{ match.name }}</span>
                  <span v-if="match.dynasty" class="search-result-meta">{{ match.dynasty }}</span>
                </div>
              </template>
              <div v-else class="search-empty">未找到匹配的诗人</div>
            </div>
          </transition>
        </div>

        <div class="toolbar-group">
          <button class="toolbar-btn" title="放大" @click="zoomIn">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.2" />
              <path d="M8 5.5V10.5M5.5 8H10.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
            </svg>
          </button>
          <button class="toolbar-btn" title="缩小" @click="zoomOut">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.2" />
              <path d="M5.5 8H10.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
            </svg>
          </button>
          <button class="toolbar-btn" title="重置视角" @click="resetView">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 8a6 6 0 1011.5 2.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
              <path d="M2 4V8H6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          <div class="toolbar-divider"></div>
          <button class="toolbar-btn" :class="{ active: isFullscreen }" title="全屏" @click="toggleFullscreen">
            <svg v-if="!isFullscreen" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M2 6V2H6M10 2H14V6M14 10V14H10M6 14H2V10"
                stroke="currentColor"
                stroke-width="1.2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M6 2V6H2M10 6H14V2M14 10H10V14M2 10H6V14"
                stroke="currentColor"
                stroke-width="1.2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div class="breadcrumb-bar">
      <button class="crumb" :class="{ active: viewLevel === 0 }" @click="goToLevel0">全部朝代</button>
      <template v-if="viewLevel >= 1 && currentDynasty">
        <span class="crumb-sep">›</span>
        <button class="crumb" :class="{ active: viewLevel === 1 }" @click="goToLevel1">{{ currentDynasty }}</button>
      </template>
      <template v-if="viewLevel === 2 && currentAuthor">
        <span class="crumb-sep">›</span>
        <span class="crumb active">{{ currentAuthor }}</span>
      </template>
    </div>

    <div class="graph-body">
      <div class="chart-shell">
        <div class="chart-container" :class="{ transitioning: isTransitioning }">
          <div class="graph-stage-frame">
            <div class="graph-stage-atmosphere"></div>
            <div ref="chartContainerRef" class="graph-stage-host"></div>
            <div ref="labelLayerRef" class="graph-label-layer"></div>

            <div v-if="loading" class="loading-overlay">
              <div class="loading-ripple"><div></div><div></div></div>
              <div class="loading-text">星雾铺展中...</div>
            </div>

            <div v-else-if="!scene" class="graph-empty-overlay">
              <div class="empty-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="1" opacity="0.18" />
                  <circle cx="24" cy="24" r="3" fill="currentColor" opacity="0.36" />
                  <circle cx="24" cy="12" r="2" fill="currentColor" opacity="0.18" />
                  <circle cx="36" cy="24" r="2" fill="currentColor" opacity="0.18" />
                  <circle cx="24" cy="36" r="2" fill="currentColor" opacity="0.18" />
                  <circle cx="12" cy="24" r="2" fill="currentColor" opacity="0.18" />
                </svg>
              </div>
              <div class="empty-text">暂无可渲染的图谱数据</div>
            </div>

          </div>
        </div>
      </div>

      <transition name="panel-slide">
        <div v-if="authorDetail" class="detail-panel" key="detail">
          <div class="panel-header">
            <span class="panel-title">{{ authorDetail.name }}</span>
            <button class="panel-close" @click="authorDetail = null">&times;</button>
          </div>
          <div class="detail-meta">
            <span class="meta-tag dynasty-tag">{{ authorDetail.dynasty }}</span>
            <span class="meta-tag count-tag">{{ authorDetail.poem_count }} 首</span>
          </div>

          <div class="detail-stats">
            <div class="stat-card">
              <div class="stat-card-value">{{ authorDetail.poem_count }}</div>
              <div class="stat-card-label">收录诗作</div>
            </div>
            <div class="stat-card">
              <div class="stat-card-value">{{ authorDetail.categories.length }}</div>
              <div class="stat-card-label">涉及题材</div>
            </div>
          </div>

          <div class="detail-section">
            <div class="section-label">擅长题材</div>
            <div class="category-tags">
              <span v-for="category in authorDetail.categories" :key="category" class="cat-tag">{{ category }}</span>
            </div>
          </div>

          <div class="detail-section">
            <div class="section-label">代表作品</div>
            <div class="poem-list">
              <router-link
                v-for="poem in authorDetail.representative_poems"
                :key="poem.id"
                :to="`/poems/${poem.id}`"
                class="poem-entry"
              >
                <div class="poem-entry-title">{{ poem.title }}</div>
                <div class="poem-entry-preview">{{ poem.content }}</div>
              </router-link>
            </div>
          </div>
        </div>
      </transition>

      <div v-if="!authorDetail" class="detail-panel empty-panel-wrapper">
        <div class="empty-panel">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="1" opacity="0.18" />
              <circle cx="24" cy="24" r="3" fill="currentColor" opacity="0.34" />
              <circle cx="24" cy="12" r="2" fill="currentColor" opacity="0.16" />
              <circle cx="36" cy="24" r="2" fill="currentColor" opacity="0.16" />
              <circle cx="24" cy="36" r="2" fill="currentColor" opacity="0.16" />
              <circle cx="12" cy="24" r="2" fill="currentColor" opacity="0.16" />
            </svg>
          </div>
          <div class="empty-text">点击诗人节点查看详情</div>
        </div>
      </div>
    </div>

    <div v-if="aiRelationVisible" class="ai-relation-overlay" @click.self="closeAIRelation">
      <div class="ai-relation-modal">
        <div class="ai-relation-header">
          <div class="ai-relation-poets">
            <span class="ai-poet-name">{{ aiRelationData?.poet_a }}</span>
            <span class="ai-relation-link-icon">&harr;</span>
            <span class="ai-poet-name">{{ aiRelationData?.poet_b }}</span>
          </div>
          <button class="ai-relation-close" aria-label="关闭关系解读" @click="closeAIRelation">&times;</button>
        </div>

        <div v-if="aiRelationLoading" class="ai-relation-body ai-relation-loading">
          <div class="loading-ripple"><div></div><div></div></div>
          <div class="loading-text">翰林解析中...</div>
          <div class="loading-hint">首次解析需稍候片刻，结果将自动缓存</div>
          <AiPhaseStatus
            title="关系解读生成中"
            :stages="aiRelationStages"
            :current="aiRelationStep"
            hint="正在串联诗人关系与作品语境"
          />
        </div>

        <div v-else-if="aiRelationError" class="ai-relation-body ai-relation-error">
          <div class="ai-relation-error-text">{{ aiRelationError }}</div>
          <button class="ai-relation-retry" @click="retryAIRelation">重试</button>
        </div>

        <div v-else-if="aiRelationData" class="ai-relation-body ai-relation-result">
          <div v-if="aiRelationData.known_relation" class="ai-relation-known">{{ aiRelationData.known_relation }}</div>
          <div class="ai-relation-summary">{{ aiRelationData.summary }}</div>

          <div class="ai-relation-sections">
            <div v-for="(section, index) in aiRelationData.sections" :key="index" class="ai-relation-section">
              <div class="ai-section-title">{{ section.title }}</div>
              <div class="ai-section-content">{{ section.content }}</div>
            </div>
          </div>

          <div class="ai-relation-footer"><span class="ai-powered-tag">AI</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import AiPhaseStatus from '@/components/AiPhaseStatus.vue'
import {
  graphApi,
  type AIRelationResponse,
  type AuthorDetail,
  type DynastyItem,
  type DynastyProfile,
  type GraphData,
  type PoetProfile,
  type PoetRelation,
} from '@/api/graph'
import { usePixiGraph } from './pixi/usePixiGraph'
import { type GraphRenderEdge, type GraphRenderNode } from './pixi/types'

const router = useRouter()

const pageRef = ref<HTMLElement | null>(null)
const searchBoxRef = ref<HTMLElement | null>(null)
const chartContainerRef = ref<HTMLElement | null>(null)
const labelLayerRef = ref<HTMLElement | null>(null)

const loading = ref(false)
const isFullscreen = ref(false)
const searchKeyword = ref('')
const searchFocused = ref(false)
const highlightedIndex = ref(0)
const isTransitioning = ref(false)

const viewLevel = ref<0 | 1 | 2>(0)
const currentDynasty = ref<string | null>(null)
const currentAuthor = ref<string | null>(null)

const dynastyList = ref<DynastyItem[]>([])
const graphData = shallowRef<GraphData | null>(null)
const authorDetail = ref<AuthorDetail | null>(null)

const poetProfiles = shallowRef<Record<string, PoetProfile>>({})
const poetRelationsData = shallowRef<PoetRelation[]>([])
const dynastyProfiles = shallowRef<Record<string, DynastyProfile>>({})

const aiRelationVisible = ref(false)
const aiRelationLoading = ref(false)
const aiRelationError = ref('')
const aiRelationData = ref<AIRelationResponse | null>(null)
const aiRelationStep = ref(0)
const aiRelationStages = ['读取人物关系', '检索关联线索', '生成关系解读']
const aiRelationTimer = ref<number | null>(null)

let pendingRelationPoets: [string, string] | null = null

const selectedNodeId = computed(() => {
  if (viewLevel.value === 1 && currentDynasty.value) return `dynasty_${currentDynasty.value}`
  if (viewLevel.value === 2 && currentAuthor.value) return `author_${currentAuthor.value}`
  return null
})

const {
  scene,
  zoomIn,
  zoomOut,
  resetView,
} = usePixiGraph({
  containerRef: chartContainerRef,
  labelLayerRef,
  viewLevel,
  dynastyList,
  graphData,
  currentDynasty,
  currentAuthor,
  poetProfiles,
  poetRelations: poetRelationsData,
  dynastyProfiles,
  selectedNodeId,
  onNodeClick: handleGraphNodeClick,
  onEdgeClick: handleGraphEdgeClick,
})

watch(searchKeyword, () => {
  highlightedIndex.value = 0
})

const searchMatches = computed(() => {
  if (!searchKeyword.value || !graphData.value) return []
  const keyword = searchKeyword.value.toLowerCase()

  return graphData.value.nodes
    .filter((node) => node.category === 1 && node.name.toLowerCase().includes(keyword))
    .slice(0, 8)
    .map((node) => ({
      name: node.name,
      dynasty: node.dynasty || '',
    }))
})

const highlightNext = () => {
  if (searchMatches.value.length === 0) return
  highlightedIndex.value = (highlightedIndex.value + 1) % searchMatches.value.length
}

const highlightPrev = () => {
  if (searchMatches.value.length === 0) return
  highlightedIndex.value = (highlightedIndex.value - 1 + searchMatches.value.length) % searchMatches.value.length
}

const onClickOutside = (event: MouseEvent) => {
  if (searchBoxRef.value && !searchBoxRef.value.contains(event.target as Node)) {
    searchFocused.value = false
  }
}

const withTransition = (callback: () => void | Promise<void>) => {
  isTransitioning.value = true
  window.setTimeout(async () => {
    await callback()
    requestAnimationFrame(() => {
      isTransitioning.value = false
    })
  }, 260)
}

async function loadDynasties() {
  loading.value = true
  try {
    dynastyList.value = await graphApi.getDynasties()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function loadGraphForDynasty(dynasty?: string) {
  loading.value = true
  try {
    graphData.value = await graphApi.getData(dynasty ? { dynasty } : undefined)
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function preloadAllGraph() {
  loading.value = true
  try {
    graphData.value = await graphApi.getData()
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function loadAuthorDetail(name: string) {
  try {
    authorDetail.value = await graphApi.getAuthorDetail(name)
  } catch (error) {
    console.error(error)
  }
}

async function loadMetadata(retries = 2): Promise<void> {
  try {
    const [profiles, relations, dynasties] = await Promise.all([
      graphApi.getPoetProfiles(),
      graphApi.getPoetRelations(),
      graphApi.getDynastyProfiles(),
    ])
    poetProfiles.value = profiles
    poetRelationsData.value = relations
    dynastyProfiles.value = dynasties
  } catch (error) {
    if (retries > 0) {
      await new Promise((resolve) => window.setTimeout(resolve, 1400))
      await loadMetadata(retries - 1)
    } else {
      console.error(error)
    }
  }
}

function clearAIRelationTimer() {
  if (aiRelationTimer.value !== null) {
    window.clearInterval(aiRelationTimer.value)
    aiRelationTimer.value = null
  }
}

function goToLevel0() {
  withTransition(async () => {
    viewLevel.value = 0
    currentDynasty.value = null
    currentAuthor.value = null
    authorDetail.value = null
    aiRelationVisible.value = false
    await preloadAllGraph()
  })
}

function goToLevel1() {
  if (!currentDynasty.value) return

  withTransition(async () => {
    viewLevel.value = 1
    currentAuthor.value = null
    authorDetail.value = null
    aiRelationVisible.value = false
    await loadGraphForDynasty(currentDynasty.value!)
  })
}

function navigateToAuthor(name: string, dynasty: string) {
  searchKeyword.value = ''
  searchFocused.value = false

  withTransition(async () => {
    if (!dynasty && graphData.value) {
      const match = graphData.value.nodes.find((node) => node.name === name && node.category === 1)
      dynasty = match?.dynasty || ''
    }

    if (dynasty && currentDynasty.value !== dynasty) {
      currentDynasty.value = dynasty
      await loadGraphForDynasty(dynasty)
    }

    viewLevel.value = 2
    currentAuthor.value = name
    await loadAuthorDetail(name)
  })
}

function handleGraphNodeClick(node: GraphRenderNode) {
  if (node.type === 'dynasty') {
    withTransition(async () => {
      currentDynasty.value = node.name
      currentAuthor.value = null
      authorDetail.value = null
      aiRelationVisible.value = false
      viewLevel.value = 1
      await loadGraphForDynasty(node.name)
    })
    return
  }

  if (node.type !== 'poet') return

  if (viewLevel.value === 1) {
    navigateToAuthor(node.name, node.dynasty || currentDynasty.value || '')
    return
  }

  if (viewLevel.value === 2) {
    if (node.name === currentAuthor.value) {
      loadAuthorDetail(node.name)
      return
    }

    navigateToAuthor(node.name, node.dynasty || currentDynasty.value || '')
  }
}

function handleGraphEdgeClick(edge: GraphRenderEdge) {
  if (!edge.isSemantic) return
  const poetA = edge.sourceId.replace(/^author_/, '')
  const poetB = edge.targetId.replace(/^author_/, '')

  if (!poetA || !poetB) return
  triggerAIRelation(poetA, poetB)
}

async function triggerAIRelation(poetA: string, poetB: string) {
  pendingRelationPoets = [poetA, poetB]
  aiRelationVisible.value = true
  aiRelationLoading.value = true
  aiRelationError.value = ''
  aiRelationData.value = null
  aiRelationStep.value = 0

  clearAIRelationTimer()
  aiRelationTimer.value = window.setInterval(() => {
    if (aiRelationStep.value < aiRelationStages.length - 1) {
      aiRelationStep.value += 1
    }
  }, 2500)

  try {
    aiRelationData.value = await graphApi.aiRelation(poetA, poetB)
  } catch (error: unknown) {
    aiRelationError.value = error instanceof Error ? error.message : '分析失败'
  } finally {
    aiRelationLoading.value = false
    clearAIRelationTimer()
  }
}

function closeAIRelation() {
  aiRelationVisible.value = false
  aiRelationData.value = null
  clearAIRelationTimer()
}

function retryAIRelation() {
  if (pendingRelationPoets) {
    triggerAIRelation(pendingRelationPoets[0], pendingRelationPoets[1])
  }
}

function searchAndFocus() {
  const match = searchMatches.value[highlightedIndex.value]
  if (!match) return
  navigateToAuthor(match.name, match.dynasty)
}

function goBack() {
  router.push('/')
}

function toggleFullscreen() {
  if (!isFullscreen.value) {
    pageRef.value?.requestFullscreen?.()
    return
  }
  document.exitFullscreen?.()
}

function onFullscreenChange() {
  isFullscreen.value = Boolean(document.fullscreenElement)
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  document.addEventListener('fullscreenchange', onFullscreenChange)
  loadDynasties()
  preloadAllGraph()
  loadMetadata()
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  clearAIRelationTimer()
})
</script>

<style scoped src="./styles/graph.css"></style>
