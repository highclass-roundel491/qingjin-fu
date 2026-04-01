<template>
  <div class="home">
    <div class="ink-background">
      <div class="ink-layer layer-1"></div>
      <div class="ink-layer layer-2"></div>
      <div class="ink-layer layer-3"></div>
      <div class="ink-particles"></div>
    </div>

    <nav class="nav-bar" :class="{ 'scrolled': isScrolled }">
      <div class="nav-content">
        <div class="logo">
          <span class="logo-char">青</span>
          <span class="logo-char">衿</span>
          <span class="logo-char">赋</span>
        </div>
        <div class="nav-links">
          <router-link to="/poems" class="nav-link"><BookIcon class="nav-link-icon" />诗词学堂</router-link>
          <router-link to="/challenge" class="nav-link"><PenIcon class="nav-link-icon" />妙笔</router-link>
          <router-link to="/works" class="nav-link"><BrushIcon class="nav-link-icon" />诗词创作</router-link>
          <router-link to="/games" class="nav-link"><GameIcon class="nav-link-icon" />互动游戏</router-link>
          <router-link to="/graph" class="nav-link"><GraphIcon class="nav-link-icon" />文脉星图</router-link>
        </div>
        <div class="nav-actions">
          <template v-if="showAuthPlaceholder">
            <div class="nav-auth-placeholder" aria-hidden="true">
              <span class="nav-auth-placeholder__shimmer"></span>
            </div>
          </template>
          <template v-else-if="userStore.isLogin && userStore.userInfo">
            <UserAvatar 
              :username="userStore.userInfo.username" 
              :avatar="userStore.userInfo.avatar_url"
              :clickable="true"
              @click="handleAvatarClick"
            />
          </template>
          <template v-else>
            <button class="btn-secondary" @click="goToLogin">登录</button>
            <button class="btn-primary" @click="goToRegister">注册</button>
          </template>
        </div>
      </div>
    </nav>

    <section class="hero">
      <div class="hero-decoration hero-decoration-left"></div>
      <div class="hero-decoration hero-decoration-right"></div>
      
      <div class="hero-content">
        <div class="title-group">
          <div class="title-ornament title-ornament-top"></div>
          <h1 class="main-title">
            <span class="char" v-for="(char, index) in titleChars" :key="index" :style="{ animationDelay: `${index * 0.15}s` }">
              {{ char }}
            </span>
          </h1>
          <div class="title-ornament title-ornament-bottom"></div>
          <div class="subtitle">
            <span class="subtitle-char" v-for="(char, index) in subtitleChars" :key="index" :style="{ animationDelay: `${0.6 + index * 0.05}s` }">
              {{ char }}
            </span>
          </div>

          <div v-if="showGuidePanel" class="hero-guide">
            <span class="hero-guide__badge">{{ guideBadge }}</span>
            <p class="hero-guide__text">{{ guideText }}</p>
            <div class="hero-guide__actions">
              <button v-for="item in guideActions" :key="item.label" class="hero-guide__action" @click="item.action">
                {{ item.label }}
              </button>
            </div>
          </div>

          <div v-if="showOnboardingCard" class="onboarding-card">
            <div class="onboarding-card__header">
              <span class="onboarding-card__badge">新卷启程</span>
              <button class="onboarding-card__dismiss" @click="dismissOnboarding">稍后再看</button>
            </div>
            <h2 class="onboarding-card__title">欢迎回来，{{ onboardingName }}</h2>
            <p class="onboarding-card__desc">先从一首诗开始，再试一次妙笔，最后留下你的第一段作品，最容易找到自己的节奏。</p>
            <div class="onboarding-card__steps">
              <button class="onboarding-step" @click="startLearning">
                <span class="onboarding-step__index">其一</span>
                <span class="onboarding-step__title">先读一首诗</span>
                <span class="onboarding-step__desc">进入诗词学堂，看完注释与赏析。</span>
              </button>
              <button class="onboarding-step" @click="exploreChallenges">
                <span class="onboarding-step__index">其二</span>
                <span class="onboarding-step__title">再试一次妙笔</span>
                <span class="onboarding-step__desc">先完成一轮轻挑战，熟悉节奏与反馈。</span>
              </button>
              <button class="onboarding-step" @click="startCreating">
                <span class="onboarding-step__index">其三</span>
                <span class="onboarding-step__title">留下第一笔</span>
                <span class="onboarding-step__desc">去创作页落一段内容，建立你的卷宗痕迹。</span>
              </button>
            </div>
          </div>
          
          <div class="cta-buttons">
            <button class="btn-large btn-primary" @click="handlePrimaryAction">
              <span class="btn-text">{{ primaryActionLabel }}</span>
              <span class="btn-bg"></span>
              <ArrowRightIcon class="icon" />
            </button>
            <button class="btn-large btn-outline" @click="handleSecondaryAction">
              <span class="btn-text">{{ secondaryActionLabel }}</span>
              <span class="btn-bg"></span>
              <component :is="secondaryActionIcon" class="icon icon-outline" />
            </button>
          </div>
        </div>

        <div class="poem-showcase">
          <div class="poem-seal">诗</div>
          <div class="poem-text">
            <div class="poem-line" v-for="(line, index) in currentPoem.lines" :key="index" :style="{ animationDelay: `${1.2 + index * 0.2}s` }">
              <span class="poem-char" v-for="(char, charIndex) in line" :key="charIndex">{{ char }}</span>
            </div>
          </div>
          <div class="poem-author">{{ currentPoem.author }}</div>
          <div class="poem-corner poem-corner-tl"></div>
          <div class="poem-corner poem-corner-tr"></div>
          <div class="poem-corner poem-corner-bl"></div>
          <div class="poem-corner poem-corner-br"></div>
        </div>
      </div>
    </section>

    <section class="features">
      <div class="features-container">
        <div class="section-header">
          <div class="section-ornament">
            <svg class="ornament-knot" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.2">
              <rect x="6" y="6" width="12" height="12" rx="1" />
              <rect x="8" y="8" width="8" height="8" rx="0.5" />
              <path d="M6 6L2 2M18 6L22 2M6 18L2 22M18 18L22 22" stroke-linecap="round" />
            </svg>
          </div>
          <h2 class="section-title">平台特色</h2>
          <div class="section-subtitle">传统与现代的完美融合</div>
        </div>

        <div class="feature-grid">
          <div class="feature-card" v-for="(feature, index) in features" :key="index" :style="{ animationDelay: `${index * 0.1}s` }">
            <div class="feature-number">{{ formatFeatureNumber(index + 1) }}</div>
            <div class="feature-icon">
              <component :is="feature.icon" />
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.desc }}</p>
            <div class="feature-decoration"></div>
            <div class="feature-glow"></div>
          </div>
        </div>
      </div>
    </section>

    <section class="daily-challenge">
      <div class="challenge-bg-pattern"></div>
      <div class="challenge-container">
        <div class="challenge-card">
          <div class="challenge-stamp">今日</div>
          <div class="challenge-header">
            <div class="challenge-badge">
              <span class="badge-text">妙笔</span>
              <span class="badge-decoration"></span>
            </div>
            <div class="challenge-date">{{ currentDate }}</div>
          </div>
          <div class="challenge-content">
            <div class="challenge-sentence">
              <span v-for="(char, index) in challengeSentenceParts.before" :key="'b1-' + index" class="sentence-char">{{ char }}</span>
              <span class="blank">
                <span class="blank-inner">（？）</span>
                <span class="blank-glow"></span>
              </span>
              <span v-for="(char, index) in challengeSentenceParts.after" :key="'a1-' + index" class="sentence-char">{{ char }}</span>
            </div>
            <div v-if="challengeSentenceParts2" class="challenge-sentence">
              <span v-for="(char, index) in challengeSentenceParts2.before" :key="'b2-' + index" class="sentence-char">{{ char }}</span>
              <span class="blank">
                <span class="blank-inner">（？）</span>
                <span class="blank-glow"></span>
              </span>
              <span v-for="(char, index) in challengeSentenceParts2.after" :key="'a2-' + index" class="sentence-char">{{ char }}</span>
            </div>
            <div class="challenge-hint">
              <LightBulbIcon class="hint-icon" />
              <span>自由填字，不拘对错，尽抒才情</span>
            </div>
          </div>
          <button class="btn-challenge" @click="tryChallenge">
            <span class="btn-challenge-text">立即挑战</span>
            <span class="btn-challenge-arrow">→</span>
          </button>
        </div>
      </div>
    </section>

    <section class="stats">
      <div class="stats-bg"></div>
      <div class="stats-container">
        <div class="stat-item" v-for="(stat, index) in stats" :key="index">
          <div class="stat-decoration-icon"></div>
          <div class="stat-number" :data-number="stat.number">{{ stat.number }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </section>

    <footer class="footer">
      <div class="footer-content">
        <div class="footer-brand">
          <div class="footer-logo">青衿赋</div>
          <div class="footer-slogan">让诗词学习更有趣</div>
        </div>
        <div class="footer-links">
          <div class="footer-column">
            <h4>学习</h4>
            <router-link to="/poems">诗词学堂</router-link>
            <router-link to="/challenge">妙笔</router-link>
            <router-link to="/graph">文脉星图</router-link>
          </div>
          <div class="footer-column">
            <h4>创作</h4>
            <router-link to="/works/create">诗词创作</router-link>
            <router-link to="/works">作品展示</router-link>
            <router-link to="/works/rankings">创作排行</router-link>
          </div>
          <div class="footer-column">
            <h4>互动</h4>
            <router-link to="/games/feihualing">飞花令</router-link>
            <router-link to="/relay">诗词接龙</router-link>
            <router-link to="/social/feed">诗友动态</router-link>
          </div>
          <div class="footer-column">
            <h4>成长</h4>
            <router-link to="/achievements">成就殿堂</router-link>
            <router-link to="/relay/rankings">接龙排行</router-link>
            <router-link to="/profile">个人中心</router-link>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2026 青衿赋 - 中国大学生计算机设计大赛作品</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookIcon, PenIcon, BrushIcon, GameIcon, GraphIcon, ArrowRightIcon, LightBulbIcon } from '@/components/icons'
import { poemApi } from '@/api/poem'
import { statsApi } from '@/api/stats'
import { challengeApi, type DailyChallenge } from '@/api/challenge'
import { useUserStore } from '@/store/modules/user'
import UserAvatar from '@/components/UserAvatar.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const titleChars = '青衿赋'.split('')
const subtitleChars = '沉浸式传统诗词学习与创作平台'.split('')

const isScrolled = ref(false)

const currentPoem = ref({
  lines: ['春江潮水连海平', '海上明月共潮生'],
  author: '张若虚《春江花月夜》',
  title: '春江花月夜'
})

const totalPoems = ref(0)
const tangPoems = ref(0)
const songPoems = ref(0)
const dailyChallenge = ref<DailyChallenge | null>(null)

const currentDate = computed(() => {
  const date = new Date()
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
})

const showOnboardingCard = computed(() => {
  return route.query.onboarding === '1' && userStore.isLogin && Boolean(userStore.userInfo)
})

const homeMode = computed(() => {
  if (showOnboardingCard.value) return 'onboarding'
  if (userStore.isLogin) return 'member'
  return 'guest'
})

const onboardingName = computed(() => {
  return userStore.userInfo?.nickname || userStore.userInfo?.username || '青衿同窗'
})

const showGuidePanel = computed(() => {
  return homeMode.value !== 'onboarding'
})

const guideBadge = computed(() => {
  return homeMode.value === 'member' ? '卷宗续读' : '初来青衿'
})

const guideText = computed(() => {
  if (homeMode.value === 'member') {
    return '今日可继续诗词学堂、妙笔挑战或回到个人卷宗，把昨日的学习与创作节奏接续下去。'
  }

  return '初到青衿赋，建议先注册保存学习与创作记录；若想先感受平台氛围，也可以直接去读一首诗。'
})

const primaryActionLabel = computed(() => {
  if (homeMode.value === 'guest') return '注册开启卷宗'
  if (homeMode.value === 'member') return '继续学习'
  return '先读一首诗'
})

const secondaryActionLabel = computed(() => {
  if (homeMode.value === 'guest') return '先读一首诗'
  return '去试妙笔'
})

const secondaryActionIcon = computed(() => {
  return homeMode.value === 'guest' ? BookIcon : PenIcon
})

const showAuthPlaceholder = computed(() => {
  return Boolean(userStore.token) && (userStore.authLoading || !userStore.authReady)
})

const guideActions = computed(() => {
  if (homeMode.value === 'member') {
    return [
      {
        label: '个人卷宗',
        action: handleAvatarClick
      },
      {
        label: '诗词创作',
        action: startCreating
      }
    ]
  }

  return [
    {
      label: '作品墙',
      action: openWorksHall
    },
    {
      label: '文脉星图',
      action: openGraph
    }
  ]
})

const features = [
  {
    icon: BookIcon,
    title: '诗词学堂',
    desc: '海量诗词库，按朝代、作者、主题分类，深度注释与赏析'
  },
  {
    icon: PenIcon,
    title: '妙笔',
    desc: '开放式填字与续写，以诗会友，妙笔生花'
  },
  {
    icon: BrushIcon,
    title: '诗词创作',
    desc: 'AI辅助创作，格律检查，智能评分，发布作品展示'
  },
  {
    icon: GameIcon,
    title: '互动游戏',
    desc: '飞花令、诗词接龙、限时挑战，寓教于乐'
  }
]

const stats = computed(() => [
  { number: totalPoems.value.toLocaleString() + '+', label: '诗词收录' },
  { number: tangPoems.value.toLocaleString() + '+', label: '唐诗' },
  { number: songPoems.value.toLocaleString() + '+', label: '宋词' },
  { number: '10000+', label: '学习人次' }
])

const loadRandomPoem = async () => {
  try {
    const poem = await poemApi.getRandom()
    const lines = poem.content.split('\n').filter(line => line.trim())
    currentPoem.value = {
      lines: lines.slice(0, 2),
      author: `${poem.author}《${poem.title}》`,
      title: poem.title
    }
  } catch (error) {
    console.error('加载诗词失败:', error)
  }
}

const loadStats = async () => {
  try {
    const data = await statsApi.getPlatformStats()
    totalPoems.value = data.total_poems
    tangPoems.value = data.tang_poems
    songPoems.value = data.song_poems
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadDailyChallenge = async () => {
  try {
    dailyChallenge.value = await challengeApi.getDaily()
  } catch (error) {
    console.error('加载每日挑战失败:', error)
  }
}

const challengeSentenceParts = computed(() => {
  if (!dailyChallenge.value) {
    return { before: '寒江', after: '茶暖' }
  }
  const parts = dailyChallenge.value.sentence_template.split('__')
  return {
    before: parts[0] || '',
    after: parts[1] || ''
  }
})

const challengeSentenceParts2 = computed(() => {
  if (!dailyChallenge.value?.sentence_template_2) {
    return null
  }
  const parts = dailyChallenge.value.sentence_template_2.split('__')
  return {
    before: parts[0] || '',
    after: parts[1] || ''
  }
})

const handleScroll = () => {
  isScrolled.value = window.scrollY > 50
}

const formatFeatureNumber = (num: number) => {
  return String(num).padStart(2, '0')
}

onMounted(() => {
  loadRandomPoem()
  loadStats()
  loadDailyChallenge()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const goToLogin = () => {
  router.push('/login')
}

const goToRegister = () => {
  router.push('/register')
}

const dismissOnboarding = () => {
  router.replace('/')
}

const handlePrimaryAction = () => {
  if (homeMode.value === 'guest') {
    goToRegister()
    return
  }

  startLearning()
}

const handleSecondaryAction = () => {
  if (homeMode.value === 'guest') {
    startLearning()
    return
  }

  exploreChallenges()
}

const startLearning = () => {
  router.push('/poems')
}

const exploreChallenges = () => {
  router.push('/challenge')
}

const startCreating = () => {
  router.push('/works/create')
}

const openWorksHall = () => {
  router.push('/works')
}

const openGraph = () => {
  router.push('/graph')
}

const tryChallenge = () => {
  router.push('/challenge')
}

const handleAvatarClick = () => {
  router.push('/profile')
}

</script>

<style scoped src="./styles/base.css"></style>
<style scoped src="./styles/background.css"></style>
<style scoped src="./styles/navigation.css"></style>
<style scoped src="./styles/hero.css"></style>
<style scoped src="./styles/poem.css"></style>
<style scoped src="./styles/buttons.css"></style>
<style scoped src="./styles/features.css"></style>
<style scoped src="./styles/challenge.css"></style>
<style scoped src="./styles/stats.css"></style>
<style scoped src="./styles/footer.css"></style>
