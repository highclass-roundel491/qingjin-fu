<template>
  <div class="profile-page">
    <div class="profile-page__texture"></div>
    <div class="profile-page__wash profile-page__wash--one"></div>
    <div class="profile-page__wash profile-page__wash--two"></div>

    <header class="profile-nav">
      <router-link to="/" class="profile-nav__brand">
        <span class="profile-nav__brand-mark">青衿赋</span>
        <span class="profile-nav__brand-sub">我的诗心卷宗</span>
      </router-link>
      <nav class="profile-nav__links">
        <router-link to="/poems" class="profile-nav__link">诗词学堂</router-link>
        <router-link to="/challenge" class="profile-nav__link">妙笔</router-link>
        <router-link to="/achievements" class="profile-nav__link profile-nav__link--accent">成就殿堂</router-link>
        <router-link to="/profile/folio" class="profile-nav__link">卷宗馆</router-link>
      </nav>
    </header>

    <main class="profile-layout">
      <section v-if="showWelcomeCard" class="welcome-card">
        <div class="welcome-card__header">
          <span class="welcome-card__badge">卷宗初启</span>
          <span class="welcome-card__name">{{ displayName }}，欢迎来到你的诗心卷宗</span>
        </div>
        <p class="welcome-card__desc">这里是你的个人档案中枢。目前数据还在等待落墨，下面几条路径可以帮你快速积累第一批成长痕迹。</p>
        <div class="welcome-card__steps">
          <button type="button" class="welcome-step" @click="goCreate">
            <span class="welcome-step__index">其一</span>
            <span class="welcome-step__title">写下第一篇作品</span>
            <span class="welcome-step__desc">进入创作页，用起手句或 AI 辅助完成第一次表达。</span>
          </button>
          <button type="button" class="welcome-step" @click="goChallenge">
            <span class="welcome-step__index">其二</span>
            <span class="welcome-step__title">试一次妙笔挑战</span>
            <span class="welcome-step__desc">每日一题，填字或续写，给卷宗留下第一笔记录。</span>
          </button>
          <button type="button" class="welcome-step" @click="goPoems">
            <span class="welcome-step__index">其三</span>
            <span class="welcome-step__title">逛一逛诗词学堂</span>
            <span class="welcome-step__desc">读一首诗、收藏一篇名篇，开始积累学习进度。</span>
          </button>
        </div>
      </section>

      <section class="profile-top">
        <ProfileHeroCard
          :user="userInfo"
          :stats="stats"
          :challenge-streak="challengeStreak"
          @navigate-challenge="goChallenge"
          @show-ranks="rankVisible = true"
        />

        <section class="profile-main">
          <div class="profile-main__header">
            <div class="profile-main__header-top">
              <div class="profile-main__intro">
                <p class="profile-main__eyebrow">PROFILE SNAPSHOT</p>
                <h2 class="profile-main__title">个人摘要</h2>
              </div>
              <div class="profile-main__header-side">
                <div class="profile-main__insight">
                  <span class="profile-main__insight-label">当前研习线索</span>
                  <strong class="profile-main__insight-value">{{ insightText }}</strong>
                </div>
              </div>
            </div>

            <div class="profile-main__quick-grid">
              <article v-for="item in quickItems" :key="item.label" class="profile-main__quick-item">
                <span class="profile-main__quick-label">{{ item.label }}</span>
                <strong class="profile-main__quick-value">{{ item.value }}</strong>
              </article>
            </div>

            <div class="profile-main__toolbar">
              <button type="button" class="profile-main__toolbar-button profile-main__toolbar-button--primary" @click="goFolio()">
                进入卷宗馆
              </button>
              <button type="button" class="profile-main__toolbar-button profile-main__toolbar-button--secondary" @click="goAchievements('all')">
                全部成就
              </button>
              <button type="button" class="profile-main__toolbar-button profile-main__toolbar-button--secondary" @click="passwordDialogVisible = true">
                修改密码
              </button>
              <button type="button" class="profile-main__toolbar-button profile-main__toolbar-button--secondary" @click="editDialogVisible = true">
                编辑资料
              </button>
              <button type="button" class="profile-main__toolbar-button profile-main__toolbar-button--ghost" @click="handleLogout">
                退出登录
              </button>
            </div>
          </div>
        </section>
      </section>

      <ProfileStatsGrid class="profile-stats-strip" :items="statsItems" />

      <section class="folio-entry">
        <div v-if="loading" class="folio-loading">
          <div class="folio-loading__row folio-loading__row--wide"></div>
          <div class="folio-loading__grid">
            <div class="folio-loading__card"></div>
            <div class="folio-loading__card"></div>
            <div class="folio-loading__card"></div>
          </div>
        </div>

        <template v-else>
          <article class="folio-entry__panel folio-entry__panel--trace">
            <div class="folio-entry__panel-head">
              <div>
                <p class="folio-entry__panel-eyebrow">RECENT TRACE</p>
                <h3 class="folio-entry__panel-title">近期落笔</h3>
              </div>
              <button type="button" class="folio-entry__panel-link" @click="goFolio('challenges')">查看全部</button>
            </div>

            <ul v-if="challengeHistory.length" class="timeline-list timeline-list--compact">
              <li v-for="item in challengeHistory.slice(0, 2)" :key="item.id" class="timeline-item">
                <div>
                  <strong>{{ formatChallengeSummary(item) }}</strong>
                  <span>{{ formatDateTime(item.submitted_at) }}</span>
                </div>
                <span class="timeline-item__score">{{ formatChallengeType(item.challenge_type) }}</span>
              </li>
            </ul>
            <div v-else class="empty-inline">暂未留下挑战记录，去试试妙笔吧。</div>
          </article>

          <article class="folio-entry__panel folio-entry__panel--actions">
            <div class="folio-entry__panel-head">
              <div>
                <p class="folio-entry__panel-eyebrow">ARCHIVE ENTRY</p>
                <h3 class="folio-entry__panel-title">常用入口</h3>
              </div>
            </div>

            <div class="folio-entry__mini-grid">
              <article class="folio-entry__mini-card">
                <span class="folio-entry__mini-label">收藏卷目</span>
                <strong class="folio-entry__mini-value">{{ favoritesTotal }}</strong>
              </article>
              <article class="folio-entry__mini-card">
                <span class="folio-entry__mini-label">我的作品</span>
                <strong class="folio-entry__mini-value">{{ worksTotal }}</strong>
              </article>
              <article class="folio-entry__mini-card">
                <span class="folio-entry__mini-label">妙笔经验</span>
                <strong class="folio-entry__mini-value">{{ challengeExpTotal }}</strong>
              </article>
            </div>

            <div class="folio-entry__quick-actions">
              <button type="button" class="action-stack__button action-stack__button--secondary" @click="goFolio('favorites')">
                我的收藏
              </button>
              <button type="button" class="action-stack__button action-stack__button--secondary" @click="goFolio('works')">
                我的作品
              </button>
            </div>
          </article>
        </template>
      </section>
    </main>

    <ProfileEditDialog
      v-model="editDialogVisible"
      :user="userInfo"
      @saved="handleProfileSaved"
    />

    <ProfilePasswordDialog
      v-model="passwordDialogVisible"
      @saved="handlePasswordSaved"
    />

    <RankOverview
      v-if="userInfo"
      v-model:visible="rankVisible"
      :current-level="currentLevel"
      :current-exp="currentExp"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import ProfileHeroCard from '@/components/profile/ProfileHeroCard.vue'
import ProfileEditDialog from '@/components/profile/ProfileEditDialog.vue'
import ProfilePasswordDialog from '@/components/profile/ProfilePasswordDialog.vue'
import ProfileStatsGrid from '@/components/profile/ProfileStatsGrid.vue'
import RankOverview from '@/components/RankOverview.vue'
import { useUserStore } from '@/store/modules/user'
import { isProfileFolioTab, type ProfileFolioTab, useProfileCenter } from './useProfileCenter'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const rankVisible = ref(false)
const editDialogVisible = ref(false)
const passwordDialogVisible = ref(false)

const {
  loading,
  userInfo,
  currentExp,
  currentLevel,
  stats,
  favoritesTotal,
  challengeHistory,
  challengeStreak,
  worksTotal,
  insightText,
  quickItems,
  statsItems,
  challengeExpTotal,
  displayName,
  loadProfile,
  formatDateTime,
  formatChallengeType,
  formatChallengeSummary
} = useProfileCenter()

const showWelcomeCard = computed(() => {
  if (loading.value) return false
  return worksTotal.value === 0 && challengeHistory.value.length === 0 && favoritesTotal.value === 0
})

const readQueryString = (value: unknown) => {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value[0] || ''
  return ''
}

const goFolio = (tab: ProfileFolioTab = 'overview') => {
  router.push({
    path: '/profile/folio',
    query: tab === 'overview' ? {} : { tab }
  })
}

const goAchievements = (tab: 'progress' | 'all' = 'progress') => {
  router.push({
    path: '/achievements',
    query: tab === 'progress' ? {} : { tab }
  })
}

const goChallenge = () => {
  router.push('/challenge')
}

const goCreate = () => {
  router.push('/works/create')
}

const goPoems = () => {
  router.push('/poems')
}

const handleProfileSaved = () => {
  void loadProfile()
}

const handlePasswordSaved = () => {
  passwordDialogVisible.value = false
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '退出后将返回首页，重新登录即可继续查看卷宗与创作记录。',
      '确认退出登录？',
      {
        confirmButtonText: '退出登录',
        cancelButtonText: '留在这里',
        type: 'warning',
        customClass: 'profile-logout-confirm',
        confirmButtonClass: 'profile-logout-confirm__confirm',
        cancelButtonClass: 'profile-logout-confirm__cancel',
        showClose: false,
        closeOnClickModal: false,
        closeOnPressEscape: false
      }
    )
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  } catch {}
}

onMounted(() => {
  const queryTab = readQueryString(route.query.tab)
  if (isProfileFolioTab(queryTab)) {
    router.replace({
      path: '/profile/folio',
      query: queryTab === 'overview' ? {} : { tab: queryTab }
    })
    return
  }
  void loadProfile()
})
</script>
<style scoped src="./styles/index.css"></style>
<style scoped src="./styles/folio-extensions.css"></style>
