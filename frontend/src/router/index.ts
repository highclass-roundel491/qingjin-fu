import { createRouter, createWebHistory } from 'vue-router'
import pinia from '../store'
import { useUserStore } from '../store/modules/user'

const AUTH_PAGE_PATHS = new Set(['/login', '/register'])

const getSafeRedirectPath = (value: unknown) => {
  if (typeof value !== 'string') return null
  if (!value.startsWith('/')) return null
  if (value.startsWith('//')) return null
  return value
}

const isAuthPagePath = (path: string) => AUTH_PAGE_PATHS.has(path)

const isAuthRedirectPath = (path: string) => {
  const normalizedPath = path.split('?')[0] ?? ''
  return AUTH_PAGE_PATHS.has(normalizedPath)
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/home/index.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/user/login.vue')
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/user/register.vue')
    },
    {
      path: '/challenge',
      name: 'challenge',
      component: () => import('../views/challenge/index.vue')
    },
    {
      path: '/challenge/rankings',
      name: 'challenge-rankings',
      component: () => import('../views/challenge/rankings.vue')
    },
    {
      path: '/games',
      name: 'games',
      component: () => import('../views/games/index.vue')
    },
    {
      path: '/games/feihualing',
      name: 'feihualing',
      component: () => import('../views/game/index.vue')
    },
    {
      path: '/feihualing',
      redirect: '/games/feihualing'
    },
    {
      path: '/poems',
      name: 'poems',
      component: () => import('../views/poems/index.vue')
    },
    {
      path: '/poems/:id',
      name: 'poem-detail',
      component: () => import('../views/poems/detail.vue')
    },
    {
      path: '/works',
      name: 'works',
      component: () => import('../views/works/index.vue')
    },
    {
      path: '/works/create',
      name: 'works-create',
      component: () => import('../views/works/create.vue')
    },
    {
      path: '/works/drafts',
      name: 'works-drafts',
      component: () => import('../views/works/drafts.vue')
    },
    {
      path: '/works/rankings',
      name: 'works-rankings',
      component: () => import('../views/works/rankings.vue')
    },
    {
      path: '/works/:id',
      name: 'works-detail',
      component: () => import('../views/works/detail.vue')
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/profile/index.vue')
    },
    {
      path: '/profile/folio',
      name: 'profile-folio',
      component: () => import('../views/profile/folio.vue')
    },
    {
      path: '/relay',
      name: 'relay',
      component: () => import('../views/relay/index.vue')
    },
    {
      path: '/relay/history',
      name: 'relay-history',
      component: () => import('../views/relay/history.vue')
    },
    {
      path: '/relay/rankings',
      name: 'relay-rankings',
      component: () => import('../views/relay/rankings.vue')
    },
    {
      path: '/social/feed',
      name: 'social-feed',
      component: () => import('../views/social/feed.vue')
    },
    {
      path: '/user/:id',
      name: 'user-profile',
      component: () => import('../views/social/user-profile.vue')
    },
    {
      path: '/achievements',
      name: 'achievements',
      component: () => import('../views/social/achievements.vue')
    },
    {
      path: '/games/timed',
      name: 'timed-challenge',
      component: () => import('../views/timed/index.vue')
    },
    {
      path: '/games/timed/history',
      name: 'timed-history',
      component: () => import('../views/timed/history.vue')
    },
    {
      path: '/games/timed/rankings',
      name: 'timed-rankings',
      component: () => import('../views/timed/rankings.vue')
    },
    {
      path: '/social/following',
      name: 'social-following',
      component: () => import('../views/social/connections.vue')
    },
    {
      path: '/social/followers',
      name: 'social-followers',
      component: () => import('../views/social/connections.vue')
    },
    {
      path: '/graph',
      name: 'graph',
      component: () => import('../views/graph/index.vue')
    }
  ]
})

router.beforeEach((to) => {
  const userStore = useUserStore(pinia)
  const hasSession = Boolean(userStore.token)

  if (hasSession && isAuthPagePath(to.path)) {
    const redirectPath = getSafeRedirectPath(to.query.redirect)

    if (redirectPath && !isAuthRedirectPath(redirectPath)) {
      return redirectPath
    }

    return '/'
  }

  return true
})

export default router
