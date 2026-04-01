<template>
  <div class="drafts-page">
    <div class="ink-bg">
      <div class="ink-wash ink-wash--1"></div>
      <div class="ink-wash ink-wash--2"></div>
    </div>

    <nav class="page-nav">
      <router-link to="/works" class="nav-back">← 作品墙</router-link>
      <span class="nav-title">草稿箱</span>
      <router-link to="/works/create" class="btn-create">+ 新建创作</router-link>
    </nav>

    <main class="page-body">
      <div v-if="!loading || drafts.length > 0" class="drafts-summary">
        <span class="drafts-summary__count">草稿箱共有 {{ total }} 篇待完善的作品</span>
        <span class="drafts-summary__hint">发布后将出现在作品墙</span>
      </div>

      <div v-if="loading && drafts.length === 0" class="loading-state">
        <div class="loading-dot"></div>
        <span>加载中…</span>
      </div>

      <div v-else-if="drafts.length === 0" class="empty-state">
        <div class="empty-glyph">稿</div>
        <h3 class="empty-title">还没有草稿，先去落下第一笔</h3>
        <p class="empty-desc">创作时点“存草稿”就能把未完成的作品保存在这里。也可以用起手句快速开始，以后再慢慢润色。</p>
        <div class="empty-state__actions">
          <router-link to="/works/create" class="empty-action">去创作第一篇</router-link>
          <router-link to="/works" class="empty-secondary">先逛作品墙</router-link>
        </div>
      </div>

      <div v-else class="drafts-list">
        <article
          v-for="draft in drafts"
          :key="draft.id"
          class="draft-card"
        >
          <div class="draft-card__left">
            <div class="draft-card__status">
              <span class="draft-dot"></span>
              草稿
            </div>
            <h3 class="draft-card__title">{{ draft.title }}</h3>
            <p class="draft-card__preview">{{ truncateContent(draft.content) }}</p>
            <div class="draft-card__meta">
              <span class="draft-card__genre">{{ draft.genre }}</span>
              <span class="draft-card__time">{{ formatTime(draft.created_at) }}</span>
            </div>
          </div>
          <div class="draft-card__actions">
            <button class="draft-action draft-action--edit" @click="goEdit(draft.id)">继续编辑</button>
            <button class="draft-action draft-action--publish" @click="publishDraft(draft)">直接发布</button>
            <button class="draft-action draft-action--delete" @click="deleteDraft(draft)">删除</button>
          </div>
        </article>
      </div>

      <div v-if="hasMore" class="load-more">
        <button class="btn-load-more" @click="loadMore" :disabled="loading">
          {{ loading ? '加载中…' : '加载更多' }}
        </button>
      </div>
    </main>

    <AppToast v-model="toast.show" :message="toast.message" :type="toast.type" />
    <AppConfirm
      v-model="confirmVisible"
      title="删除草稿"
      message="确定删除此草稿？删除后不可恢复。"
      confirm-text="删除"
      variant="danger"
      @confirm="doDeleteDraft"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { worksApi, type WorkItem } from '@/api/works'
import { useUserStore } from '@/store/modules/user'
import AppToast from '@/components/AppToast.vue'
import AppConfirm from '@/components/AppConfirm.vue'

const router = useRouter()
const userStore = useUserStore()

const drafts = ref<WorkItem[]>([])
const page = ref(1)
const total = ref(0)
const loading = ref(false)
const toast = ref({ show: false, message: '', type: 'success' as 'success' | 'error' | 'warning' | 'info' })
const confirmVisible = ref(false)
const pendingDeleteDraft = ref<WorkItem | null>(null)

const hasMore = computed(() => drafts.value.length < total.value)

function showToast(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'success') {
  toast.value = { show: true, message, type }
}

async function fetchDrafts(reset = false) {
  if (reset) {
    page.value = 1
    drafts.value = []
  }
  loading.value = true
  try {
    const res = await worksApi.getMyWorks({
      status: 'draft',
      page: page.value,
      page_size: 20
    })
    if (reset) {
      drafts.value = res.items
    } else {
      drafts.value.push(...res.items)
    }
    total.value = res.total
  } catch {}
  loading.value = false
}

function loadMore() {
  page.value++
  fetchDrafts()
}

function goEdit(id: number) {
  router.push(`/works/create?id=${id}`)
}

async function publishDraft(draft: WorkItem) {
  try {
    await worksApi.publishWork(draft.id)
    await userStore.fetchUserInfo()
    drafts.value = drafts.value.filter(d => d.id !== draft.id)
    total.value = Math.max(0, total.value - 1)
    showToast('作品已发布，等级经验已同步')
  } catch (e: any) {
    showToast(e?.response?.data?.detail || '发布失败', 'error')
  }
}

function deleteDraft(draft: WorkItem) {
  pendingDeleteDraft.value = draft
  confirmVisible.value = true
}

async function doDeleteDraft() {
  const draft = pendingDeleteDraft.value
  if (!draft) return
  try {
    await worksApi.deleteWork(draft.id)
    drafts.value = drafts.value.filter(d => d.id !== draft.id)
    total.value = Math.max(0, total.value - 1)
    showToast('草稿已删除')
  } catch (e: any) {
    showToast(e?.response?.data?.detail || '删除失败', 'error')
  } finally {
    pendingDeleteDraft.value = null
  }
}

function truncateContent(content: string) {
  const lines = content.split('\n').filter(l => l.trim())
  const preview = lines.slice(0, 2).join('　')
  return preview.length > 60 ? preview.slice(0, 60) + '…' : preview || '（空）'
}

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
}

onMounted(() => fetchDrafts(true))
</script>

<style scoped>
.drafts-page {
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
  opacity: 0.12;
}

.ink-wash--1 {
  width: 450px;
  height: 450px;
  top: -120px;
  right: -80px;
  background: radial-gradient(circle, rgba(44,62,80,0.25), transparent 70%);
}

.ink-wash--2 {
  width: 350px;
  height: 350px;
  bottom: -80px;
  left: -60px;
  background: radial-gradient(circle, rgba(22,160,133,0.2), transparent 70%);
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

.nav-back:hover { color: var(--color-vermilion); }

.nav-title {
  font-family: var(--font-poem);
  font-size: 1.15rem;
  letter-spacing: 0.2em;
  color: var(--color-ink-dark);
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
  max-width: 860px;
  margin: 0 auto;
  padding: 28px 24px;
}

.drafts-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.draft-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 26px;
  border-radius: 20px;
  background: rgba(255,255,255,0.8);
  border: 1px solid rgba(44,62,80,0.07);
  box-shadow: 0 8px 24px rgba(44,62,80,0.05);
  transition: all var(--transition-fast);
}

.draft-card:hover {
  background: rgba(255,255,255,0.95);
  box-shadow: 0 12px 32px rgba(44,62,80,0.09);
  border-color: rgba(44,62,80,0.1);
}

.draft-card__left {
  flex: 1;
  min-width: 0;
}

.draft-card__status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  color: var(--color-warning);
  margin-bottom: 8px;
}

.draft-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-warning);
  animation: blink 2.4s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.draft-card__title {
  font-family: var(--font-title);
  font-size: 1.1rem;
  color: var(--color-ink-dark);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.draft-card__preview {
  font-family: var(--font-poem);
  font-size: 0.88rem;
  color: rgba(44,62,80,0.6);
  line-height: 1.6;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.draft-card__meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.draft-card__genre {
  font-size: 0.78rem;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(44,62,80,0.05);
  color: rgba(52,73,94,0.6);
}

.draft-card__time {
  font-size: 0.78rem;
  color: rgba(52,73,94,0.45);
}

.draft-card__actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.draft-action {
  height: 34px;
  padding: 0 16px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);
}

.draft-action--edit {
  background: rgba(22,160,133,0.1);
  color: var(--color-cyan);
}

.draft-action--edit:hover {
  background: rgba(22,160,133,0.18);
}

.draft-action--publish {
  background: linear-gradient(135deg, var(--color-vermilion), #b73325);
  color: #fff;
  box-shadow: 0 2px 8px rgba(192,57,43,0.15);
}

.draft-action--publish:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(192,57,43,0.22);
}

.draft-action--delete {
  background: rgba(231,76,60,0.06);
  color: rgba(231,76,60,0.7);
}

.draft-action--delete:hover {
  background: rgba(231,76,60,0.12);
  color: var(--color-error);
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
  padding: 100px 0 80px;
  gap: 10px;
}

.empty-glyph {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(44,62,80,0.04);
  font-family: var(--font-poem);
  font-size: 2.2rem;
  color: rgba(44,62,80,0.15);
  margin-bottom: 8px;
}

.empty-title {
  font-size: 1.05rem;
  color: var(--color-ink-dark);
  font-weight: 500;
}

.empty-desc {
  font-size: 0.88rem;
  color: rgba(52,73,94,0.5);
  max-width: 320px;
  text-align: center;
  line-height: 1.6;
}

.empty-state__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 6px;
}

.empty-action {
  margin-top: 12px;
  padding: 10px 24px;
  border-radius: 999px;
  background: var(--color-vermilion);
  color: #fff;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all var(--transition-fast);
}

.empty-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(192,57,43,0.25);
}

.empty-secondary {
  margin-top: 12px;
  padding: 10px 24px;
  border-radius: 999px;
  background: rgba(255,255,255,0.76);
  color: var(--color-ink-medium);
  text-decoration: none;
  font-size: 0.9rem;
  border: 1px solid rgba(44,62,80,0.12);
  transition: all var(--transition-fast);
}

.empty-secondary:hover {
  transform: translateY(-1px);
  border-color: rgba(192,57,43,0.16);
  color: var(--color-vermilion);
}

.drafts-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  padding: 14px 18px;
  border-radius: 18px;
  background: rgba(255,255,255,0.64);
  border: 1px solid rgba(44,62,80,0.06);
}

.drafts-summary__count {
  font-size: 0.9rem;
  color: var(--color-ink-dark);
}

.drafts-summary__hint {
  font-size: 0.78rem;
  color: rgba(52,73,94,0.5);
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
}

.btn-load-more:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 640px) {
  .draft-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }

  .draft-card__actions {
    width: 100%;
  }

  .draft-action {
    flex: 1;
    text-align: center;
  }

  .page-body {
    padding: 20px 16px;
  }

  .empty-state__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .drafts-summary {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
