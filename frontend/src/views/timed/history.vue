<template>
  <div class="tc-page">
    <div class="tc-container">
      <nav class="tc-nav">
        <router-link to="/games/timed" class="tc-back">&larr; 返回限时挑战</router-link>
        <div class="tc-nav-links">
          <router-link to="/games/timed/rankings" class="tc-nav-link">排行榜</router-link>
        </div>
      </nav>

      <div class="tc-welcome__header">
        <h1 class="tc-welcome__title">挑战记录</h1>
        <p class="tc-welcome__subtitle">过往战绩 · 精进之路</p>
      </div>

      <div v-if="stats.total_games > 0" class="tc-history-preview" style="margin-bottom: 24px;">
        <div class="tc-stat-mini">
          <span class="tc-stat-mini__value">{{ stats.total_games }}</span>
          <span class="tc-stat-mini__label">总场次</span>
        </div>
        <div class="tc-stat-mini">
          <span class="tc-stat-mini__value">{{ stats.best_score }}</span>
          <span class="tc-stat-mini__label">最高分</span>
        </div>
        <div class="tc-stat-mini">
          <span class="tc-stat-mini__value">{{ stats.best_accuracy }}%</span>
          <span class="tc-stat-mini__label">最佳正确率</span>
        </div>
      </div>

      <div v-if="loading" style="text-align: center; padding: 40px; color: var(--color-ink-medium);">
        加载中...
      </div>

      <div v-else-if="items.length === 0" style="text-align: center; padding: 60px; color: var(--color-ink-light);">
        暂无挑战记录
      </div>

      <div v-else class="tc-history-list">
        <div v-for="item in items" :key="item.id" class="tc-history-item">
          <div class="tc-history-item__left">
            <div class="tc-history-item__diff" :class="'tc-history-item__diff--' + item.difficulty">
              {{ diffLabel(item.difficulty) }}
            </div>
            <div class="tc-history-item__info">
              <div class="tc-history-item__score">{{ item.total_score }}分</div>
              <div class="tc-history-item__meta">
                {{ item.correct_count }}/{{ item.total_questions }}正确
                · 连击{{ item.max_combo }}
                · {{ formatDuration(item.duration) }}
              </div>
            </div>
          </div>
          <div class="tc-history-item__right">
            <div class="tc-history-item__accuracy">{{ item.accuracy }}%</div>
            <div class="tc-history-item__date">{{ formatDate(item.started_at) }}</div>
          </div>
        </div>
      </div>

      <div v-if="total > items.length" style="text-align: center; margin-top: 20px;">
        <button class="tc-next-btn" @click="loadMore">加载更多</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { timedChallengeApi, type TimedHistoryItem } from '@/api/timed-challenge'

const items = ref<TimedHistoryItem[]>([])
const loading = ref(true)
const total = ref(0)
const page = ref(1)
const stats = ref({ total_games: 0, best_score: 0, best_accuracy: 0 })

const diffLabel = (d: string) => {
  const map: Record<string, string> = { easy: '初阶', medium: '进阶', hard: '大家' }
  return map[d] || d
}

const formatDuration = (s: number) => {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m > 0 ? `${m}分${sec}秒` : `${sec}秒`
}

const formatDate = (dt: string) => {
  const d = new Date(dt)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const loadData = async () => {
  try {
    loading.value = true
    const res = await timedChallengeApi.getHistory({ page: page.value, page_size: 20 })
    if (page.value === 1) {
      items.value = res.items
    } else {
      items.value.push(...res.items)
    }
    total.value = res.total
    stats.value = {
      total_games: res.total_games,
      best_score: res.best_score,
      best_accuracy: res.best_accuracy,
    }
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  page.value++
  loadData()
}

onMounted(loadData)
</script>

<style>
@import './styles/timed-challenge.css';

.tc-history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.tc-history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 22px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.4));
  border: 1px solid rgba(178, 141, 87, 0.08);
  border-radius: 10px;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.tc-history-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--color-border-light);
  border-radius: 3px 0 0 3px;
  transition: background 0.25s ease;
}

.tc-history-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(178, 141, 87, 0.08);
  border-color: rgba(178, 141, 87, 0.15);
}

.tc-history-item:hover::before {
  background: var(--color-gold);
}

.tc-history-item__left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.tc-history-item__diff {
  font-family: var(--font-poem);
  font-size: 12px;
  padding: 5px 14px;
  border-radius: 6px;
  letter-spacing: 2px;
  white-space: nowrap;
  font-weight: 500;
  border: 1px solid transparent;
}

.tc-history-item__diff--easy {
  background: rgba(69, 104, 93, 0.08);
  color: var(--color-jade);
  border-color: rgba(69, 104, 93, 0.12);
}

.tc-history-item__diff--medium {
  background: rgba(178, 141, 87, 0.08);
  color: var(--color-gold);
  border-color: rgba(178, 141, 87, 0.12);
}

.tc-history-item__diff--hard {
  background: rgba(188, 42, 24, 0.06);
  color: var(--color-vermilion);
  border-color: rgba(188, 42, 24, 0.1);
}

.tc-history-item__score {
  font-family: var(--font-poem);
  font-size: 18px;
  color: var(--color-ink-deep);
  letter-spacing: 0.5px;
}

.tc-history-item__meta {
  font-size: 12px;
  color: var(--color-ink-medium);
  margin-top: 3px;
  letter-spacing: 0.3px;
}

.tc-history-item__right {
  text-align: right;
}

.tc-history-item__accuracy {
  font-family: var(--font-poem);
  font-size: 18px;
  color: var(--color-gold);
  letter-spacing: 1px;
}

.tc-history-item__date {
  font-size: 11px;
  color: var(--color-ink-light);
  margin-top: 4px;
  letter-spacing: 0.5px;
}
</style>
