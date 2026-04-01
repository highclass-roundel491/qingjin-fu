<template>
  <div class="auth-page auth-page--login">
    <div class="auth-page__texture"></div>
    <div class="auth-page__wash auth-page__wash--one"></div>
    <div class="auth-page__wash auth-page__wash--two"></div>

    <header class="auth-topbar">
      <router-link to="/" class="auth-topbar__brand">
        <span class="auth-topbar__brand-mark">青衿赋</span>
        <span class="auth-topbar__brand-sub">诗学卷宗认证入口</span>
      </router-link>
      <div class="auth-topbar__actions">
        <router-link to="/" class="auth-topbar__link">
          <el-icon><House /></el-icon>
          <span>返回首页</span>
        </router-link>
        <router-link :to="registerLink" class="auth-topbar__link auth-topbar__link--accent">
          <span>新建诗笺</span>
        </router-link>
      </div>
    </header>

    <main class="auth-shell auth-shell--login">
      <section class="auth-hero">
        <div class="auth-hero__seal">归</div>

        <div class="auth-hero__content">
          <p class="auth-hero__eyebrow">诗学卷宗入口</p>
          <h1 class="auth-hero__title">回到你的诗学卷宗</h1>
          <p class="auth-hero__description">
            登录后可继续诗词学堂研习、妙笔挑战、作品创作与个人成长记录，保持你的学习与创作节奏。
          </p>
        </div>

        <div class="auth-hero__summary">
          <article v-for="item in highlights" :key="item.title" class="auth-summary-item">
            <span class="auth-summary-item__mark">{{ item.mark }}</span>
            <div class="auth-summary-item__content">
              <h3 class="auth-summary-item__title">{{ item.title }}</h3>
              <p class="auth-summary-item__desc">{{ item.desc }}</p>
            </div>
          </article>
        </div>
      </section>

      <section class="auth-card">
        <div class="auth-card__header">
          <p class="auth-card__eyebrow">账号登录</p>
          <h2 class="auth-card__title">欢迎回来</h2>
          <p class="auth-card__subtitle">输入账号信息，即可回到你的个人卷宗。</p>
        </div>

        <div class="auth-card__status">
          <span class="auth-card__status-dot"></span>
          <span>{{ statusText }}</span>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          :hide-required-asterisk="true"
          class="auth-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              autocomplete="username"
              clearable
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              autocomplete="current-password"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item>
            <el-button class="auth-submit" :loading="loading" @click="handleLogin">进入青衿赋</el-button>
          </el-form-item>
        </el-form>

        <div class="auth-card__switch">
          <span>还没有账号？</span>
          <router-link :to="registerLink" class="auth-card__switch-link">立即注册</router-link>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { House, Lock, User } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { userApi } from '../../api/user'
import { useUserStore } from '../../store/modules/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const JUST_REGISTERED_KEY = 'qingjin-auth-just-registered'

const getSafeRedirectPath = (value: unknown) => {
  if (typeof value !== 'string') return null
  if (!value.startsWith('/')) return null
  if (value.startsWith('//')) return null
  return value
}

const redirectPath = computed(() => getSafeRedirectPath(route.query.redirect))

const registerLink = computed(() => {
  if (!redirectPath.value) return '/register'

  return {
    path: '/register',
    query: {
      redirect: redirectPath.value
    }
  }
})

const statusText = computed(() => {
  if (redirectPath.value) {
    return '登录后将返回你刚刚访问的页面。'
  }

  if (route.query.from === 'register' || sessionStorage.getItem(JUST_REGISTERED_KEY) === '1') {
    return '卷宗已创建，登录后即可继续启程。'
  }

  return '登录后将自动恢复个人信息与学习状态。'
})

const form = ref({
  username: typeof route.query.username === 'string' ? route.query.username : '',
  password: ''
})

const highlights = [
  {
    mark: '学',
    title: '续上学习记录',
    desc: '继续诗词学堂中的收藏、学习进度与复习节奏。'
  },
  {
    mark: '笔',
    title: '回到妙笔挑战',
    desc: '延续每日落笔、答题成长与个人状态，不让体验中断。'
  },
  {
    mark: '作',
    title: '接续创作档案',
    desc: '查看你的作品草稿、发布记录与互动数据，继续下一次表达。'
  }
]

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    const res = await userApi.login(form.value)

    if (!res || !res.access_token) {
      ElMessage.error('登录响应格式错误')
      return
    }

    userStore.setToken(res.access_token)
    await userStore.fetchUserInfo()
    ElMessage.success('登录成功')

    const shouldOnboard = sessionStorage.getItem(JUST_REGISTERED_KEY) === '1' || route.query.from === 'register'

    sessionStorage.removeItem(JUST_REGISTERED_KEY)

    if (redirectPath.value) {
      await router.replace(redirectPath.value)
      return
    }

    if (shouldOnboard) {
      await router.replace({
        path: '/',
        query: {
          onboarding: '1'
        }
      })
      return
    }

    await router.replace('/')
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || error.message || '登录失败'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped src="./styles/auth.css"></style>
