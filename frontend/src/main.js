import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)

  // Restore session BEFORE installing router so the navigation guard
  // sees the correct auth state on the very first route resolution.
  const { useAuthStore } = await import('./stores/auth')
  const authStore = useAuthStore()
  try {
    await authStore.refreshToken()
  } catch {
    // No valid session - router guard will redirect to /login
  }

  app.use(router)
  app.mount('#app')
}

bootstrap()
