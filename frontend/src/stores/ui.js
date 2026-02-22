import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * UI store - manages global UI state (toasts, modals, install prompt).
 */
export const useUiStore = defineStore('ui', () => {
  /** @type {import('vue').Ref<Array<{id:number,message:string,type:string}>>} */
  const toasts = ref([])
  let nextId = 0

  const pwaPrompt = ref(null)
  const sidebarOpen = ref(false)

  /**
   * Show a toast notification.
   * @param {string} message
   * @param {'success'|'error'|'info'|'warning'} type
   * @param {number} duration - milliseconds before auto-dismiss
   */
  function showToast(message, type = 'success', duration = 3500) {
    const id = nextId++
    toasts.value.push({ id, message, type })
    setTimeout(() => dismissToast(id), duration)
  }

  function dismissToast(id) {
    toasts.value = toasts.value.filter(t => t.id \!== id)
  }

  function setPwaPrompt(event) {
    pwaPrompt.value = event
  }

  async function installPwa() {
    if (\!pwaPrompt.value) return
    pwaPrompt.value.prompt()
    await pwaPrompt.value.userChoice
    pwaPrompt.value = null
  }

  return { toasts, pwaPrompt, sidebarOpen, showToast, dismissToast, setPwaPrompt, installPwa }
})
