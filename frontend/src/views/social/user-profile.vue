<template>
  <div class="user-profile-page">
    <nav class="page-nav">
      <div class="nav-inner">
        <AppBackButton label="返回上一页" fallback-to="/social/feed" tone="light" class="user-profile-back" />
        <h1 class="page-title">诗友主页</h1>
        <div style="width:60px"></div>
      </div>
    </nav>

    <div class="profile-content" v-if="profile">
      <div class="profile-banner">
        <div class="banner-deco"></div>
      </div>
      <div class="profile-header">
        <div class="profile-avatar">{{ (profile.nickname || profile.username || '?')[0] }}</div>
        <div class="profile-info">
          <h2 class="profile-name">{{ profile.nickname || profile.username }}</h2>
          <p class="profile-username" v-if="profile.nickname">@{{ profile.username }}</p>
          <p class="profile-bio" v-if="profile.bio">{{ profile.bio }}</p>
          <div class="profile-meta">
            <div class="profile-rank-meta">
              <UserRank :level="profile.level" :exp="profile.exp" compact class="profile-rank-pill" />
              <span class="meta-item">文采 {{ profile.exp }}</span>
            </div>
            <span class="meta-dot"></span>
            <span class="meta-item">{{ profile.work_count }} 作品</span>
            <span class="meta-dot"></span>
            <span class="meta-item clickable" @click="$router.push(`/social/following?user_id=${profile.user_id}`)">{{ profile.following_count }} 关注</span>
            <span class="meta-dot"></span>
            <span class="meta-item clickable" @click="$router.push(`/social/followers?user_id=${profile.user_id}`)">{{ profile.follower_count }} 粉丝</span>
          </div>
        </div>
        <button v-if="!isSelf" class="follow-btn" :class="{ following: profile.is_following }" @click="toggleFollow">
          {{ profile.is_following ? '已关注' : '关注' }}
        </button>
      </div>

      <div class="section">
        <h3 class="section-title">成就徽章</h3>
        <div class="achievement-grid" v-if="profile.achievements.length > 0">
          <div v-for="a in profile.achievements" :key="a.id" class="achievement-badge" :class="a.rarity">
            <div class="badge-icon">{{ a.name[0] }}</div>
            <div class="badge-info">
              <span class="badge-name">{{ a.name }}</span>
              <span class="badge-desc">{{ a.description }}</span>
            </div>
          </div>
        </div>
        <div v-else class="section-empty">
          <span class="section-empty-text">还没有解锁成就</span>
        </div>
      </div>

      <div class="section">
        <h3 class="section-title">近期作品</h3>
        <div class="works-list" v-if="profile.recent_works.length > 0">
          <router-link v-for="w in profile.recent_works" :key="w.id" :to="`/works/${w.id}`" class="work-item">
            <div class="work-title">{{ w.title }}</div>
            <div class="work-meta">
              <span>{{ w.genre }}</span>
              <span>{{ w.like_count }} 赞</span>
            </div>
          </router-link>
        </div>
        <div v-else class="section-empty">
          <span class="section-empty-text">还没有发布作品</span>
          <router-link to="/works" class="section-empty-link">浏览作品墙</router-link>
        </div>
      </div>
    </div>

    <div class="profile-404" v-if="!profile && !loading">
      <div class="profile-404-seal">无</div>
      <p>未找到该用户</p>
      <router-link to="/social/feed" class="profile-404-link">返回诗友动态</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { socialApi, type UserPublicProfile } from '@/api/social'
import AppBackButton from '@/components/AppBackButton.vue'
import UserRank from '@/components/UserRank.vue'
import { useUserStore } from '@/store/modules/user'

const route = useRoute()
const userStore = useUserStore()
const profile = ref<UserPublicProfile | null>(null)
const loading = ref(false)

const isSelf = computed(() => {
  return userStore.userInfo && profile.value && userStore.userInfo.id === profile.value.user_id
})

const loadProfile = async () => {
  const userId = Number(route.params.id)
  if (!userId) return
  loading.value = true
  try {
    profile.value = await socialApi.getUserProfile(userId)
  } catch {
  } finally {
    loading.value = false
  }
}

const toggleFollow = async () => {
  if (!profile.value) return
  try {
    if (profile.value.is_following) {
      await socialApi.unfollowUser(profile.value.user_id)
      profile.value.is_following = false
      profile.value.follower_count--
    } else {
      await socialApi.followUser(profile.value.user_id)
      profile.value.is_following = true
      profile.value.follower_count++
    }
  } catch {
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.user-profile-page {
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

.user-profile-back {
  flex-shrink: 0;
}

.page-title {
  font-family: var(--font-title);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 4px;
}

.profile-content {
  max-width: 600px;
  margin: 0 auto;
  padding: 0 24px 32px;
}

.profile-banner {
  height: 80px;
  background: linear-gradient(135deg, rgba(69, 104, 93, 0.08), rgba(188, 42, 24, 0.06), rgba(178, 141, 87, 0.08));
  position: relative;
  overflow: hidden;
}

.banner-deco {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 30px,
    rgba(18, 17, 16, 0.01) 30px,
    rgba(18, 17, 16, 0.01) 31px
  );
}

.profile-header {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding: 0 0 28px;
  border-bottom: 1px solid var(--color-border);
  margin: -32px 0 28px;
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.5s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.profile-avatar {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  background: var(--color-paper-white);
  border: 3px solid var(--color-paper-white);
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-title);
  font-size: 26px;
  color: var(--color-ink-medium);
  flex-shrink: 0;
  transition: box-shadow var(--transition-fast);
}

.profile-avatar:hover {
  box-shadow: 0 0 0 3px rgba(188, 42, 24, 0.1), var(--shadow-md);
}

.profile-info { flex: 1; padding-top: 8px; }

.profile-name {
  font-family: var(--font-title);
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 2px;
}

.profile-username {
  font-size: 13px;
  color: var(--color-ink-medium);
  opacity: 0.5;
  margin-bottom: 6px;
}

.profile-bio {
  font-size: 14px;
  color: var(--color-ink-medium);
  margin-bottom: 10px;
  line-height: 1.5;
  font-family: var(--font-poem);
}

.profile-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.profile-rank-meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.profile-rank-pill {
  flex-shrink: 0;
}

.meta-item {
  font-size: 13px;
  color: var(--color-ink-medium);
  transition: color var(--transition-fast);
}

.meta-item.clickable { cursor: pointer; }
.meta-item.clickable:hover { color: var(--color-vermilion); }

.meta-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--color-border);
}

.follow-btn {
  padding: 8px 24px;
  border-radius: 20px;
  font-size: 14px;
  font-family: var(--font-title);
  letter-spacing: 2px;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--color-vermilion);
  color: white;
  border: 1px solid var(--color-vermilion);
  flex-shrink: 0;
  margin-top: 8px;
}

.follow-btn:hover { box-shadow: 0 4px 12px rgba(188, 42, 24, 0.2); transform: translateY(-1px); }

.follow-btn.following {
  background: transparent;
  color: var(--color-ink-medium);
  border-color: var(--color-border);
}

.follow-btn.following:hover {
  border-color: var(--color-vermilion);
  color: var(--color-vermilion);
  box-shadow: none;
  transform: none;
}

.section {
  margin-bottom: 32px;
  animation: fadeInUp 0.5s ease backwards;
}

.section:nth-child(2) { animation-delay: 0.1s; }
.section:nth-child(3) { animation-delay: 0.2s; }

.section-title {
  font-family: var(--font-title);
  font-size: 16px;
  letter-spacing: 2px;
  margin-bottom: 16px;
  padding-left: 12px;
  border-left: 3px solid var(--color-vermilion);
}

.achievement-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

.achievement-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.achievement-badge:hover { box-shadow: var(--shadow-sm); }
.achievement-badge.rare { border-color: rgba(69, 104, 93, 0.3); }
.achievement-badge.epic { border-color: rgba(178, 141, 87, 0.3); }
.achievement-badge.legendary { border-color: rgba(188, 42, 24, 0.3); }

.badge-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-title);
  font-size: 16px;
  font-weight: 700;
  background: var(--color-paper-light);
  color: var(--color-ink-medium);
  flex-shrink: 0;
  transition: box-shadow var(--transition-fast);
}

.achievement-badge.rare .badge-icon { color: var(--color-cyan); }
.achievement-badge.epic .badge-icon { color: var(--color-gold); }
.achievement-badge.legendary .badge-icon { color: var(--color-vermilion); }
.achievement-badge.legendary:hover .badge-icon { box-shadow: 0 0 12px rgba(188, 42, 24, 0.15); }

.badge-info { display: flex; flex-direction: column; gap: 2px; }
.badge-name { font-size: 14px; font-weight: 600; color: var(--color-ink-dark); }
.badge-desc { font-size: 12px; color: var(--color-ink-medium); opacity: 0.6; }

.works-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.work-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-ink-dark);
  transition: all var(--transition-fast);
}

.work-item:hover { border-color: var(--color-ink-medium); box-shadow: var(--shadow-sm); transform: translateX(2px); }

.work-title {
  font-family: var(--font-title);
  font-size: 15px;
  font-weight: 500;
}

.work-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--color-ink-medium);
  opacity: 0.5;
}

.section-empty {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border-radius: var(--radius-md);
  background: rgba(44, 62, 80, 0.02);
  border: 1px dashed var(--color-border);
}

.section-empty-text {
  font-size: 13px;
  color: var(--color-ink-medium);
  opacity: 0.4;
  font-family: var(--font-poem);
}

.section-empty-link {
  font-size: 13px;
  color: var(--color-vermilion);
  opacity: 0.7;
  transition: opacity var(--transition-fast);
}

.section-empty-link:hover {
  opacity: 1;
}

.profile-404 {
  text-align: center;
  padding: 100px 24px;
  color: var(--color-ink-medium);
  animation: fadeInUp 0.5s ease;
}

.profile-404-seal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border: 2px solid var(--color-border);
  border-radius: 4px;
  font-family: var(--font-title);
  font-size: 22px;
  opacity: 0.25;
  transform: rotate(-6deg);
  margin-bottom: 16px;
}

.profile-404-link {
  display: inline-block;
  margin-top: 16px;
  padding: 8px 24px;
  border-radius: 999px;
  font-size: 13px;
  background: var(--color-paper-white);
  border: 1px solid var(--color-border);
  color: var(--color-ink-medium);
  transition: all var(--transition-fast);
}

.profile-404-link:hover {
  border-color: var(--color-vermilion);
  color: var(--color-vermilion);
}

@media (max-width: 640px) {
  .profile-header { flex-wrap: wrap; }
  .achievement-grid { grid-template-columns: 1fr; }
}
</style>
