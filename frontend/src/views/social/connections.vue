<template>
  <div class="connections-page">
    <div class="page-wash page-wash--1"></div>
    <div class="page-wash page-wash--2"></div>

    <nav class="page-nav">
      <div class="nav-inner">
        <AppBackButton label="返回" :fallback-to="backTarget" tone="light" class="connections-back" />
        <h1 class="page-title">{{ ownerLabel }}</h1>
        <div class="nav-placeholder"></div>
      </div>
    </nav>

    <div class="connections-body">
      <div class="tab-strip">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          <img :src="tab.icon" class="tab-icon" alt="" />
          <span class="tab-label">{{ tab.label }}</span>
          <span class="tab-count" v-if="tab.count > 0">{{ tab.count }}</span>
        </button>
        <div class="tab-ink" :style="tabInkStyle"></div>
      </div>

      <div class="connections-search" v-if="displayItems.length > 6 || searchQuery">
        <div class="search-box">
          <span class="search-icon">搜</span>
          <input
            v-model="searchQuery"
            class="search-input"
            :placeholder="activeTab === 'following' ? '搜索关注的诗友...' : '搜索粉丝...'"
          />
          <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''">清</button>
        </div>
      </div>

      <div class="list-area">
        <div v-if="loading && items.length === 0" class="loading-state">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
          <p class="loading-text">正在寻觅诗友...</p>
        </div>

        <div v-else-if="!loading && items.length === 0" class="empty-state">
          <div class="empty-seal">{{ activeTab === 'following' ? '寂' : '静' }}</div>
          <p class="empty-title">{{ activeTab === 'following' ? '尚未关注任何诗友' : '暂无粉丝' }}</p>
          <p class="empty-hint">{{ activeTab === 'following' ? '去诗友动态中发现志同道合的人吧' : '分享你的作品，吸引更多诗友关注' }}</p>
          <router-link v-if="activeTab === 'following' && isSelf" to="/social/feed" class="empty-action">
            前往动态
          </router-link>
        </div>

        <div v-else-if="filteredItems.length === 0 && searchQuery" class="empty-state">
          <div class="empty-seal">无</div>
          <p class="empty-title">未找到匹配的诗友</p>
          <p class="empty-hint">试试其他关键词</p>
        </div>

        <TransitionGroup v-else name="card-list" tag="div" class="user-list">
          <div
            v-for="(user, idx) in filteredItems"
            :key="user.user_id"
            class="user-card"
            :style="{ animationDelay: `${idx * 0.04}s` }"
          >
            <div class="card-left" @click="goToProfile(user.user_id)">
              <UserAvatar
                :username="user.username"
                :avatar="user.avatar_url"
                size="medium"
                :clickable="false"
              />
            </div>

            <div class="card-center" @click="goToProfile(user.user_id)">
              <div class="card-name-row">
                <span class="card-nickname">{{ user.nickname || user.username }}</span>
                <UserRank :level="user.level" :exp="0" compact class="card-rank" />
                <span
                  v-if="isMutual(user)"
                  class="mutual-badge"
                >互关</span>
              </div>
              <p v-if="user.nickname" class="card-username">@{{ user.username }}</p>
              <p v-if="user.bio" class="card-bio">{{ user.bio }}</p>
              <p v-else class="card-bio card-bio--empty">这位诗友很低调，什么都没写</p>
            </div>

            <div class="card-right" v-if="isSelf">
              <button
                v-if="activeTab === 'following'"
                class="action-btn action-btn--unfollow"
                @click.stop="handleUnfollow(user)"
                :disabled="user._busy"
              >
                {{ user._busy ? '...' : '取消关注' }}
              </button>
              <button
                v-else
                class="action-btn"
                :class="isFollowingUser(user) ? 'action-btn--following' : 'action-btn--follow'"
                @click.stop="handleToggleFollow(user)"
                :disabled="user._busy"
              >
                {{ user._busy ? '...' : isFollowingUser(user) ? '已关注' : '回关' }}
              </button>
            </div>
          </div>
        </TransitionGroup>

        <div class="load-more" v-if="items.length > 0 && items.length < total">
          <button class="load-btn" @click="loadMore" :disabled="loading">
            {{ loading ? '加载中...' : '加载更多' }}
          </button>
        </div>

        <div class="list-end" v-if="items.length > 0 && items.length >= total && items.length > 5">
          <img :src="inkBranchIcon" class="list-end-deco" alt="" />
          <span class="list-end-text">已至末页</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { socialApi, type FollowingItem, type FollowerItem } from '@/api/social'
import { useUserStore } from '@/store/modules/user'
import AppBackButton from '@/components/AppBackButton.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import UserRank from '@/components/UserRank.vue'
import followMutualIcon from '@/assets/icons/social/follow-mutual.svg'
import usersGroupIcon from '@/assets/icons/social/users-group.svg'
import inkBranchIcon from '@/assets/icons/social/ink-branch.svg'

type ConnectionUser = (FollowingItem | FollowerItem) & { _busy?: boolean }

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeTab = ref<'following' | 'followers'>('following')
const items = ref<ConnectionUser[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const searchQuery = ref('')
const followingTotal = ref(0)
const followerTotal = ref(0)

const targetUserId = computed(() => {
  const q = route.query.user_id
  return q ? Number(q) : undefined
})

const isSelf = computed(() => {
  if (!targetUserId.value) return true
  return userStore.userInfo?.id === targetUserId.value
})

const ownerLabel = computed(() => {
  if (isSelf.value) return '我的诗友'
  return '诗友圈'
})

const backTarget = computed(() => {
  if (targetUserId.value) return `/user/${targetUserId.value}`
  return '/social/feed'
})

const tabs = computed(() => [
  { key: 'following' as const, label: '关注', icon: followMutualIcon, count: followingTotal.value },
  { key: 'followers' as const, label: '粉丝', icon: usersGroupIcon, count: followerTotal.value }
])

const tabInkStyle = computed(() => {
  const idx = activeTab.value === 'following' ? 0 : 1
  return { transform: `translateX(${idx * 100}%)` }
})

const displayItems = computed(() => items.value)

const filteredItems = computed(() => {
  if (!searchQuery.value.trim()) return displayItems.value
  const q = searchQuery.value.toLowerCase()
  return displayItems.value.filter(u =>
    (u.username?.toLowerCase().includes(q)) ||
    (u.nickname?.toLowerCase().includes(q)) ||
    (u.bio?.toLowerCase().includes(q))
  )
})

const isMutual = (user: ConnectionUser) => {
  if (activeTab.value === 'following') return (user as FollowingItem).is_mutual
  return (user as FollowerItem).is_following
}

const isFollowingUser = (user: ConnectionUser) => {
  if (activeTab.value === 'following') return true
  return (user as FollowerItem).is_following
}

const switchTab = (tab: 'following' | 'followers') => {
  if (activeTab.value === tab) return
  activeTab.value = tab
  const newPath = tab === 'following' ? '/social/following' : '/social/followers'
  const query = targetUserId.value ? { user_id: String(targetUserId.value) } : {}
  router.replace({ path: newPath, query })
  resetAndLoad()
}

const resetAndLoad = () => {
  items.value = []
  page.value = 1
  total.value = 0
  searchQuery.value = ''
  loadData()
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      user_id: targetUserId.value,
      page: page.value,
      page_size: 20
    }
    if (activeTab.value === 'following') {
      const res = await socialApi.getFollowing(params)
      if (page.value === 1) {
        items.value = res.items.map(i => ({ ...i, _busy: false }))
      } else {
        items.value.push(...res.items.map(i => ({ ...i, _busy: false })))
      }
      total.value = res.total
      followingTotal.value = res.total
    } else {
      const res = await socialApi.getFollowers(params)
      if (page.value === 1) {
        items.value = res.items.map(i => ({ ...i, _busy: false }))
      } else {
        items.value.push(...res.items.map(i => ({ ...i, _busy: false })))
      }
      total.value = res.total
      followerTotal.value = res.total
    }
  } catch {
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  page.value++
  loadData()
}

const loadCounts = async () => {
  try {
    const params = { user_id: targetUserId.value, page: 1, page_size: 1 }
    const [fing, fers] = await Promise.all([
      socialApi.getFollowing(params),
      socialApi.getFollowers(params)
    ])
    followingTotal.value = fing.total
    followerTotal.value = fers.total
  } catch {}
}

const handleUnfollow = async (user: ConnectionUser) => {
  user._busy = true
  try {
    await socialApi.unfollowUser(user.user_id)
    items.value = items.value.filter(u => u.user_id !== user.user_id)
    total.value = Math.max(0, total.value - 1)
    followingTotal.value = Math.max(0, followingTotal.value - 1)
  } catch {
  } finally {
    user._busy = false
  }
}

const handleToggleFollow = async (user: ConnectionUser) => {
  const follower = user as FollowerItem & { _busy?: boolean }
  follower._busy = true
  try {
    if (follower.is_following) {
      await socialApi.unfollowUser(user.user_id)
      follower.is_following = false
      followingTotal.value = Math.max(0, followingTotal.value - 1)
    } else {
      await socialApi.followUser(user.user_id)
      follower.is_following = true
      followingTotal.value++
    }
  } catch {
  } finally {
    follower._busy = false
  }
}

const goToProfile = (userId: number) => {
  router.push(`/user/${userId}`)
}

onMounted(() => {
  if (route.path === '/social/followers') {
    activeTab.value = 'followers'
  }
  loadData()
  loadCounts()
})

watch(() => route.path, (newPath) => {
  if (newPath === '/social/following' && activeTab.value !== 'following') {
    activeTab.value = 'following'
    resetAndLoad()
  } else if (newPath === '/social/followers' && activeTab.value !== 'followers') {
    activeTab.value = 'followers'
    resetAndLoad()
  }
})
</script>

<style scoped>
.connections-page {
  min-height: 100vh;
  background: var(--color-paper-light);
  position: relative;
  overflow-x: hidden;
}

.page-wash {
  position: fixed;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}

.page-wash--1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -200px;
  background: radial-gradient(circle, rgba(69, 104, 93, 0.04) 0%, transparent 70%);
}

.page-wash--2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  left: -100px;
  background: radial-gradient(circle, rgba(178, 141, 87, 0.04) 0%, transparent 70%);
}

.page-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(249, 246, 240, 0.92);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--color-border);
}

.nav-inner {
  max-width: 700px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.connections-back {
  flex-shrink: 0;
}

.page-title {
  font-family: var(--font-title);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 4px;
  color: var(--color-ink-dark);
}

.nav-placeholder {
  width: 60px;
}

.connections-body {
  position: relative;
  z-index: 1;
  max-width: 640px;
  margin: 0 auto;
  padding: 0 20px 48px;
}

.tab-strip {
  display: flex;
  position: relative;
  margin: 20px 0 0;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 4px;
  gap: 0;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 0;
  border-radius: 10px;
  font-family: var(--font-title);
  font-size: 15px;
  letter-spacing: 2px;
  color: var(--color-ink-medium);
  background: transparent;
  transition: color var(--transition-fast);
  position: relative;
  z-index: 1;
  cursor: pointer;
}

.tab-item.active {
  color: var(--color-paper-white);
}

.tab-icon {
  width: 18px;
  height: 18px;
  opacity: 0.5;
  transition: opacity var(--transition-fast), filter var(--transition-fast);
}

.tab-item.active .tab-icon {
  opacity: 1;
  filter: brightness(0) invert(1);
}

.tab-count {
  font-family: var(--font-body);
  font-size: 12px;
  min-width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(18, 17, 16, 0.06);
  color: var(--color-ink-medium);
  padding: 0 6px;
  transition: all var(--transition-fast);
}

.tab-item.active .tab-count {
  background: rgba(255, 255, 255, 0.25);
  color: rgba(255, 255, 255, 0.9);
}

.tab-ink {
  position: absolute;
  top: 4px;
  left: 4px;
  width: calc(50% - 4px);
  height: calc(100% - 8px);
  background: var(--color-ink-dark);
  border-radius: 10px;
  transition: transform 380ms cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
  box-shadow: 0 2px 8px rgba(18, 17, 16, 0.15);
}

.connections-search {
  margin: 16px 0 0;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.search-box:focus-within {
  border-color: rgba(69, 104, 93, 0.3);
  box-shadow: 0 0 0 3px rgba(69, 104, 93, 0.06);
}

.search-icon {
  font-family: var(--font-title);
  font-size: 13px;
  color: var(--color-ink-medium);
  opacity: 0.35;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  transform: rotate(-4deg);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: var(--color-ink-dark);
  font-family: var(--font-body);
}

.search-input::placeholder {
  color: var(--color-ink-medium);
  opacity: 0.35;
}

.search-clear {
  font-family: var(--font-title);
  font-size: 12px;
  color: var(--color-ink-medium);
  opacity: 0.4;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(18, 17, 16, 0.04);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.search-clear:hover {
  opacity: 0.7;
  background: rgba(18, 17, 16, 0.08);
}

.list-area {
  margin-top: 20px;
}

.loading-state {
  text-align: center;
  padding: 80px 0;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.loading-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 16px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-ink-medium);
  opacity: 0.2;
  animation: dotPulse 1.2s ease infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotPulse {
  0%, 100% { opacity: 0.15; transform: scale(0.85); }
  50% { opacity: 0.5; transform: scale(1.1); }
}

.loading-text {
  font-family: var(--font-title);
  font-size: 14px;
  color: var(--color-ink-medium);
  opacity: 0.4;
  letter-spacing: 2px;
}

.empty-state {
  text-align: center;
  padding: 80px 0 60px;
  animation: fadeIn 0.5s ease;
}

.empty-seal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border: 2px solid var(--color-border);
  font-family: var(--font-title);
  font-size: 24px;
  color: var(--color-ink-medium);
  border-radius: 4px;
  margin-bottom: 20px;
  opacity: 0.25;
  transform: rotate(-6deg);
}

.empty-title {
  font-family: var(--font-title);
  font-size: 16px;
  color: var(--color-ink-medium);
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.empty-hint {
  font-size: 13px;
  color: var(--color-ink-medium);
  opacity: 0.4;
  margin-bottom: 20px;
}

.empty-action {
  display: inline-block;
  padding: 10px 28px;
  background: var(--color-ink-dark);
  color: var(--color-paper-white);
  border-radius: 20px;
  font-size: 14px;
  font-family: var(--font-title);
  letter-spacing: 2px;
  transition: all var(--transition-fast);
}

.empty-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(18, 17, 16, 0.15);
  color: var(--color-paper-white);
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  transition: all 280ms cubic-bezier(0.25, 0.1, 0.25, 1);
  animation: cardSlideIn 0.4s ease backwards;
  position: relative;
}

@keyframes cardSlideIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 16px;
  bottom: 16px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--color-cyan);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.user-card:hover {
  border-color: rgba(69, 104, 93, 0.18);
  box-shadow: 0 4px 16px rgba(18, 17, 16, 0.05);
  transform: translateX(2px);
}

.user-card:hover::before {
  opacity: 1;
}

.card-left {
  flex-shrink: 0;
  cursor: pointer;
}

.card-center {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.card-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.card-nickname {
  font-family: var(--font-title);
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink-dark);
  transition: color var(--transition-fast);
}

.card-center:hover .card-nickname {
  color: var(--color-vermilion);
}

.card-rank {
  flex-shrink: 0;
}

.mutual-badge {
  display: inline-flex;
  align-items: center;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(69, 104, 93, 0.08);
  color: var(--color-cyan);
  font-family: var(--font-title);
  letter-spacing: 1px;
  flex-shrink: 0;
}

.card-username {
  font-size: 12px;
  color: var(--color-ink-medium);
  opacity: 0.4;
  margin-top: 2px;
}

.card-bio {
  font-size: 13px;
  color: var(--color-ink-medium);
  margin-top: 6px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-family: var(--font-poem);
}

.card-bio--empty {
  opacity: 0.3;
  font-style: italic;
  font-family: var(--font-body);
}

.card-right {
  flex-shrink: 0;
}

.action-btn {
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 13px;
  font-family: var(--font-title);
  letter-spacing: 1px;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.action-btn--follow {
  background: var(--color-vermilion);
  color: white;
  border: 1px solid var(--color-vermilion);
}

.action-btn--follow:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(188, 42, 24, 0.2);
  transform: translateY(-1px);
}

.action-btn--following {
  background: transparent;
  color: var(--color-ink-medium);
  border: 1px solid var(--color-border);
}

.action-btn--following:hover:not(:disabled) {
  border-color: var(--color-vermilion);
  color: var(--color-vermilion);
}

.action-btn--unfollow {
  background: transparent;
  color: var(--color-ink-medium);
  border: 1px solid var(--color-border);
}

.action-btn--unfollow:hover:not(:disabled) {
  border-color: var(--color-vermilion);
  color: var(--color-vermilion);
  background: rgba(188, 42, 24, 0.04);
}

.card-list-enter-active {
  transition: all 0.35s ease;
}

.card-list-leave-active {
  transition: all 0.25s ease;
}

.card-list-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.card-list-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.card-list-move {
  transition: transform 0.3s ease;
}

.load-more {
  text-align: center;
  margin-top: 24px;
}

.load-btn {
  padding: 10px 36px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  font-size: 14px;
  font-family: var(--font-title);
  letter-spacing: 2px;
  color: var(--color-ink-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.load-btn:hover:not(:disabled) {
  border-color: var(--color-ink-medium);
  transform: translateY(-1px);
}

.load-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.list-end {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 0 16px;
  animation: fadeIn 0.5s ease;
}

.list-end-deco {
  width: 100px;
  height: 34px;
  opacity: 0.15;
}

.list-end-text {
  font-family: var(--font-title);
  font-size: 12px;
  color: var(--color-ink-medium);
  opacity: 0.25;
  letter-spacing: 4px;
}

@media (max-width: 640px) {
  .connections-body {
    padding: 0 16px 40px;
  }

  .user-card {
    padding: 14px 16px;
    gap: 12px;
    border-radius: 12px;
  }

  .card-bio {
    -webkit-line-clamp: 1;
  }

  .action-btn {
    padding: 6px 14px;
    font-size: 12px;
  }

  .tab-item {
    font-size: 14px;
    padding: 10px 0;
  }

  .tab-icon {
    width: 16px;
    height: 16px;
  }
}
</style>
