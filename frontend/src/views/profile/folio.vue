<template>
  <div class="profile-page profile-page--folio">
    <div class="profile-page__texture"></div>
    <div class="profile-page__wash profile-page__wash--one"></div>
    <div class="profile-page__wash profile-page__wash--two"></div>

    <header class="profile-nav">
      <router-link to="/profile" class="profile-nav__brand">
        <span class="profile-nav__brand-mark">青衿赋</span>
        <span class="profile-nav__brand-sub">个人卷宗馆</span>
      </router-link>
      <nav class="profile-nav__links">
        <router-link to="/profile" class="profile-nav__link">个人中心</router-link>
        <router-link to="/poems" class="profile-nav__link">诗词学堂</router-link>
        <router-link to="/challenge" class="profile-nav__link">妙笔</router-link>
        <router-link to="/achievements" class="profile-nav__link profile-nav__link--accent">成就殿堂</router-link>
      </nav>
    </header>

    <main class="profile-layout profile-layout--folio">
      <section class="folio-page-hero">
        <div class="folio-page-hero__copy">
          <p class="folio-page-hero__eyebrow">PERSONAL FOLIO</p>
          <h1 class="folio-page-hero__title">{{ displayName }} 的卷宗馆</h1>
          <p class="folio-page-hero__text">
            把学习进度、收藏卷柜、妙笔记录与个人作品分栏归档，让个人中心回到摘要入口，把沉淀内容放到独立页面集中查看。
          </p>
        </div>

        <div class="folio-page-hero__aside">
          <div class="folio-page-hero__rank-card">
            <span class="folio-page-hero__rank-label">当前段位</span>
            <div class="folio-page-hero__rank-value">
              <UserRank :level="currentLevel" :exp="currentExp" compact class="folio-page-hero__rank-badge" />
              <strong class="folio-page-hero__rank-level">Lv.{{ currentLevel }}</strong>
            </div>
            <div class="folio-page-hero__rank-meta">
              <span>{{ currentRank.name }}</span>
              <span>{{ currentExp }} 文采</span>
            </div>
          </div>

          <p class="folio-page-hero__hint">{{ insightText }}</p>

          <div class="folio-page-hero__actions">
            <button type="button" class="action-stack__button action-stack__button--primary" @click="goProfileHome">
              返回个人中心
            </button>
            <button type="button" class="action-stack__button action-stack__button--secondary" @click="goAchievements('all')">
              全部成就
            </button>
            <button type="button" class="action-stack__button action-stack__button--secondary" @click="goCreateWork">
              立即创作
            </button>
          </div>
        </div>
      </section>

      <ProfileStatsGrid class="profile-stats-strip" :items="statsItems" />

      <section class="folio-board">
        <div class="folio-board__tabs">
          <button
            v-for="tab in profileFolioTabs"
            :key="tab.key"
            type="button"
            class="folio-board__tab"
            :class="{ 'is-active': activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <span class="folio-board__tab-mark">{{ tab.mark }}</span>
            <span>{{ tab.label }}</span>
          </button>
        </div>

        <div v-if="loading" class="folio-loading">
          <div class="folio-loading__row folio-loading__row--wide"></div>
          <div class="folio-loading__grid">
            <div class="folio-loading__card"></div>
            <div class="folio-loading__card"></div>
            <div class="folio-loading__card"></div>
          </div>
        </div>

        <div v-else class="folio-content">
          <template v-if="activeTab === 'overview'">
            <div class="overview-grid">
              <article class="folio-card folio-card--summary">
                <div class="folio-card__stamp">修习札记</div>
                <h3 class="folio-card__title">{{ displayName }} 的当下诗学节奏</h3>
                <div class="folio-highlight-grid">
                  <div v-for="item in overviewHighlights" :key="item.label" class="folio-highlight">
                    <span class="folio-highlight__label">{{ item.label }}</span>
                    <strong class="folio-highlight__value">{{ item.value }}</strong>
                  </div>
                </div>
                <div class="overview-actions">
                  <button type="button" class="action-stack__button action-stack__button--primary" @click="goPoems">
                    前往诗词学堂
                  </button>
                  <button type="button" class="action-stack__button action-stack__button--secondary" @click="goChallenge">
                    去妙笔
                  </button>
                </div>
              </article>

              <article class="folio-card folio-card--challenge">
                <div class="folio-card__stamp">挑战摘录</div>
                <h3 class="folio-card__title">妙笔留痕</h3>
                <ul v-if="challengeHistory.length" class="timeline-list">
                  <li v-for="item in challengeHistory.slice(0, 3)" :key="item.id" class="timeline-item">
                    <div>
                      <strong>{{ formatChallengeSummary(item) }}</strong>
                      <span>{{ formatDateTime(item.submitted_at) }}</span>
                    </div>
                    <span class="timeline-item__score">{{ formatChallengeType(item.challenge_type) }}</span>
                  </li>
                </ul>
                <div v-else class="empty-inline">暂未留下挑战记录，去试试妙笔吧。</div>
              </article>
            </div>
          </template>

          <template v-else-if="activeTab === 'progress'">
            <LearningProgress />
          </template>

          <template v-else-if="activeTab === 'favorites'">
            <div v-if="favorites.length" class="poem-grid">
              <button
                v-for="poem in favorites"
                :key="poem.id"
                type="button"
                class="poem-card"
                @click="goPoemDetail(poem.id)"
              >
                <div class="poem-card__meta">
                  <span>{{ poem.dynasty }}</span>
                  <span>{{ poem.genre || '诗作' }}</span>
                </div>
                <h3 class="poem-card__title">{{ poem.title }}</h3>
                <p class="poem-card__author">{{ poem.author }}</p>
                <p class="poem-card__excerpt">{{ previewPoem(poem.content) }}</p>
                <div class="poem-card__footer">
                  <span>收藏卷目</span>
                  <span>{{ poem.favorite_count }} 人喜欢</span>
                </div>
              </button>
            </div>
            <div v-else class="empty-panel">
              <div class="empty-panel__seal">藏</div>
              <h3>还没有收藏的诗卷</h3>
              <p>去诗词学堂挑几首喜欢的作品收进自己的卷柜里吧。</p>
              <button type="button" class="empty-panel__button" @click="goPoems">前往收藏诗词</button>
            </div>
          </template>

          <template v-else-if="activeTab === 'challenges'">
            <div v-if="challengeHistory.length" class="history-list">
              <article v-for="item in challengeHistory" :key="item.id" class="history-item">
                <div class="history-item__header">
                  <div>
                    <p class="history-item__time">{{ formatDateTime(item.submitted_at) }}</p>
                    <h3 class="history-item__answer">{{ formatChallengeSummary(item) }}</h3>
                  </div>
                  <div class="history-item__actions">
                    <span class="history-item__score">+{{ item.exp_gained }}经验</span>
                    <button
                      type="button"
                      class="history-item__delete"
                      @click="handleDeleteSubmission(item.id, item.exp_gained)"
                    >删除</button>
                  </div>
                </div>
                <div class="history-item__metrics">
                  <span>{{ formatChallengeType(item.challenge_type) }}</span>
                  <span v-if="item.answer_2">下句：{{ item.answer_2 }}</span>
                  <span v-else-if="item.content">续笔：{{ previewChallengeContent(item.content) }}</span>
                  <span>+{{ item.points_gained }}积分</span>
                </div>
              </article>
            </div>
            <div v-else class="empty-panel">
              <div class="empty-panel__seal">战</div>
              <h3>还没有妙笔记录</h3>
              <p>你在妙笔中的每次落笔、续写与经验收获，都会在这里沉淀成个人卷宗。</p>
              <button type="button" class="empty-panel__button" @click="goChallenge">立即挑战</button>
            </div>
          </template>

          <template v-else>
            <div v-if="works.length" class="profile-work-grid">
              <button
                v-for="work in works"
                :key="work.id"
                type="button"
                class="profile-work-card"
                @click="goWorkDetail(work.id)"
              >
                <div class="profile-work-card__head">
                  <span class="profile-work-card__genre">{{ work.genre }}</span>
                  <span class="profile-work-card__status" :class="`is-${work.status}`">
                    {{ work.status === 'published' ? '已发布' : '草稿中' }}
                  </span>
                </div>
                <h3 class="profile-work-card__title">{{ work.title }}</h3>
                <p class="profile-work-card__preview">{{ previewWork(work.content) }}</p>
                <div class="profile-work-card__meta">
                  <span>{{ formatDate(work.published_at || work.created_at) }}</span>
                  <span v-if="work.ai_total_score">AI {{ work.ai_total_score }}分</span>
                  <span v-else>待评分</span>
                </div>
                <div class="profile-work-card__footer">
                  <span>赞 {{ work.like_count }}</span>
                  <span>阅 {{ work.view_count }}</span>
                </div>
              </button>
            </div>
            <div v-else class="works-placeholder">
              <div class="works-placeholder__seal">作</div>
              <div class="works-placeholder__content">
                <p class="works-placeholder__eyebrow">CREATION ARCHIVE</p>
                <h3>你的文心卷还未落笔</h3>
                <p>
                  写下第一篇作品后，这里会展示你的草稿、已发布作品、AI评分与获赞情况。
                </p>
                <button type="button" class="works-placeholder__button" @click="goCreateWork">立即创作</button>
              </div>
            </div>
          </template>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UserRank from '@/components/UserRank.vue'
import ProfileStatsGrid from '@/components/profile/ProfileStatsGrid.vue'
import LearningProgress from './LearningProgress.vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { isProfileFolioTab, profileFolioTabs, type ProfileFolioTab, useProfileCenter } from './useProfileCenter'

const router = useRouter()
const route = useRoute()

const readQueryString = (value: unknown) => {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value[0] || ''
  return ''
}

const resolveTab = (value: unknown): ProfileFolioTab => {
  const tab = readQueryString(value)
  return isProfileFolioTab(tab) ? tab : 'overview'
}

const activeTab = ref<ProfileFolioTab>(resolveTab(route.query.tab))

const {
  loading,
  displayName,
  currentExp,
  currentLevel,
  currentRank,
  insightText,
  statsItems,
  favorites,
  challengeHistory,
  works,
  overviewHighlights,
  loadProfile,
  formatDateTime,
  previewPoem,
  previewWork,
  formatDate,
  formatChallengeType,
  previewChallengeContent,
  formatChallengeSummary,
  deleteChallengeSubmission
} = useProfileCenter()

const handleDeleteSubmission = async (id: number, expGained: number) => {
  try {
    await ElMessageBox.confirm(
      `删除此条落笔后，${expGained} 点经验与对应积分将一并扣回，此操作不可撤销。`,
      '确认删除落笔',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '再想想',
        type: 'warning',
        customClass: 'miaobi-confirm-dialog',
        closeOnClickModal: true,
        distinguishCancelAndClose: true
      }
    )
  } catch {
    return
  }
  try {
    const result = await deleteChallengeSubmission(id)
    ElMessage.success(result.message)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const goProfileHome = () => {
  router.push('/profile')
}

const goAchievements = (tab: 'progress' | 'all' = 'progress') => {
  router.push({
    path: '/achievements',
    query: tab === 'progress' ? {} : { tab }
  })
}

const goPoems = () => {
  router.push('/poems')
}

const goChallenge = () => {
  router.push('/challenge')
}

const goCreateWork = () => {
  router.push('/works/create')
}

const goPoemDetail = (id: number) => {
  router.push(`/poems/${id}`)
}

const goWorkDetail = (id: number) => {
  router.push(`/works/${id}`)
}

watch(
  () => route.query.tab,
  (value) => {
    const nextTab = resolveTab(value)
    if (nextTab !== activeTab.value) {
      activeTab.value = nextTab
    }
  }
)

watch(activeTab, (tab) => {
  const currentTab = readQueryString(route.query.tab)
  if (tab === 'overview' && !currentTab) return
  if (currentTab === tab) return

  router.replace({
    path: '/profile/folio',
    query: tab === 'overview' ? {} : { tab }
  })
})

onMounted(() => {
  activeTab.value = resolveTab(route.query.tab)
  void loadProfile()
})
</script>

<style scoped src="./styles/index.css"></style>
<style scoped src="./styles/folio-extensions.css"></style>
