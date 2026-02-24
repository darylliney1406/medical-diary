import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/new-entry',
    name: 'new-entry',
    component: () => import('@/views/NewEntryView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/calendar',
    name: 'calendar',
    component: () => import('@/views/CalendarView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/daily-log',
    name: 'daily-log',
    component: () => import('@/views/DailyLogView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/weekly-summary',
    name: 'weekly-summary',
    component: () => import('@/views/WeeklySummaryView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next('/login')
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return next('/dashboard')
  }

  if (to.meta.public && auth.isAuthenticated) {
    return next('/dashboard')
  }

  next()
})

// When a lazy-loaded route chunk fails to fetch (stale service worker cache
// after a redeploy), force a full page reload to the target route so the
// browser picks up the latest index.html and correct chunk hashes.
router.onError((error, to) => {
  const isChunkError =
    error?.message?.includes('Failed to fetch dynamically imported module') ||
    error?.message?.includes('Importing a module script failed') ||
    error?.message?.includes('Unable to preload CSS')
  if (isChunkError) {
    window.location.assign(to.fullPath)
  }
})

export default router
