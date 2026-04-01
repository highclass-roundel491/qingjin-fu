<template>
  <Teleport to="body">
    <div v-if="visible" class="rank-overlay" @click.self="close">
      <div class="rank-dialog">
        <button class="rank-dialog__close" @click="close">&times;</button>
        <div class="rank-dialog__scroll">
          <div class="rank-dialog__header">
            <h2 class="rank-dialog__title">科举功名录</h2>
            <p class="rank-dialog__subtitle">诗学精进，逐阶登科</p>
          </div>

          <div class="rank-dialog__tabs">
            <button
              type="button"
              class="rank-dialog__tab"
              :class="{ 'rank-dialog__tab--active': activeTab === 'ranks' }"
              @click="switchTab('ranks')"
            >
              功名阶位
            </button>
            <button
              type="button"
              class="rank-dialog__tab"
              :class="{ 'rank-dialog__tab--active': activeTab === 'history' }"
              @click="switchTab('history')"
            >
              经验明细
            </button>
          </div>

          <template v-if="activeTab === 'ranks'">
            <div class="rank-dialog__list">
              <div
                v-for="rank in RANK_CONFIG"
                :key="rank.level"
                class="rank-item"
                :class="{
                  'rank-item--current': rank.level === displayLevel,
                  'rank-item--achieved': rank.level < displayLevel,
                  'rank-item--locked': rank.level > displayLevel
                }"
              >
                <img :src="rank.icon" class="rank-item__icon" alt="" />
                <div class="rank-item__info">
                  <div class="rank-item__head">
                    <span class="rank-item__name" :style="{ color: rank.level <= displayLevel ? rank.color : '' }">
                      {{ rank.name }}
                    </span>
                    <span class="rank-item__level">Lv.{{ rank.level }}</span>
                  </div>
                  <div class="rank-item__desc">{{ rank.desc }}</div>
                  <div class="rank-item__exp">
                    <template v-if="rank.level === 1">
                      起始等级
                    </template>
                    <template v-else>
                      {{ rank.expRequired }} 经验
                    </template>
                  </div>
                </div>
                <div class="rank-item__status">
                  <span v-if="rank.level < displayLevel" class="rank-item__badge rank-item__badge--done">已达成</span>
                  <span v-else-if="rank.level === displayLevel" class="rank-item__badge rank-item__badge--current">当前</span>
                  <span v-else class="rank-item__badge rank-item__badge--locked">{{ rank.expRequired - resolvedExp > 0 ? `差${rank.expRequired - resolvedExp}` : '' }}</span>
                </div>
              </div>
            </div>

            <div class="rank-dialog__footer" v-if="nextRank">
              <div class="rank-dialog__progress-label">
                当前经验 <strong>{{ resolvedExp }}</strong>，本阶进度 {{ progress.current }} / {{ progress.total }}，距「{{ nextRank.name }}」还需 {{ expToNextRank }}
              </div>
              <div class="rank-dialog__detail-list">
                <span class="rank-dialog__detail-item">当前阶位 {{ currentRank.name }}</span>
                <span class="rank-dialog__detail-item">本阶门槛 {{ currentRank.expRequired }}</span>
                <span class="rank-dialog__detail-item">下阶门槛 {{ nextRank.expRequired }}</span>
                <span class="rank-dialog__detail-item">升级还需 {{ expToNextRank }}</span>
              </div>
              <div class="rank-dialog__progress-bar">
                <div class="rank-dialog__progress-fill" :style="{ width: actualPercent + '%' }"></div>
              </div>
            </div>

            <div class="rank-dialog__footer" v-else>
              <div class="rank-dialog__progress-label">当前经验 <strong>{{ resolvedExp }}</strong>，已至最高境界</div>
              <div class="rank-dialog__detail-list">
                <span class="rank-dialog__detail-item">当前阶位 {{ currentRank.name }}</span>
                <span class="rank-dialog__detail-item">当前门槛 {{ currentRank.expRequired }}</span>
                <span class="rank-dialog__detail-item">本阶累计 {{ progress.current }}</span>
              </div>
            </div>

          </template>

          <section v-else class="exp-history">
            <div class="exp-history__meta">
              <span>当前经验 {{ resolvedExp }}</span>
              <span v-if="historyTotal">最近记录 {{ Math.min(historyItems.length, historyTotal) }} / {{ historyTotal }}</span>
            </div>

            <div v-if="historyLoading" class="exp-history__state">正在整理经验明细...</div>
            <div v-else-if="historyError" class="exp-history__state">{{ historyError }}</div>

            <div v-else-if="historyItems.length" class="exp-history__list">
              <article v-for="item in historyItems" :key="item.id" class="exp-history__item">
                <div class="exp-history__item-main">
                  <div class="exp-history__item-head">
                    <span class="exp-history__item-source">{{ item.source_label }}</span>
                    <time class="exp-history__item-time">{{ formatDateTime(item.occurred_at) }}</time>
                  </div>
                  <h3 class="exp-history__item-title">{{ item.title }}</h3>
                  <p class="exp-history__item-detail">{{ item.detail }}</p>
                </div>
                <strong class="exp-history__item-exp">+{{ item.exp }}</strong>
              </article>
            </div>

            <div v-else class="exp-history__state">还没有可展示的经验记录</div>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { type UserExpHistoryItem, userApi } from '@/api/user'
import { RANK_CONFIG, getExpProgress, getNextRank, getRankByExp, getRankByLevel } from '@/utils/levels'

const props = defineProps<{
  visible: boolean
  currentLevel: number
  currentExp: number
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const resolvedExp = computed(() => Math.max(0, props.currentExp))
const currentRank = computed(() => Number.isFinite(props.currentExp) ? getRankByExp(resolvedExp.value) : getRankByLevel(props.currentLevel))
const displayLevel = computed(() => currentRank.value.level)
const nextRank = computed(() => getNextRank(displayLevel.value))
const progress = computed(() => getExpProgress(resolvedExp.value))
const actualPercent = computed(() => nextRank.value ? progress.value.percent : 100)
const expToNextRank = computed(() => nextRank.value ? Math.max(0, nextRank.value.expRequired - resolvedExp.value) : 0)
const activeTab = ref<'ranks' | 'history'>('ranks')
const historyLoading = ref(false)
const historyLoaded = ref(false)
const historyError = ref('')
const historyItems = ref<UserExpHistoryItem[]>([])
const historyTotal = ref(0)

const switchTab = (tab: 'ranks' | 'history') => {
  activeTab.value = tab
}

const loadHistory = async () => {
  if (historyLoading.value || historyLoaded.value) return
  historyLoading.value = true
  historyError.value = ''
  try {
    const data = await userApi.getExpHistory({ page: 1, page_size: 30 })
    historyItems.value = data.items
    historyTotal.value = data.total
    historyLoaded.value = true
  } catch {
    historyItems.value = []
    historyTotal.value = 0
    historyError.value = '经验明细暂时无法加载'
  } finally {
    historyLoading.value = false
  }
}

const formatDateTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '刚刚'
  return `${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

watch(() => props.visible, visible => {
  if (!visible) {
    activeTab.value = 'ranks'
    historyLoaded.value = false
    historyError.value = ''
    return
  }
  if (activeTab.value === 'history') {
    void loadHistory()
  }
})

watch(activeTab, tab => {
  if (tab === 'history' && props.visible) {
    void loadHistory()
  }
})

const close = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.rank-overlay {
  position: fixed;
  inset: 0;
  background: rgba(18, 17, 16, 0.5);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px;
  z-index: 2000;
  animation: rank-fade-in 0.25s ease;
}

@keyframes rank-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.rank-dialog {
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  width: min(100%, 560px);
  max-height: 85vh;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(73, 61, 52, 0.16);
  animation: rank-scale-in 0.3s ease;
}

@keyframes rank-scale-in {
  from { opacity: 0; transform: scale(0.96) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.rank-dialog__scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: rgba(122, 107, 91, 0.62) transparent;
  padding: var(--spacing-lg);
  padding-right: calc(var(--spacing-lg) - 2px);
}

.rank-dialog__scroll::-webkit-scrollbar {
  width: 10px;
}

.rank-dialog__scroll::-webkit-scrollbar-track {
  background: rgba(18, 17, 16, 0.04);
  border-radius: 999px;
}

.rank-dialog__scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(120, 140, 93, 0.8), rgba(139, 115, 85, 0.88));
  border-radius: 999px;
  border: 2px solid rgba(248, 245, 238, 0.96);
}

.rank-dialog__scroll::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(120, 140, 93, 0.92), rgba(139, 115, 85, 1));
}

.rank-dialog__close {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(250, 249, 245, 0.9);
  border: 1px solid rgba(18, 17, 16, 0.08);
  border-radius: 999px;
  font-size: 22px;
  color: var(--color-ink-medium);
  opacity: 0.7;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  z-index: 2;
  box-shadow: 0 8px 18px rgba(73, 61, 52, 0.08);
  transition: opacity var(--transition-fast), transform var(--transition-fast), box-shadow var(--transition-fast);
}

.rank-dialog__close:hover {
  opacity: 1;
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(73, 61, 52, 0.12);
}

.rank-dialog__header {
  text-align: center;
  padding-top: 6px;
  margin-bottom: 12px;
}

.rank-dialog__title {
  font-family: var(--font-poem);
  font-size: 24px;
  color: var(--color-ink-dark);
  letter-spacing: 4px;
  font-weight: 400;
  margin-bottom: 4px;
}

.rank-dialog__subtitle {
  font-size: 13px;
  color: var(--color-ink-medium);
  opacity: 0.6;
  letter-spacing: 2px;
}

.rank-dialog__tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.rank-dialog__tab {
  min-height: 40px;
  border: 1px solid rgba(18, 17, 16, 0.08);
  border-radius: 14px;
  background: rgba(18, 17, 16, 0.03);
  color: var(--color-ink-medium);
  font-family: var(--font-title);
  font-size: 13px;
  letter-spacing: 1.5px;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);
}

.rank-dialog__tab:hover {
  transform: translateY(-1px);
}

.rank-dialog__tab--active {
  background: rgba(188, 42, 24, 0.08);
  border-color: rgba(188, 42, 24, 0.18);
  color: var(--color-vermilion);
}

.rank-dialog__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: var(--spacing-md);
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  transition: background var(--transition-fast);
}

.rank-item--current {
  background: rgba(188, 42, 24, 0.04);
  border-color: rgba(188, 42, 24, 0.12);
}

.rank-item--achieved {
  opacity: 0.85;
}

.rank-item--locked {
  opacity: 0.45;
}

.rank-item__icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.rank-item__info {
  flex: 1;
  min-width: 0;
}

.rank-item__head {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.rank-item__name {
  font-family: var(--font-title);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 2px;
}

.rank-item__level {
  font-size: 11px;
  color: var(--color-ink-medium);
  opacity: 0.6;
}

.rank-item__desc {
  font-size: 12px;
  color: var(--color-ink-medium);
  opacity: 0.55;
  margin-top: 2px;
}

.rank-item__exp {
  font-size: 11px;
  color: var(--color-ink-medium);
  opacity: 0.4;
  margin-top: 2px;
}

.rank-item__status {
  flex-shrink: 0;
}

.rank-item__badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.5px;
}

.rank-item__badge--done {
  background: rgba(69, 104, 93, 0.1);
  color: var(--color-cyan);
}

.rank-item__badge--current {
  background: rgba(188, 42, 24, 0.1);
  color: var(--color-vermilion);
  font-weight: 600;
}

.rank-item__badge--locked {
  background: rgba(18, 17, 16, 0.04);
  color: var(--color-ink-medium);
  opacity: 0.6;
}

.rank-dialog__footer {
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.rank-dialog__progress-label {
  font-size: 13px;
  color: var(--color-ink-medium);
  text-align: center;
  margin-bottom: 8px;
}

.rank-dialog__progress-label strong {
  color: var(--color-vermilion);
}

.rank-dialog__detail-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-bottom: 10px;
}

.rank-dialog__detail-item {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(18, 17, 16, 0.04);
  border: 1px solid rgba(18, 17, 16, 0.06);
  color: var(--color-ink-medium);
  font-size: 11px;
  letter-spacing: 0.5px;
}

.rank-dialog__progress-bar {
  height: 6px;
  background: rgba(18, 17, 16, 0.06);
  border-radius: 3px;
  overflow: hidden;
}

.rank-dialog__progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-cyan), var(--color-gold));
  border-radius: 3px;
  transition: width 0.4s ease;
}

.exp-history {
  display: grid;
  gap: 12px;
}

.exp-history__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--color-ink-medium);
  opacity: 0.7;
  font-size: 12px;
  letter-spacing: 1px;
}

.exp-history__state {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px;
  border-radius: var(--radius-md);
  background: rgba(18, 17, 16, 0.03);
  border: 1px solid rgba(18, 17, 16, 0.05);
  color: var(--color-ink-medium);
  opacity: 0.7;
  text-align: center;
}

.exp-history__list {
  display: grid;
  gap: 10px;
}

.exp-history__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: rgba(18, 17, 16, 0.03);
  border: 1px solid rgba(18, 17, 16, 0.06);
}

.exp-history__item-main {
  min-width: 0;
  flex: 1;
}

.exp-history__item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.exp-history__item-source {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(188, 42, 24, 0.08);
  color: var(--color-vermilion);
  font-size: 11px;
  letter-spacing: 1px;
}

.exp-history__item-time {
  flex-shrink: 0;
  color: var(--color-ink-medium);
  opacity: 0.55;
  font-size: 11px;
}

.exp-history__item-title {
  margin: 0 0 4px;
  color: var(--color-ink-dark);
  font-family: var(--font-title);
  font-size: 15px;
  letter-spacing: 1px;
}

.exp-history__item-detail {
  margin: 0;
  color: var(--color-ink-medium);
  opacity: 0.74;
  line-height: 1.6;
  font-size: 12px;
}

.exp-history__item-exp {
  flex-shrink: 0;
  color: var(--color-vermilion);
  font-family: var(--font-title);
  font-size: 18px;
  letter-spacing: 1px;
}
</style>
