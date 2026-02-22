import { useUiStore } from '@/stores/ui'
export function useToast() {
  const ui = useUiStore()
  function toast(msg, type, dur) { ui.showToast(msg, type||'success', dur||3500) }
  return { toast }
}
