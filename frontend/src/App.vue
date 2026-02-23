<template>
  <div class="min-h-screen bg-gray-50">
    <AppNav v-if="showNav" />
    <main :class="showNav ? 'pb-20 md:pl-64' : ''" class="min-h-screen">
      <RouterView v-slot="{ Component }">
        <Transition name="fade" mode="out-in">
          <component :is="Component" :key="route.fullPath" />
        </Transition>
      </RouterView>
    </main>
    <ToastContainer />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import AppNav from '@/components/AppNav.vue'
import ToastContainer from '@/components/ToastContainer.vue'

const route = useRoute()
const auth = useAuthStore()
const ui = useUiStore()

const showNav = computed(() => auth.isAuthenticated && route.name !== 'login')

onMounted(() => {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    ui.setPwaPrompt(e)
  })
})
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
