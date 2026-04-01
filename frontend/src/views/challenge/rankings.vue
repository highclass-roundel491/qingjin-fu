<template>
  <div class="cr-page">
    <div class="cr-container">
      <nav class="cr-nav">
        <router-link to="/challenge" class="cr-back">&larr; 返回妙笔</router-link>
      </nav>

      <div class="cr-header">
        <h1 class="cr-header__title">妙笔排行</h1>
        <p class="cr-header__subtitle">落笔千言 · 文采争辉</p>
      </div>

      <div class="cr-period-bar">
        <button
          v-for="p in periodOptions"
          :key="p.value"
          class="cr-period-btn"
          :class="{ 'cr-period-btn--active': period === p.value }"
          @click="switchPeriod(p.value)"
        >{{ p.label }}</button>
      </div>

      <div v-if="loading" class="cr-state">加载中...</div>

      <div v-else-if="items.length === 0" class="cr-state cr-state--empty">暂无排行数据</div>

      <div v-else class="cr-ranking-list">
        <div
          v-for="item in items"
          :key="item.user_id"
          class="cr-ranking-item"
          :class="{ 'cr-ranking-item--top': item.rank <= 3 }"
        >
          <div class="cr-ranking-item__rank" :class="'cr-ranking-item__rank--' + item.rank">
            {{ item.rank }}
          </div>
          <UserAvatar :username="item.nickname || item.username" :avatar="item.avatar_url" size="small" />
          <div class="cr-ranking-item__info">
            <div class="cr-ranking-item__name">{{ item.nickname || item.username }}</div>
            <div class="cr-ranking-item__meta">
              {{ item.total_submissions }}次落笔 · {{ item.total_exp }}经验
            </div>
          </div>
          <div class="cr-ranking-item__score">
            <div class="cr-ranking-item__total">{{ item.total_points }}</div>
            <div class="cr-ranking-item__label">积分</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { challengeApi, type ChallengeRankingItem } from '@/api/challenge'
import UserAvatar from '@/components/UserAvatar.vue'

const periodOptions = [
  { value: 'today', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'all', label: '总榜' },
]

const period = ref('all')
const items = ref<ChallengeRankingItem[]>([])
const loading = ref(true)

const loadData = async () => {
  try {
    loading.value = true
    const res = await challengeApi.getRankings({ period: period.value, page: 1, page_size: 50 })
    items.value = res.items
  } catch {
    items.value = []
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

<style scoped>
.cr-page {
  min-height: 100vh;
  background: var(--color-bg-primary);
  padding: 32px 0 64px;
}

.cr-container {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 24px;
}

.cr-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.cr-back {
  font-size: 13px;
  color: var(--color-ink-medium);
  text-decoration: none;
  letter-spacing: 0.5px;
  transition: color 0.2s;
}

.cr-back:hover {
  color: var(--color-gold);
}

.cr-header {
  text-align: center;
  margin-bottom: 28px;
}

.cr-header__title {
  font-family: var(--font-heading);
  font-size: 28px;
  color: var(--color-ink-deep);
  letter-spacing: 6px;
  margin: 0 0 8px;
}

.cr-header__subtitle {
  font-family: var(--font-poem);
  font-size: 14px;
  color: var(--color-ink-medium);
  letter-spacing: 4px;
  margin: 0;
}

.cr-header__subtitle::after {
  content: '';
  display: block;
  width: 40px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-gold), transparent);
  margin: 12px auto 0;
  border-radius: 1px;
}

.cr-period-bar {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
  padding: 12px 18px;
  background: linear-gradient(160deg, rgba(255,255,255,0.7), rgba(255,255,255,0.4));
  border: 1px solid rgba(178,141,87,0.08);
  border-radius: 12px;
}

.cr-period-btn {
  padding: 6px 22px;
  font-family: var(--font-poem);
  font-size: 14px;
  color: var(--color-ink-medium);
  background: transparent;
  border: 1px solid var(--color-border-light);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.25s ease;
  letter-spacing: 2px;
}

.cr-period-btn:hover {
  color: var(--color-gold);
  border-color: rgba(178,141,87,0.25);
}

.cr-period-btn--active {
  background: linear-gradient(135deg, var(--color-gold), #d4a54a);
  color: #fff;
  border-color: var(--color-gold);
  box-shadow: 0 2px 8px rgba(178,141,87,0.2);
}

.cr-state {
  text-align: center;
  padding: 40px;
  color: var(--color-ink-medium);
  font-family: var(--font-poem);
  font-size: 14px;
  letter-spacing: 1px;
}

.cr-state--empty {
  padding: 60px;
  color: var(--color-ink-light);
}

.cr-ranking-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.cr-ranking-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: 16px 22px;
  background: linear-gradient(160deg, rgba(255,255,255,0.7), rgba(255,255,255,0.4));
  border: 1px solid rgba(178,141,87,0.08);
  border-radius: 10px;
  transition: all 0.25s ease;
  position: relative;
}

.cr-ranking-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(178,141,87,0.08);
  border-color: rgba(178,141,87,0.15);
}

.cr-ranking-item--top {
  padding: 18px 24px;
  background: linear-gradient(160deg, rgba(178,141,87,0.06), rgba(255,255,255,0.5));
  border-color: rgba(178,141,87,0.12);
}

.cr-ranking-item__rank {
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

.cr-ranking-item:hover .cr-ranking-item__rank {
  transform: scale(1.08);
}

.cr-ranking-item__rank--1 {
  background: linear-gradient(135deg, var(--color-gold), #d4a54a);
  color: #fff;
  border-color: var(--color-gold);
  box-shadow: 0 2px 8px rgba(178,141,87,0.25);
  font-size: 17px;
}

.cr-ranking-item__rank--2 {
  background: linear-gradient(135deg, #b0b0b0, #8a8a8a);
  color: #fff;
  border-color: #a0a0a0;
  box-shadow: 0 2px 6px rgba(140,140,140,0.2);
}

.cr-ranking-item__rank--3 {
  background: linear-gradient(135deg, #d08850, #a06030);
  color: #fff;
  border-color: #c07840;
  box-shadow: 0 2px 6px rgba(192,120,64,0.2);
}

.cr-ranking-item__info {
  flex: 1;
}

.cr-ranking-item__name {
  font-family: var(--font-poem);
  font-size: 16px;
  color: var(--color-ink-deep);
  letter-spacing: 1px;
}

.cr-ranking-item--top .cr-ranking-item__name {
  font-size: 17px;
}

.cr-ranking-item__meta {
  font-size: 12px;
  color: var(--color-ink-medium);
  margin-top: 3px;
  letter-spacing: 0.3px;
}

.cr-ranking-item__score {
  text-align: right;
}

.cr-ranking-item__total {
  font-family: var(--font-poem);
  font-size: 20px;
  color: var(--color-vermilion);
  letter-spacing: 0.5px;
}

.cr-ranking-item--top .cr-ranking-item__total {
  font-size: 22px;
  text-shadow: 0 1px 4px rgba(188,42,24,0.1);
}

.cr-ranking-item__label {
  font-size: 11px;
  color: var(--color-ink-light);
  margin-top: 3px;
  letter-spacing: 0.3px;
}
</style>
