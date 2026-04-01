<template>
  <div class="feed-page">
    <nav class="page-nav">
      <div class="nav-inner">
        <router-link to="/" class="back-link">
          <img :src="chainLinkIcon" class="back-icon" alt="" />
          <span>首页</span>
        </router-link>
        <h1 class="page-title">诗友动态</h1>
        <div class="nav-actions">
          <router-link to="/social/following" class="nav-action-link">关注</router-link>
          <router-link to="/social/followers" class="nav-action-link">粉丝</router-link>
        </div>
      </div>
    </nav>

    <div class="feed-content">
      <div class="empty-state" v-if="!loading && items.length === 0">
        <div class="empty-seal">静</div>
        <p class="empty-title">诗友圈尚无波澜</p>
        <p class="empty-hint">关注感兴趣的诗友，他们的创作、点赞、成就都会出现在这里</p>
        <div class="empty-actions">
          <router-link to="/works" class="empty-action-btn empty-action-btn--primary">浏览作品墙</router-link>
          <router-link to="/works/rankings" class="empty-action-btn">创作排行榜</router-link>
          <router-link to="/relay" class="empty-action-btn">诗词接龙</router-link>
        </div>
        <p class="empty-tip">在作品详情或排行榜中，点击作者头像即可关注</p>
      </div>

      <div class="feed-list" v-if="items.length > 0">
        <div v-for="(item, idx) in items" :key="item.id" class="feed-card" :class="item.type" :style="{ animationDelay: idx * 0.04 + 's' }">
          <div class="feed-avatar" @click="goToProfile(item.user_id)">
            {{ (item.username || '?')[0] }}
          </div>
          <div class="feed-body">
            <div class="feed-header">
              <span class="feed-username" @click="goToProfile(item.user_id)">{{ item.username }}</span>
              <span class="feed-type-tag" :class="item.type">{{ typeLabel(item.type) }}</span>
            </div>
            <div class="feed-text">{{ item.content }}</div>
            <div class="feed-footer">
              <span class="feed-time">{{ timeAgo(item.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="load-more" v-if="items.length > 0 && items.length < total">
        <button class="load-btn" @click="loadMore" :disabled="loading">{{ loading ? '...' : '加载更多' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { socialApi, type ActivityFeedItem } from '@/api/social'
import chainLinkIcon from '@/assets/icons/relay/chain-link.svg'

const router = useRouter()
const items = ref<ActivityFeedItem[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

const typeLabel = (t: string) => {
  const map: Record<string, string> = {
    work_published: '发布作品',
    work_liked: '点赞',
    achievement_unlocked: '成就',
    relay_record: '接龙',
    challenge_completed: '挑战',
    level_up: '升级'
  }
  return map[t] || t
}

const timeAgo = (t: string) => {
  const now = Date.now()
  const diff = now - new Date(t).getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min}分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}小时前`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day}天前`
  return new Date(t).toLocaleDateString()
}

const goToProfile = (userId: number) => {
  router.push(`/user/${userId}`)
}

const loadFeed = async () => {
  loading.value = true
  try {
    const res = await socialApi.getFeed({ page: page.value, page_size: 20 })
    if (page.value === 1) {
      items.value = res.items
    } else {
      items.value.push(...res.items)
    }
    total.value = res.total
  } catch {
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  page.value++
  loadFeed()
}

onMounted(loadFeed)
</script>

<style scoped>
.feed-page {
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
  max-width: 700px;
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

.nav-actions { display: flex; gap: 16px; }
.nav-action-link { font-size: 14px; color: var(--color-ink-medium); transition: color var(--transition-fast); }
.nav-action-link:hover { color: var(--color-vermilion); }

.feed-content {
  max-width: 600px;
  margin: 0 auto;
  padding: 24px;
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

.empty-title { font-family: var(--font-title); font-size: 16px; letter-spacing: 0.15em; color: var(--color-ink-dark); margin-bottom: 4px; }
.empty-hint { font-size: 13px; opacity: 0.5; margin-top: 0; line-height: 1.7; max-width: 320px; margin-left: auto; margin-right: auto; }

.empty-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 24px;
}

.empty-action-btn {
  padding: 10px 22px;
  border-radius: 999px;
  font-size: 13px;
  font-family: var(--font-title);
  letter-spacing: 0.08em;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  color: var(--color-ink-medium);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.empty-action-btn:hover {
  border-color: var(--color-ink-medium);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.empty-action-btn--primary {
  background: var(--color-ink-dark);
  color: var(--color-paper-white);
  border-color: var(--color-ink-dark);
}

.empty-action-btn--primary:hover {
  box-shadow: 0 4px 12px rgba(18, 17, 16, 0.15);
  border-color: var(--color-ink-dark);
}

.empty-tip {
  font-size: 12px;
  color: var(--color-ink-medium);
  opacity: 0.35;
  margin-top: 20px;
}

.feed-list { display: flex; flex-direction: column; gap: 10px; }

.feed-card {
  display: flex;
  gap: 14px;
  padding: 16px 20px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  animation: cardEnter 0.35s ease backwards;
  border-left: 3px solid var(--color-border);
}

@keyframes cardEnter {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.feed-card:hover { box-shadow: var(--shadow-sm); border-color: rgba(18, 17, 16, 0.12); }

.feed-card.work_published { border-left-color: var(--color-cyan); }
.feed-card.work_liked { border-left-color: var(--color-vermilion); }
.feed-card.achievement_unlocked { border-left-color: var(--color-gold); }
.feed-card.relay_record { border-left-color: var(--color-vermilion); }
.feed-card.challenge_completed { border-left-color: var(--color-cyan); }
.feed-card.level_up { border-left-color: var(--color-gold); }

.feed-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-paper-light);
  border: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-title);
  font-size: 14px;
  color: var(--color-ink-medium);
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.feed-avatar:hover {
  border-color: var(--color-vermilion);
  color: var(--color-vermilion);
  transform: scale(1.05);
}

.feed-body { flex: 1; min-width: 0; }

.feed-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.feed-username {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink-dark);
  cursor: pointer;
  transition: color var(--transition-fast);
}
.feed-username:hover { color: var(--color-vermilion); }

.feed-type-tag {
  display: inline-block;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--color-paper-light);
  color: var(--color-ink-medium);
  flex-shrink: 0;
}

.feed-type-tag.work_published { color: var(--color-cyan); }
.feed-type-tag.achievement_unlocked { color: var(--color-gold); }
.feed-type-tag.relay_record { color: var(--color-vermilion); }
.feed-type-tag.level_up { color: var(--color-gold); }

.feed-text {
  font-size: 14px;
  color: var(--color-ink-dark);
  line-height: 1.6;
}

.feed-footer {
  margin-top: 8px;
}

.feed-time {
  font-size: 11px;
  color: var(--color-ink-medium);
  opacity: 0.4;
}

.load-more { text-align: center; margin-top: 24px; }

.load-btn {
  padding: 10px 32px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  font-size: 14px;
  color: var(--color-ink-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.load-btn:hover { border-color: var(--color-ink-medium); }
.load-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
