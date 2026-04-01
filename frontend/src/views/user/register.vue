<template>
  <div class="auth-page auth-page--register">
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
        <router-link :to="loginLink" class="auth-topbar__link auth-topbar__link--accent">
          <span>已有账号</span>
        </router-link>
      </div>
    </header>

    <main class="auth-shell auth-shell--register">
      <section class="auth-hero">
        <div class="auth-hero__seal">启</div>

        <div class="auth-hero__content">
          <p class="auth-hero__eyebrow">新卷启封</p>
          <h1 class="auth-hero__title">开启你的青衿卷宗</h1>
          <p class="auth-hero__description">
            注册后即可记录学习、承接创作并持续积累成长身份。
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
          <p class="auth-card__eyebrow">创建账号</p>
          <h2 class="auth-card__title">注册新账号</h2>
          <p class="auth-card__subtitle">填写基础信息后，即可开启你的诗学卷宗。</p>
        </div>

        <div class="auth-card__status">
          <span class="auth-card__status-dot"></span>
          <span>完成落印后将自动进入你的诗学卷宗。</span>
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
              placeholder="用于登录与展示的用户名"
              autocomplete="username"
              clearable
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="form.email"
              placeholder="请输入常用邮箱"
              autocomplete="email"
              clearable
              :prefix-icon="Message"
            />
          </el-form-item>

          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="form.phone"
              placeholder="手机号可选，用于后续扩展能力"
              autocomplete="tel"
              clearable
              :prefix-icon="Phone"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              autocomplete="new-password"
              show-password
              :prefix-icon="Lock"
            />
          </el-form-item>

          <div class="auth-strength">
            <div class="auth-strength__bars">
              <span
                v-for="index in 3"
                :key="index"
                class="auth-strength__bar"
                :class="{ 'is-active': index <= passwordStrengthScore }"
              ></span>
            </div>
            <span class="auth-strength__label">{{ passwordStrengthLabel }}</span>
          </div>
          <p class="auth-strength__hint">建议使用 6 位以上密码，并组合字母、数字或符号提升安全性。</p>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              autocomplete="new-password"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="handleRegister"
            />
          </el-form-item>

          <el-form-item>
            <el-button class="auth-submit" :loading="loading" @click="handleRegister">落印入卷</el-button>
          </el-form-item>
        </el-form>

        <div class="auth-card__switch">
          <span>已经有账号了？</span>
          <router-link :to="loginLink" class="auth-card__switch-link">立即登录</router-link>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { House, Lock, Message, Phone, User } from '@element-plus/icons-vue'
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

const loginLink = computed(() => {
  if (!redirectPath.value) return '/login'

  return {
    path: '/login',
    query: {
      redirect: redirectPath.value
    }
  }
})

const form = ref({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const highlights = [
  {
    mark: '学',
    title: '建立学习档案',
    desc: '从第一天开始记录诗词浏览、收藏与个人学习进度。'
  },
  {
    mark: '笔',
    title: '承接妙笔与创作',
    desc: '后续每日挑战、续写记录与作品创作都会统一归档。'
  },
  {
    mark: '成',
    title: '沉淀成长身份',
    desc: '等级、成就与互动数据都会围绕你的账号持续积累。'
  }
]

const passwordStrengthScore = computed(() => {
  const password = form.value.password.trim()

  if (!password) return 0

  let score = 0

  if (password.length >= 6) score += 1
  if (/[A-Za-z]/.test(password) && /\d/.test(password)) score += 1
  if (/[^A-Za-z\d]/.test(password) || password.length >= 10) score += 1

  return Math.min(score, 3)
})

const passwordStrengthLabel = computed(() => {
  if (passwordStrengthScore.value === 0) return '待填写'
  if (passwordStrengthScore.value === 1) return '基础'
  if (passwordStrengthScore.value === 2) return '稳妥'
  return '较强'
})

const validateConfirmPassword = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (!value) {
    callback(new Error('请确认密码'))
    return
  }

  if (value !== form.value.password) {
    callback(new Error('两次密码不一致'))
    return
  }

  callback()
}

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }]
}

const handleRegister = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true

  try {
    await userApi.register({
      username: form.value.username,
      email: form.value.email,
      password: form.value.password,
      phone: form.value.phone || undefined
    })

    sessionStorage.setItem(JUST_REGISTERED_KEY, '1')

    try {
      const loginRes = await userApi.login({
        username: form.value.username,
        password: form.value.password
      })

      if (!loginRes || !loginRes.access_token) {
        throw new Error('自动登录失败')
      }

      userStore.setToken(loginRes.access_token)
      await userStore.fetchUserInfo()
      sessionStorage.removeItem(JUST_REGISTERED_KEY)
      ElMessage.success('注册成功，已进入卷宗')

      if (redirectPath.value) {
        await router.replace(redirectPath.value)
        return
      }

      await router.replace({
        path: '/',
        query: {
          onboarding: '1'
        }
      })
      return
    } catch {
      ElMessage.success('注册成功，请登录继续')
      await router.replace({
        path: '/login',
        query: {
          username: form.value.username,
          from: 'register',
          ...(redirectPath.value ? { redirect: redirectPath.value } : {})
        }
      })
      return
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || error.message || '注册失败'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped src="./styles/auth.css"></style>
