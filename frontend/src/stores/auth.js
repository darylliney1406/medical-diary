import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, configureApi } from '@/api'
import router from '@/router'

/**
 * Auth store - manages authentication state.
 * Access token is kept in memory only (not localStorage).
 * Session persistence relies on HTTP-only refresh cookie.
 */
export const useAuthStore = defineStore('auth', () => {
  /** @type {import('vue').Ref<string|null>} */
  const accessToken = ref(null)

  /** @type {import('vue').Ref<Object|null>} */
  const user = ref(null)

  const loading = ref(false)

  /** @type {import('vue').Ref<{mfaToken: string}|null>} */
  const mfaPending = ref(null)

  const isAuthenticated = computed(() => accessToken.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // Configure API interceptors with store accessors
  configureApi({
    getToken: () => accessToken.value,
    onUnauthorized: () => {
      accessToken.value = null
      user.value = null
      router.push('/login')
    },
  })

  /**
   * Attempt login with email/password.
   * Returns true if logged in, false if MFA required.
   * @param {string} email
   * @param {string} password
   * @returns {Promise<boolean>}
   */
  async function login(email, password) {
    loading.value = true
    try {
      const { data } = await authApi.login(email, password)
      if (data.mfa_required) {
        mfaPending.value = { mfaToken: data.mfa_token }
        return false
      }
      accessToken.value = data.access_token
      user.value = data.user
      return true
    } finally {
      loading.value = false
    }
  }

  /**
   * Validate MFA TOTP code.
   * @param {string} code
   */
  async function validateMfa(code) {
    if (!mfaPending.value) throw new Error('No MFA pending')
    loading.value = true
    try {
      const { data } = await authApi.validateMfa(mfaPending.value.mfaToken, code)
      accessToken.value = data.access_token
      user.value = data.user
      mfaPending.value = null
    } finally {
      loading.value = false
    }
  }

  /**
   * Silently refresh access token using HTTP-only cookie.
   * Called on app startup and by axios interceptor on 401.
   */
  async function refreshToken() {
    const { data } = await authApi.refresh()
    accessToken.value = data.access_token
    if (data.user) user.value = data.user
  }

  /**
   * Logout: clear state and call server logout endpoint.
   */
  async function logout() {
    try {
      await authApi.logout()
    } catch { /* ignore */ }
    accessToken.value = null
    user.value = null
    mfaPending.value = null
    router.push('/login')
  }

  return {
    accessToken, user, loading, mfaPending,
    isAuthenticated, isAdmin,
    login, validateMfa, refreshToken, logout,
  }
})
