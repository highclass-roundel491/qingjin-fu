const resolveDefaultApiBaseUrl = () => {
  if (typeof window === 'undefined') return 'http://localhost:8000/api/v1'
  const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
  return `${protocol}//${window.location.hostname}:8000/api/v1`
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL || resolveDefaultApiBaseUrl()).replace(/\/api\/v1$/, '')

export function resolveUploadUrl(path: string | null | undefined): string | null {
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  if (path.startsWith('/uploads/')) return `${API_BASE}${path}`
  return path
}
