import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  app.use(router)

  // Silently restore session from HTTP-only refresh cookie before mounting
  const { useAuthStore } = await import('./stores/auth')
  const authStore = useAuthStore()
  try {
    await authStore.refreshToken()
  } catch {
    // No valid session - user will be redirected to login by router guard
  }

  app.mount('#app')
}

bootstrap()
