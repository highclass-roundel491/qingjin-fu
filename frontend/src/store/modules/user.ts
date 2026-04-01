import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userApi, type UserInfo } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const userInfo = ref<UserInfo | null>(null)
  const isLogin = ref<boolean>(!!token.value)
  const authReady = ref<boolean>(!token.value)
  const authLoading = ref<boolean>(!!token.value)

  const setToken = (newToken: string) => {
    token.value = newToken
    userInfo.value = null
    localStorage.setItem('token', newToken)
    isLogin.value = true
    authReady.value = false
    authLoading.value = true
  }

  const setUserInfo = (info: UserInfo | null) => {
    userInfo.value = info

    if (info) {
      isLogin.value = true
      authReady.value = true
    }
  }

  const fetchUserInfo = async () => {
    if (!token.value) {
      userInfo.value = null
      isLogin.value = false
      authReady.value = true
      authLoading.value = false
      return null
    }

    authLoading.value = true

    try {
      const info = await userApi.getCurrentUser()
      setUserInfo(info)
      return info
    } catch (error) {
      console.error('获取用户信息失败:', error)
      return null
    } finally {
      authLoading.value = false
      authReady.value = true
    }
  }

  const initializeAuth = async () => {
    if (!token.value) {
      userInfo.value = null
      isLogin.value = false
      authReady.value = true
      authLoading.value = false
      return
    }

    if (authReady.value && userInfo.value) {
      return
    }

    await fetchUserInfo()
  }

  const logout = () => {
    token.value = null
    userInfo.value = null
    isLogin.value = false
    authReady.value = true
    authLoading.value = false
    localStorage.removeItem('token')
  }

  return {
    token,
    userInfo,
    isLogin,
    authReady,
    authLoading,
    setToken,
    setUserInfo,
    fetchUserInfo,
    initializeAuth,
    logout
  }
})
