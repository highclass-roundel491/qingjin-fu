import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/modules/user'

interface RequestInstance extends AxiosInstance {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
}

const resolveDefaultApiBaseUrl = () => {
  if (typeof window === 'undefined') return 'http://localhost:8000/api/v1'
  const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
  return `${protocol}//${window.location.hostname}:8000/api/v1`
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || resolveDefaultApiBaseUrl()

const request = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
}) as RequestInstance

const AI_ENDPOINTS = [
  '/challenges/ai-check',
  '/challenges/ai-generate',
  '/challenges/ai-hint',
  '/ai/',
  '/feihualing/start',
  '/feihualing/submit'
]

const isAIRequest = (url?: string) => {
  if (!url) return false
  return AI_ENDPOINTS.some(endpoint => url.includes(endpoint))
}

const AUTH_API_PATHS = ['/users/login', '/users/register']
const AUTH_PAGE_PATHS = new Set(['/login', '/register'])

const isAuthRequest = (url?: string) => {
  if (!url) return false
  return AUTH_API_PATHS.some(path => url.includes(path))
}

const isAuthPage = () => AUTH_PAGE_PATHS.has(window.location.pathname)

const getLoginRedirectUrl = () => {
  const redirectPath = `${window.location.pathname}${window.location.search}`
  return `/login?redirect=${encodeURIComponent(redirectPath)}`
}

request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    if (isAIRequest(config.url)) {
      config.timeout = 60000
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const status = error.response?.status
    const detail = typeof error.response?.data?.detail === 'string' ? error.response.data.detail : undefined
    const requestUrl = error.config?.url as string | undefined

    if (isAuthRequest(requestUrl)) {
      return Promise.reject(error)
    }

    if (status === 401 || status === 403) {
      const userStore = useUserStore()
      userStore.logout()

      if (!isAuthPage()) {
        window.location.href = getLoginRedirectUrl()
      }

      return Promise.reject(error)
    }

    if (status === 422) {
      ElMessage.error(detail || '请求参数错误')
      return Promise.reject(error)
    }

    ElMessage.error(detail || error.message || '网络错误')
    return Promise.reject(error)
  }
)

export default request
