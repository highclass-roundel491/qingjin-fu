<template>
  <div class="tc-page">
    <div class="tc-container">
      <nav class="tc-nav">
        <router-link to="/games/timed" class="tc-back">&larr; 返回限时挑战</router-link>
        <div class="tc-nav-links">
          <router-link to="/games/timed/history" class="tc-nav-link">历史</router-link>
        </div>
      </nav>

      <div class="tc-welcome__header">
        <h1 class="tc-welcome__title">挑战排行</h1>
        <p class="tc-welcome__subtitle">群英争锋 · 一决高下</p>
      </div>

      <div class="tc-setup" style="margin-bottom: 24px; padding: 12px 18px;">
        <div class="tc-setup__options" style="justify-content: center;">
          <button
            v-for="p in periodOptions"
            :key="p.value"
            class="tc-opt-btn"
            :class="{ 'tc-opt-btn--active': period === p.value }"
            @click="switchPeriod(p.value)"
          >{{ p.label }}</button>
        </div>
      </div>

      <div v-if="loading" style="text-align: center; padding: 40px; color: var(--color-ink-medium);">
        加载中...
      </div>

      <div v-else-if="items.length === 0" style="text-align: center; padding: 60px; color: var(--color-ink-light);">
        暂无排行数据
      </div>

      <div v-else class="tc-ranking-list">
        <div
          v-for="item in items"
          :key="item.user_id"
          class="tc-ranking-item"
          :class="{ 'tc-ranking-item--top': item.rank <= 3 }"
        >
          <div class="tc-ranking-item__rank" :class="'tc-ranking-item__rank--' + item.rank">
            {{ item.rank }}
          </div>
          <UserAvatar :username="item.nickname || item.username" :avatar="item.avatar_url" size="small" />
          <div class="tc-ranking-item__info">
            <div class="tc-ranking-item__name">{{ item.nickname || item.username }}</div>
            <div class="tc-ranking-item__meta">
              {{ item.total_games }}场 · 最佳{{ item.best_accuracy }}%
            </div>
          </div>
          <div class="tc-ranking-item__score">
            <div class="tc-ranking-item__total">{{ item.total_score }}</div>
            <div class="tc-ranking-item__best">最高{{ item.best_score }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { timedChallengeApi, type TimedRankingItem } from '@/api/timed-challenge'
import UserAvatar from '@/components/UserAvatar.vue'

const periodOptions = [
  { value: 'today', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'all', label: '总榜' },
]

const period = ref('all')
const items = ref<TimedRankingItem[]>([])
const loading = ref(true)

const loadData = async () => {
  try {
    loading.value = true
    const res = await timedChallengeApi.getRankings({ period: period.value, page: 1, page_size: 50 })
    items.value = res.items
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

const switchPeriod = (p: string) => {
  period.value = p
  loadData()
}

onMounted(loadData)
</script>

<style>
@import './styles/timed-challenge.css';

.tc-ranking-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.tc-ranking-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: 16px 22px;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.4));
  border: 1px solid rgba(178, 141, 87, 0.08);
  border-radius: 10px;
  transition: all 0.25s ease;
  position: relative;
}

.tc-ranking-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(178, 141, 87, 0.08);
  border-color: rgba(178, 141, 87, 0.15);
}

.tc-ranking-item--top {
  padding: 18px 24px;
  background: linear-gradient(160deg, rgba(178, 141, 87, 0.06), rgba(255, 255, 255, 0.5));
  border-color: rgba(178, 141, 87, 0.12);
}

.tc-ranking-item--top::after {
  content: '';
  position: absolute;
  right: 20px;
  bottom: 8px;
  width: 40px;
  height: 40px;
  opacity: 0.04;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23B28D57"><path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3c0 .6-.4 1-1 1H6c-.6 0-1-.4-1-1v-1h14v1z"/></svg>') no-repeat center;
  background-size: contain;
}

.tc-ranking-item__rank {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-poem);
  font-size: 16px;
  color: var(--color-ink-medium);
  border: 1.5px solid var(--color-border-light);
  border-radius: 50%;
  transition: transform 0.25s ease;
}

.tc-ranking-item:hover .tc-ranking-item__rank {
  transform: scale(1.08);
}

.tc-ranking-item__rank--1 {
  background: linear-gradient(135deg, var(--color-gold), #d4a54a);
  color: #fff;
  border-color: var(--color-gold);
  box-shadow: 0 2px 8px rgba(178, 141, 87, 0.25);
  font-size: 17px;
}

.tc-ranking-item__rank--2 {
  background: linear-gradient(135deg, #b0b0b0, #8a8a8a);
  color: #fff;
  border-color: #a0a0a0;
  box-shadow: 0 2px 6px rgba(140, 140, 140, 0.2);
}

.tc-ranking-item__rank--3 {
  background: linear-gradient(135deg, #d08850, #a06030);
  color: #fff;
  border-color: #c07840;
  box-shadow: 0 2px 6px rgba(192, 120, 64, 0.2);
}

.tc-ranking-item__info {
  flex: 1;
}

.tc-ranking-item__name {
  font-family: var(--font-poem);
  font-size: 16px;
  color: var(--color-ink-deep);
  letter-spacing: 1px;
}

.tc-ranking-item--top .tc-ranking-item__name {
  font-size: 17px;
}

.tc-ranking-item__meta {
  font-size: 12px;
  color: var(--color-ink-medium);
  margin-top: 3px;
  letter-spacing: 0.3px;
}

.tc-ranking-item__score {
  text-align: right;
}

.tc-ranking-item__total {
  font-family: var(--font-poem);
  font-size: 20px;
  color: var(--color-vermilion);
  letter-spacing: 0.5px;
}

.tc-ranking-item--top .tc-ranking-item__total {
  font-size: 22px;
  text-shadow: 0 1px 4px rgba(188, 42, 24, 0.1);
}

.tc-ranking-item__best {
  font-size: 11px;
  color: var(--color-ink-light);
  margin-top: 3px;
  letter-spacing: 0.3px;
}
</style>
