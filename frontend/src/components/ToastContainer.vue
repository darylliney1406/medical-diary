<template>
  <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
    <TransitionGroup name="toast">
      <div
        v-for="toast in ui.toasts"
        :key="toast.id"
        class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg min-w-64 max-w-sm"
        :class="toastClass(toast.type)"
      >
        <component :is="toastIcon(toast.type)" class="w-5 h-5 flex-shrink-0" />
        <span class="text-sm font-medium flex-1">{{ toast.message }}</span>
        <button @click="ui.dismissToast(toast.id)" class="ml-2 opacity-70 hover:opacity-100">
          <X class="w-4 h-4" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useUiStore } from '@/stores/ui'
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from 'lucide-vue-next'

const ui = useUiStore()

function toastClass(type) {
  return {
    success: 'bg-green-600 text-white',
    error: 'bg-red-600 text-white',
    warning: 'bg-yellow-500 text-white',
    info: 'bg-indigo-600 text-white',
  }[type] || 'bg-gray-800 text-white'
}

function toastIcon(type) {
  return { success: CheckCircle, error: AlertCircle, warning: AlertTriangle, info: Info }[type] || Info
}
</script>

<style scoped>
.toast-enter-active { transition: all 0.3s ease; }
.toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from { opacity: 0; transform: translateX(100%); }
.toast-leave-to { opacity: 0; transform: translateX(100%); }
</style>
