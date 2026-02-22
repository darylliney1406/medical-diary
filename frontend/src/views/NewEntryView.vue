<template>
  <div class="max-w-lg mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <button @click="router.back()" class="p-2 rounded-lg hover:bg-gray-100">
        <ChevronLeft class="w-5 h-5 text-gray-600" />
      </button>
      <h1 class="text-xl font-bold text-gray-900">New Entry</h1>
    </div>

    <!-- Entry type selector -->
    <div class="grid grid-cols-4 gap-2 mb-6">
      <button
        v-for="t in types"
        :key="t.value"
        @click="activeType = t.value"
        class="flex flex-col items-center gap-1.5 py-3 px-1 rounded-xl border-2 text-xs font-semibold transition-all"
        :class="activeType === t.value
          ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
          : 'border-gray-200 text-gray-500 hover:border-gray-300'"
      >
        <span class="text-2xl">{{ t.icon }}</span>
        {{ t.label }}
      </button>
    </div>

    <!-- Form card -->
    <div class="card">
      <component
        :is="activeForm"
        ref="formRef"
        :key="activeType"
      />
    </div>

    <!-- Error -->
    <div v-if="error" class="mt-3 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Actions -->
    <div class="mt-4 flex gap-3">
      <button @click="handleSave" class="btn-primary flex-1" :disabled="saving">
        <span v-if="saving" class="flex items-center justify-center gap-2">
          <Loader2 class="w-4 h-4 animate-spin" /> Saving...
        </span>
        <span v-else>Save entry</span>
      </button>
    </div>

    <!-- Post-save actions -->
    <div v-if="savedOnce" class="mt-3 flex gap-3">
      <button @click="addAnother" class="btn-secondary flex-1 text-sm">Add another</button>
      <button @click="router.push('/dashboard')" class="btn-secondary flex-1 text-sm">Go to dashboard</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, shallowRef } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ChevronLeft, Loader2 } from 'lucide-vue-next'
import { useEntriesStore } from '@/stores/entries'
import { useToast } from '@/composables/useToast'
import BPForm from '@/components/BPForm.vue'
import SymptomForm from '@/components/SymptomForm.vue'
import FoodForm from '@/components/FoodForm.vue'
import GymForm from '@/components/GymForm.vue'

const router = useRouter()
const route = useRoute()
const entries = useEntriesStore()
const { toast } = useToast()

const types = [
  { value: 'bp', label: 'BP', icon: '❤️' },
  { value: 'symptom', label: 'Symptom', icon: '🤒' },
  { value: 'food', label: 'Food', icon: '🍽️' },
  { value: 'gym', label: 'Gym', icon: '💪' },
]

const activeType = ref(route.query.type || 'bp')
const formRef = ref(null)
const saving = ref(false)
const error = ref('')
const savedOnce = ref(false)

const activeForm = computed(() => {
  return { bp: BPForm, symptom: SymptomForm, food: FoodForm, gym: GymForm }[activeType.value]
})

const saveActions = {
  bp: (data) => entries.createBP(data),
  symptom: (data) => entries.createSymptom(data),
  food: (data) => entries.createFood(data),
  gym: (data) => entries.createGym(data),
}

async function handleSave() {
  if (!formRef.value) return
  error.value = ''
  saving.value = true
  try {
    const data = formRef.value.getFormData()
    await saveActions[activeType.value](data)
    toast('Entry saved successfully')
    savedOnce.value = true
    formRef.value.reset()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to save entry. Please try again.'
  } finally {
    saving.value = false
  }
}

function addAnother() {
  savedOnce.value = false
  error.value = ''
  if (formRef.value) formRef.value.reset()
}
</script>
