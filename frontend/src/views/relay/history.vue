<template>
  <div class="relay-history-page">
    <nav class="page-nav">
      <div class="nav-inner">
        <router-link to="/relay" class="back-link">
          <img :src="chainLinkIcon" class="back-icon" alt="" />
          <span>诗词接龙</span>
        </router-link>
        <h1 class="page-title">对局记录</h1>
        <div style="width:80px"></div>
      </div>
    </nav>

    <div class="history-content">
      <div class="empty-state" v-if="!loading && items.length === 0">
        <div class="empty-seal">空</div>
        <p class="empty-title">尚无对局记录</p>
        <p class="empty-hint">完成一局接龙后，每次对局的回合、得分、连击都会记录在这里</p>
        <div class="empty-actions">
          <router-link to="/relay" class="empty-link">开始接龙</router-link>
          <router-link to="/relay/rankings" class="empty-link empty-link--ghost">查看排行</router-link>
        </div>
      </div>

      <div class="history-list" v-if="items.length > 0">
        <div v-for="(item, idx) in items" :key="item.room_id" class="history-card" :style="{ animationDelay: idx * 0.03 + 's' }">
          <div class="card-left">
            <div class="card-mode">{{ item.mode === 'single' ? '单人' : '多人' }}</div>
            <div class="card-difficulty" :class="item.difficulty">{{ difficultyLabel(item.difficulty) }}</div>
          </div>
          <div class="card-center">
            <div class="card-main">
              <span class="card-rounds">{{ item.total_rounds }} 回合</span>
              <span class="card-dot"></span>
              <span class="card-score">{{ item.total_score }} 分</span>
              <span class="card-dot"></span>
              <span class="card-combo">{{ item.max_combo }} 连击</span>
            </div>
            <div class="card-time">{{ formatTime(item.played_at) }}</div>
          </div>
          <div class="card-duration">{{ formatDuration(item.duration) }}</div>
        </div>
      </div>

      <div class="pagination" v-if="total > pageSize">
        <button class="page-btn" :disabled="page <= 1" @click="page--; loadHistory()">上一页</button>
        <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
        <button class="page-btn" :disabled="page * pageSize >= total" @click="page++; loadHistory()">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { relayApi, type RelayHistoryItem } from '@/api/relay'
import chainLinkIcon from '@/assets/icons/relay/chain-link.svg'

const items = ref<RelayHistoryItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

const difficultyLabel = (d: string) => {
  const map: Record<string, string> = { easy: '简单', normal: '普通', hard: '困难' }
  return map[d] || d
}

const formatTime = (t: string) => {
  const d = new Date(t)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const formatDuration = (s: number) => {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m > 0 ? `${m}分${sec}秒` : `${sec}秒`
}

const loadHistory = async () => {
  loading.value = true
  try {
    const res = await relayApi.getHistory({ page: page.value, page_size: pageSize })
    items.value = res.items
    total.value = res.total
  } catch {
  } finally {
    loading.value = false
  }
}

onMounted(loadHistory)
</script>

<style scoped>
.relay-history-page {
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

.history-content {
  max-width: 700px;
  margin: 0 auto;
  padding: 32px 24px;
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
  color: var(--color-ink-medium);
  font-family: var(--font-title);
  font-size: 22px;
  border-radius: 4px;
  margin-bottom: 16px;
  opacity: 0.3;
  transform: rotate(-6deg);
}

.empty-link {
  display: inline-block;
  margin-top: 16px;
  padding: 8px 24px;
  background: var(--color-vermilion);
  color: white;
  border-radius: var(--radius-md);
  font-size: 14px;
  transition: all var(--transition-fast);
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
  color: var(--color-ink-medium);
  opacity: 0.45;
  max-width: 300px;
  line-height: 1.7;
  margin: 0 auto;
}

.empty-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.empty-link:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(188, 42, 24, 0.2); }

.empty-link--ghost {
  background: var(--color-paper-white);
  color: var(--color-ink-medium);
  border: 1px solid var(--color-border);
}

.empty-link--ghost:hover {
  border-color: var(--color-ink-medium);
  box-shadow: var(--shadow-sm);
  opacity: 1;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  animation: cardEnter 0.35s ease backwards;
}

@keyframes cardEnter {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.history-card:hover {
  border-color: rgba(18, 17, 16, 0.15);
  box-shadow: var(--shadow-sm);
  transform: translateX(2px);
}

.card-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 48px;
}

.card-mode {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ink-medium);
}

.card-difficulty {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--color-paper-light);
}

.card-difficulty.easy { color: var(--color-cyan); }
.card-difficulty.normal { color: var(--color-gold); }
.card-difficulty.hard { color: var(--color-vermilion); }

.card-center { flex: 1; }

.card-main {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-ink-dark);
}

.card-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--color-border);
}

.card-score { font-weight: 600; color: var(--color-gold); }
.card-combo { color: var(--color-vermilion); font-weight: 500; }

.card-time {
  font-size: 11px;
  color: var(--color-ink-medium);
  opacity: 0.4;
  margin-top: 4px;
}

.card-duration {
  font-size: 13px;
  color: var(--color-ink-medium);
  opacity: 0.5;
  white-space: nowrap;
  font-family: var(--font-title);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
}

.page-btn {
  padding: 8px 18px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  font-size: 13px;
  color: var(--color-ink-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.page-btn:hover:not(:disabled) { border-color: var(--color-ink-medium); }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.page-info {
  font-size: 13px;
  color: var(--color-ink-medium);
  opacity: 0.6;
}

@media (max-width: 640px) {
  .card-left { min-width: 40px; }
  .card-duration { display: none; }
}
</style>
