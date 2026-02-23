<template>
  <!-- Mobile bottom nav -->
  <nav class="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 md:hidden" style="padding-bottom: env(safe-area-inset-bottom)">
    <div class="flex items-center justify-around h-16">
      <NavItem v-for="item in mainNavItems" :key="item.to" :item="item" />
      <button @click="toggleMore" class="flex flex-col items-center gap-0.5 px-3 py-2 text-gray-500">
        <component :is="MoreHorizontal" class="w-6 h-6" />
        <span class="text-xs">More</span>
      </button>
    </div>
  </nav>

  <!-- More menu (mobile) -->
  <Teleport to="body">
    <div v-if="moreOpen" class="fixed inset-0 z-50 md:hidden" @click.self="moreOpen = false">
      <div class="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-xl p-4" style="padding-bottom: calc(env(safe-area-inset-bottom) + 1rem)">
        <div class="w-10 h-1 bg-gray-300 rounded mx-auto mb-4"></div>
        <div class="grid grid-cols-3 gap-3 mb-4">
          <NavItemLarge :item="{ to: '/profile', icon: User, label: 'Profile' }" @click="moreOpen = false" />
          <NavItemLarge v-if="auth.isAdmin" :item="{ to: '/admin', icon: Shield, label: 'Admin' }" @click="moreOpen = false" />
          <button @click="handleLogout" class="flex flex-col items-center gap-2 p-3 rounded-xl bg-red-50 text-red-600">
            <LogOut class="w-6 h-6" />
            <span class="text-xs font-medium">Logout</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Desktop sidebar -->
  <aside class="hidden md:flex flex-col fixed left-0 top-0 bottom-0 w-64 bg-white border-r border-gray-200 z-40">
    <div class="flex items-center gap-3 p-6 border-b border-gray-100">
      <div class="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center">
        <HeartPulse class="w-5 h-5 text-white" />
      </div>
      <span class="text-xl font-bold text-gray-900">MediDiary</span>
    </div>

    <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
      <RouterLink
        v-for="item in allNavItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
        :class="isActive(item.to) ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
        {{ item.label }}
      </RouterLink>
    </nav>

    <div class="p-4 border-t border-gray-100">
      <div class="flex items-center gap-3 mb-3">
        <div class="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center">
          <span class="text-sm font-medium text-indigo-700">{{ userInitials }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900 truncate">{{ auth.user?.name || 'User' }}</p>
          <p class="text-xs text-gray-500 truncate">{{ auth.user?.email }}</p>
        </div>
      </div>
      <button @click="handleLogout" class="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors">
        <LogOut class="w-4 h-4" />
        Sign out
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NavItem from "@/components/NavItem.vue"
import NavItemLarge from "@/components/NavItemLarge.vue"
import {
  LayoutDashboard, Plus, Calendar, BookOpen, BarChart2,
  User, Shield, LogOut, MoreHorizontal, HeartPulse
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const moreOpen = ref(false)

const mainNavItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
  { to: '/new-entry', icon: Plus, label: 'Add' },
  { to: '/calendar', icon: Calendar, label: 'Calendar' },
  { to: '/daily-log', icon: BookOpen, label: 'Log' },
  { to: '/weekly-summary', icon: BarChart2, label: 'Summary' },
]

const allNavItems = computed(() => {
  const items = [...mainNavItems]
  items.push({ to: '/profile', icon: User, label: 'Profile' })
  if (auth.isAdmin) items.push({ to: '/admin', icon: Shield, label: 'Admin' })
  return items
})

const userInitials = computed(() => {
  const name = auth.user?.name || ''
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '?'
})

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function toggleMore() {
  moreOpen.value = !moreOpen.value
}

async function handleLogout() {
  moreOpen.value = false
  await auth.logout()
}
</script>

<script>
// Sub-components defined inline
</script>
