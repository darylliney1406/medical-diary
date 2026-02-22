<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <div class="flex items-center justify-between mb-5">
      <h1 class="text-xl font-bold text-gray-900">Admin Panel</h1>
      <button @click="showCreateForm = true" class="btn-primary">+ Create User</button>
    </div>

    <!-- Create User Modal -->
    <div v-if="showCreateForm" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="w-full max-w-md bg-white rounded-2xl shadow-xl p-6">
        <h2 class="text-lg font-semibold mb-4">Create New User</h2>
        <form @submit.prevent="createUser" class="space-y-3">
          <div><label class="label">Full name</label><input v-model="newUser.name" type="text" class="input-field" required /></div>
          <div><label class="label">Email</label><input v-model="newUser.email" type="email" class="input-field" required /></div>
          <div>
            <label class="label">Role</label>
            <select v-model="newUser.role" class="input-field">
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div v-if="createError" class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{{ createError }}</div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showCreateForm = false" class="btn-secondary flex-1">Cancel</button>
            <button type="submit" class="btn-primary flex-1" :disabled="creating">
              <Loader2 v-if="creating" class="w-4 h-4 animate-spin inline mr-1" />Create
            </button>
          </div>
        </form>
        <div v-if="createdReset" class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p class="text-xs text-blue-600 font-medium mb-1">Password reset link:</p>
          <code class="text-xs text-blue-800 break-all">{{ createdReset }}</code>
        </div>
      </div>
    </div>

    <!-- User table -->
    <div class="card overflow-hidden p-0">
      <div v-if="loading" class="p-8 text-center text-gray-400">
        <Loader2 class="w-6 h-6 animate-spin mx-auto mb-2" /> Loading users...
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-100">
            <tr>
              <th class="text-left px-4 py-3 font-medium text-gray-500">Name</th>
              <th class="text-left px-4 py-3 font-medium text-gray-500">Email</th>
              <th class="text-left px-4 py-3 font-medium text-gray-500">Role</th>
              <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
              <th class="text-left px-4 py-3 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 font-medium text-gray-900">{{ user.name }}</td>
              <td class="px-4 py-3 text-gray-600">{{ user.email }}</td>
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="user.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'">{{ user.role }}</span>
              </td>
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'">
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <button
                    @click="toggleUserStatus(user)"
                    class="text-xs font-medium px-2 py-1 rounded-lg transition-colors"
                    :class="user.is_active ? 'bg-red-50 text-red-600 hover:bg-red-100' : 'bg-green-50 text-green-600 hover:bg-green-100'"
                  >
                    {{ user.is_active ? 'Deactivate' : 'Activate' }}
                  </button>
                  <button @click="requestReset(user)" class="text-xs font-medium px-2 py-1 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100">
                    Reset password
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!users.length" class="text-center text-gray-400 py-8 text-sm">No users found.</p>
      </div>
    </div>

    <!-- Reset token display -->
    <div v-if="resetToken" class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl">
      <div class="flex items-center justify-between mb-2">
        <p class="text-sm font-medium text-blue-800">Password reset token generated</p>
        <button @click="resetToken = null" class="text-blue-400 hover:text-blue-600"><X class="w-4 h-4" /></button>
      </div>
      <code class="text-xs text-blue-700 break-all block">{{ resetToken }}</code>
      <p class="text-xs text-blue-500 mt-1">Copy and send this token to the user.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Loader2, X } from 'lucide-vue-next'
import { usersApi } from '@/api'
import { useToast } from '@/composables/useToast'

const { toast } = useToast()
const loading = ref(false)
const users = ref([])
const showCreateForm = ref(false)
const creating = ref(false)
const createError = ref('')
const createdReset = ref(null)
const resetToken = ref(null)
const newUser = ref({ name: '', email: '', role: 'user' })

onMounted(fetchUsers)

async function fetchUsers() {
  loading.value = true
  try {
    const { data } = await usersApi.list()
    users.value = data.items || data
  } finally { loading.value = false }
}

async function createUser() {
  creating.value = true
  createError.value = ''
  createdReset.value = null
  try {
    const { data } = await usersApi.create(newUser.value)
    users.value.push(data.user || data)
    if (data.reset_token) createdReset.value = data.reset_token
    toast('User created successfully')
    newUser.value = { name: '', email: '', role: 'user' }
  } catch (e) {
    createError.value = e.response?.data?.detail || 'Failed to create user'
  } finally { creating.value = false }
}

async function toggleUserStatus(user) {
  try {
    if (user.is_active) {
      await usersApi.deactivate(user.id)
      user.is_active = false
      toast('User deactivated')
    } else {
      await usersApi.activate(user.id)
      user.is_active = true
      toast('User activated')
    }
  } catch { toast('Failed to update status', 'error') }
}

async function requestReset(user) {
  try {
    const { data } = await usersApi.requestPasswordReset(user.id)
    resetToken.value = data.reset_token || data.token || 'Check server logs'
    toast('Reset token generated')
  } catch { toast('Failed to generate reset token', 'error') }
}
</script>
