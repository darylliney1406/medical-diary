<template>
  <div class="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex items-center justify-center p-4">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4">
          <HeartPulse class="w-8 h-8 text-white" />
        </div>
        <h1 class="text-2xl font-bold text-gray-900">MediDiary</h1>
        <p class="text-gray-500 mt-1">Your personal health companion</p>
      </div>

      <div class="card">
        <!-- Login form -->
        <form v-if="!mfaStep" @submit.prevent="handleLogin" class="space-y-4">
          <h2 class="text-lg font-semibold text-gray-900">Sign in</h2>

          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            {{ error }}
          </div>

          <div>
            <label class="label">Email address</label>
            <input
              v-model="email"
              type="email"
              autocomplete="email"
              required
              class="input-field"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label class="label">Password</label>
            <div class="relative">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
                class="input-field pr-10"
                placeholder="Enter your password"
              />
              <button type="button" @click="showPassword = !showPassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                <component :is="showPassword ? EyeOff : Eye" class="w-4 h-4" />
              </button>
            </div>
          </div>

          <button type="submit" class="btn-primary w-full" :disabled="auth.loading">
            <span v-if="auth.loading" class="flex items-center justify-center gap-2">
              <Loader2 class="w-4 h-4 animate-spin" /> Signing in...
            </span>
            <span v-else>Sign in</span>
          </button>
        </form>

        <!-- MFA form -->
        <form v-else @submit.prevent="handleMfa" class="space-y-4">
          <div class="text-center mb-2">
            <ShieldCheck class="w-12 h-12 text-indigo-600 mx-auto mb-2" />
            <h2 class="text-lg font-semibold text-gray-900">Two-factor authentication</h2>
            <p class="text-sm text-gray-500 mt-1">Enter the 6-digit code from your authenticator app</p>
          </div>

          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            {{ error }}
          </div>

          <div>
            <label class="label">Authentication code</label>
            <input
              v-model="mfaCode"
              type="text"
              inputmode="numeric"
              pattern="[0-9]{6}"
              maxlength="6"
              required
              class="input-field text-center text-2xl tracking-widest"
              placeholder="000000"
              autofocus
            />
          </div>

          <button type="submit" class="btn-primary w-full" :disabled="auth.loading">
            <span v-if="auth.loading" class="flex items-center justify-center gap-2">
              <Loader2 class="w-4 h-4 animate-spin" /> Verifying...
            </span>
            <span v-else>Verify</span>
          </button>

          <button type="button" @click="mfaStep = false" class="btn-secondary w-full">
            Back to login
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { HeartPulse, Eye, EyeOff, Loader2, ShieldCheck } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const mfaCode = ref('')
const mfaStep = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  try {
    const loggedIn = await auth.login(email.value, password.value)
    if (loggedIn) {
      router.push('/dashboard')
    } else {
      mfaStep.value = true
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Invalid email or password'
  }
}

async function handleMfa() {
  error.value = ''
  try {
    await auth.validateMfa(mfaCode.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Invalid code. Please try again.'
    mfaCode.value = ''
  }
}
</script>
