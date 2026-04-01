import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { learningApi, type UserStats } from '@/api/learning'
import { challengeApi, type ChallengeHistoryItem } from '@/api/challenge'
import type { Poem } from '@/api/poem'
import { userApi, type UserProfileStats } from '@/api/user'
import { worksApi, type WorkItem } from '@/api/works'
import { useUserStore } from '@/store/modules/user'
import { getRankByExp } from '@/utils/levels'

export type ProfileFolioTab = 'overview' | 'progress' | 'favorites' | 'challenges' | 'works'

export const profileFolioTabs: Array<{ key: ProfileFolioTab; label: string; mark: string }> = [
  { key: 'overview', label: '卷宗总览', mark: '卷' },
  { key: 'progress', label: '学习进度', mark: '进' },
  { key: 'favorites', label: '我的收藏', mark: '藏' },
  { key: 'challenges', label: '妙笔记录', mark: '笔' },
  { key: 'works', label: '我的作品', mark: '作' }
]

export const isProfileFolioTab = (value: string): value is ProfileFolioTab => {
  return profileFolioTabs.some(item => item.key === value)
}

export function useProfileCenter() {
  const router = useRouter()
  const userStore = useUserStore()

  const loading = ref(true)
  const stats = ref<UserStats | null>(null)
  const favorites = ref<Poem[]>([])
  const favoritesTotal = ref(0)
  const challengeHistory = ref<ChallengeHistoryItem[]>([])
  const challengeStreak = ref(0)
  const works = ref<WorkItem[]>([])
  const worksTotal = ref(0)
  const userSummaryStats = ref<UserProfileStats | null>(null)

  const userInfo = computed(() => userStore.userInfo)
  const displayName = computed(() => userInfo.value?.nickname || userInfo.value?.username || '青衿旅人')
  const currentExp = computed(() => stats.value?.exp || userInfo.value?.exp || 0)
  const currentRank = computed(() => getRankByExp(currentExp.value))
  const currentLevel = computed(() => currentRank.value.level)

  const challengeExpTotal = computed(() => {
    if (!challengeHistory.value.length) return 0
    return challengeHistory.value.reduce((sum, item) => sum + item.exp_gained, 0)
  })

  const challengeFillCount = computed(() => {
    return challengeHistory.value.filter(item => item.challenge_type === 'fill_blank').length
  })

  const challengeContinueCount = computed(() => {
    return challengeHistory.value.filter(item => item.challenge_type === 'continue_line').length
  })

  const insightText = computed(() => {
    if (challengeHistory.value.length) {
      return `已在妙笔留下 ${challengeHistory.value.length} 次落笔，累计获得 ${challengeExpTotal.value} 点经验`
    }
    if (userSummaryStats.value?.total_works_created) {
      return `已沉淀 ${userSummaryStats.value.total_works_created} 篇个人作品`
    }
    if (stats.value?.total_learned) {
      return `已收进 ${stats.value.total_learned} 首研习诗词`
    }
    return '你的诗学履历正等待落墨'
  })

  const latestWork = computed(() => works.value[0] || null)

  const nextGoalText = computed(() => {
    if ((userSummaryStats.value?.total_works_created || worksTotal.value) < 1) return '写下第一篇作品'
    if ((stats.value?.total_learned || 0) < 10) return '读满10首名篇'
    if (challengeStreak.value < 3) return '连续挑战3天'
    if (favoritesTotal.value < 5) return '收藏5篇心仪作品'
    return '继续提升作品质量'
  })

  const quickItems = computed(() => [
    {
      label: '当前焦点',
      value: nextGoalText.value
    },
    {
      label: '最近作品',
      value: latestWork.value?.title || '尚未落笔'
    },
    {
      label: '挑战状态',
      value: challengeHistory.value.length ? `填字 ${challengeFillCount.value} / 续写 ${challengeContinueCount.value}` : '待开启'
    }
  ])

  const statsItems = computed(() => [
    {
      label: '已学诗词',
      value: `${stats.value?.total_learned || 0}`,
      glyph: '学',
      accent: 'vermillion' as const
    },
    {
      label: '收藏卷目',
      value: `${favoritesTotal.value}`,
      glyph: '藏',
      accent: 'jade' as const
    },
    {
      label: '研习时长',
      value: formatDuration(stats.value?.study_time || 0),
      glyph: '时',
      accent: 'ink' as const
    },
    {
      label: '连续挑战',
      value: `${challengeStreak.value}天`,
      glyph: '燃',
      accent: 'gold' as const
    }
  ])

  const overviewHighlights = computed(() => [
    {
      label: '妙笔落笔',
      value: challengeHistory.value.length ? `${challengeHistory.value.length}次` : '待解锁'
    },
    {
      label: '妙笔收益',
      value: challengeHistory.value.length ? `${challengeExpTotal.value}经验` : '待积累'
    },
    {
      label: '落笔分布',
      value: challengeHistory.value.length ? `${challengeFillCount.value}填字 / ${challengeContinueCount.value}续写` : nextGoalText.value
    }
  ])

  const ensureLogin = () => {
    if (!userStore.isLogin) {
      ElMessage.warning('请先登录后再查看个人中心')
      router.replace('/login')
      return false
    }
    return true
  }

  const loadProfile = async () => {
    if (!ensureLogin()) {
      loading.value = false
      return
    }

    loading.value = true

    try {
      await userStore.fetchUserInfo()

      const currentUserId = userStore.userInfo?.id

      const [statsResult, favoritesResult, historyResult, worksResult, summaryResult] = await Promise.allSettled([
        learningApi.getStats(),
        userApi.getFavorites({ page: 1, page_size: 6 }),
        challengeApi.getHistory({ page: 1, page_size: 10 }),
        worksApi.getMyWorks({ page: 1, page_size: 6 }),
        currentUserId ? userApi.getUserStats(currentUserId) : Promise.resolve(null)
      ])

      if (statsResult.status === 'fulfilled') {
        stats.value = statsResult.value
      } else {
        stats.value = null
      }

      if (favoritesResult.status === 'fulfilled') {
        favorites.value = favoritesResult.value.items
        favoritesTotal.value = favoritesResult.value.total
      } else {
        favorites.value = []
        favoritesTotal.value = 0
      }

      if (historyResult.status === 'fulfilled') {
        challengeHistory.value = historyResult.value.items
        challengeStreak.value = historyResult.value.streak_days
      } else {
        challengeHistory.value = []
        challengeStreak.value = 0
      }

      if (worksResult.status === 'fulfilled') {
        works.value = worksResult.value.items
        worksTotal.value = worksResult.value.total
      } else {
        works.value = []
        worksTotal.value = 0
      }

      if (summaryResult.status === 'fulfilled') {
        userSummaryStats.value = summaryResult.value
      } else {
        userSummaryStats.value = null
      }
    } finally {
      loading.value = false
    }
  }

  const formatDuration = (seconds: number) => {
    if (!seconds) return '0分'
    const totalMinutes = Math.max(1, Math.round(seconds / 60))
    const hours = Math.floor(totalMinutes / 60)
    const minutes = totalMinutes % 60
    if (hours && minutes) return `${hours}时${minutes}分`
    if (hours) return `${hours}时`
    return `${minutes}分`
  }

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr)
    if (Number.isNaN(date.getTime())) return '刚刚'
    return `${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }

  const previewPoem = (content: string) => {
    const lines = content.split('\n').map(line => line.trim()).filter(Boolean)
    return lines.slice(0, 2).join(' / ') || content
  }

  const previewWork = (content: string) => {
    const lines = content.split('\n').map(line => line.trim()).filter(Boolean)
    return lines.slice(0, 3).join(' / ') || content
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    if (Number.isNaN(date.getTime())) return '刚刚落卷'
    return `${date.getMonth() + 1}月${date.getDate()}日`
  }

  const formatChallengeType = (type?: string) => {
    return type === 'continue_line' ? '续写接力' : '填字妙想'
  }

  const previewChallengeContent = (content: string) => {
    return content.length > 14 ? `${content.slice(0, 14)}…` : content
  }

  const formatChallengeSummary = (item: ChallengeHistoryItem) => {
    if (item.challenge_type === 'continue_line') {
      return item.content || item.answer
    }
    return [item.answer, item.answer_2].filter(Boolean).join(' / ')
  }

  const deleteChallengeSubmission = async (id: number) => {
    const result = await challengeApi.deleteSubmission(id)
    challengeHistory.value = challengeHistory.value.filter(item => item.id !== id)
    await userStore.fetchUserInfo()
    return result
  }

  return {
    loading,
    stats,
    favorites,
    favoritesTotal,
    challengeHistory,
    challengeStreak,
    works,
    worksTotal,
    userSummaryStats,
    userInfo,
    displayName,
    currentExp,
    currentLevel,
    currentRank,
    insightText,
    latestWork,
    quickItems,
    statsItems,
    challengeExpTotal,
    challengeFillCount,
    challengeContinueCount,
    overviewHighlights,
    nextGoalText,
    loadProfile,
    formatDuration,
    formatDateTime,
    previewPoem,
    previewWork,
    formatDate,
    formatChallengeType,
    previewChallengeContent,
    formatChallengeSummary,
    deleteChallengeSubmission
  }
}
