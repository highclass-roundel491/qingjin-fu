<template>
  <div class="relay-rankings-page">
    <nav class="page-nav">
      <div class="nav-inner">
        <router-link to="/relay" class="back-link">
          <img :src="chainLinkIcon" class="back-icon" alt="" />
          <span>诗词接龙</span>
        </router-link>
        <h1 class="page-title">接龙排行</h1>
        <div style="width:80px"></div>
      </div>
    </nav>

    <div class="rankings-content">
      <div class="period-tabs">
        <button v-for="p in periods" :key="p.value" class="period-tab" :class="{ active: period === p.value }" @click="period = p.value; loadRankings()">
          {{ p.label }}
        </button>
      </div>

      <div class="empty-state" v-if="!loading && items.length === 0">
        <div class="empty-seal">榜</div>
        <p class="empty-title">暂无排行数据</p>
        <p class="empty-hint">完成接龙对局后，排名会根据总分自动生成</p>
        <div class="empty-actions">
          <router-link to="/relay" class="empty-action-btn empty-action-btn--primary">去接龙</router-link>
          <router-link to="/relay/history" class="empty-action-btn">对局记录</router-link>
        </div>
      </div>

      <div class="ranking-list" v-if="items.length > 0">
        <div v-for="(item, idx) in items" :key="item.user_id" class="ranking-row" :class="{ 'top-3': item.rank <= 3 }" :style="{ animationDelay: idx * 0.03 + 's' }">
          <div class="rank-num" :class="`rank-${item.rank}`">{{ item.rank }}</div>
          <div class="rank-user">
            <div class="rank-avatar">{{ (item.username || '?')[0] }}</div>
            <span class="rank-name">{{ item.username }}</span>
          </div>
          <div class="rank-stats">
            <span class="rank-score">{{ item.total_score }}</span>
            <span class="rank-detail">{{ item.total_games }}局 / {{ item.max_combo }}连击</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { relayApi, type RelayRankingItem } from '@/api/relay'
import chainLinkIcon from '@/assets/icons/relay/chain-link.svg'

const items = ref<RelayRankingItem[]>([])
const loading = ref(false)
const period = ref('all')

const periods = [
  { value: 'daily', label: '今日' },
  { value: 'weekly', label: '本周' },
  { value: 'all', label: '总榜' }
]

const loadRankings = async () => {
  loading.value = true
  try {
    const res = await relayApi.getRankings({ period: period.value, page: 1, page_size: 50 })
    items.value = res.items
  } catch {
  } finally {
    loading.value = false
  }
}

onMounted(loadRankings)
</script>

<style scoped>
.relay-rankings-page {
  min-height: 100vh;
  background: var(--color-paper-light);
}

.page-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(249, 246, 240, 0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
}

.nav-inner {
  max-width: 900px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.back-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-ink-medium);
  font-size: 14px;
  transition: color var(--transition-fast);
}
.back-link:hover { color: var(--color-vermilion); }
.back-icon { width: 20px; height: 20px; }

.page-title {
  font-family: var(--font-title);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 4px;
}

.rankings-content {
  max-width: 700px;
  margin: 0 auto;
  padding: 32px 24px;
}

.period-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 28px;
  justify-content: center;
}

.period-tab {
  padding: 8px 24px;
  font-size: 14px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  color: var(--color-ink-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.period-tab:hover { border-color: var(--color-ink-medium); }

.period-tab.active {
  background: var(--color-ink-dark);
  color: var(--color-paper-white);
  border-color: var(--color-ink-dark);
}

.empty-state {
  text-align: center;
  padding: 80px 0;
  color: var(--color-ink-medium);
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.empty-seal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border: 2px solid var(--color-border);
  font-family: var(--font-title);
  font-size: 22px;
  border-radius: 4px;
  margin-bottom: 16px;
  opacity: 0.3;
  transform: rotate(-6deg);
}

.empty-title {
  font-family: var(--font-title);
  font-size: 16px;
  letter-spacing: 0.12em;
  color: var(--color-ink-dark);
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 13px;
  opacity: 0.45;
  max-width: 280px;
  line-height: 1.7;
  margin: 0 auto;
}

.empty-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.empty-action-btn {
  display: inline-block;
  padding: 8px 22px;
  border-radius: 999px;
  font-size: 13px;
  font-family: var(--font-title);
  text-decoration: none;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  color: var(--color-ink-medium);
  transition: all var(--transition-fast);
}

.empty-action-btn:hover {
  border-color: var(--color-ink-medium);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.empty-action-btn--primary {
  background: var(--color-vermilion);
  color: white;
  border-color: var(--color-vermilion);
}

.empty-action-btn--primary:hover {
  box-shadow: 0 4px 12px rgba(188, 42, 24, 0.2);
  border-color: var(--color-vermilion);
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ranking-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 20px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  animation: rowEnter 0.35s ease backwards;
}

@keyframes rowEnter {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.ranking-row:hover { border-color: rgba(18, 17, 16, 0.15); box-shadow: var(--shadow-sm); }

.ranking-row.top-3 {
  border-color: rgba(178, 141, 87, 0.2);
  background: rgba(178, 141, 87, 0.03);
}

.rank-num {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-title);
  font-size: 15px;
  font-weight: 700;
  color: var(--color-ink-medium);
  border-radius: 50%;
  flex-shrink: 0;
}

.rank-1 {
  color: var(--color-gold);
  font-size: 18px;
  background: rgba(178, 141, 87, 0.1);
  box-shadow: 0 0 10px rgba(178, 141, 87, 0.15);
}
.rank-2 {
  color: var(--color-cyan);
  font-size: 17px;
  background: rgba(69, 104, 93, 0.08);
}
.rank-3 {
  color: var(--color-vermilion);
  font-size: 16px;
  background: rgba(188, 42, 24, 0.06);
}

.rank-user {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.rank-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-paper-light);
  border: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-title);
  font-size: 14px;
  color: var(--color-ink-medium);
  flex-shrink: 0;
}

.ranking-row.top-3 .rank-avatar {
  border-color: rgba(178, 141, 87, 0.3);
}

.rank-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink-dark);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.rank-score {
  font-family: var(--font-title);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-gold);
}

.rank-detail {
  font-size: 11px;
  color: var(--color-ink-medium);
  opacity: 0.4;
}

@media (max-width: 640px) {
  .rank-detail { display: none; }
}
</style>
