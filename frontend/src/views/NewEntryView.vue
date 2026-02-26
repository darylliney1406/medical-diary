<template>
  <div class="max-w-lg mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <h1 class="text-xl font-bold text-gray-900">{{ activeType ? typeMeta[activeType].label : 'New Entry' }}</h1>
    </div>

    <!-- Type selection screen (no type chosen yet) -->
    <div v-if="!activeType" class="grid grid-cols-2 gap-3">
      <button
        v-for="t in types"
        :key="t.value"
        @click="router.push('/new-entry?type=' + t.value)"
        class="flex flex-col items-start gap-2 p-5 rounded-2xl border-2 border-gray-200 hover:border-indigo-400 hover:bg-indigo-50 text-left transition-all"
      >
        <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="t.iconBg">
          <component :is="t.icon" class="w-5 h-5" :class="t.iconColor" />
        </div>
        <div>
          <p class="font-semibold text-gray-900 text-sm">{{ t.label }}</p>
          <p class="text-xs text-gray-500 mt-0.5 leading-relaxed">{{ t.description }}</p>
        </div>
      </button>
    </div>

    <!-- Form (type has been chosen) -->
    <template v-else>
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
    </template>
  </div>
</template>

<script setup>
import { ref, computed, shallowRef } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Loader2, Heart, Thermometer, Utensils, Dumbbell } from 'lucide-vue-next'
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
  {
    value: 'bp',
    label: 'Blood Pressure',
    icon: Heart,
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    description: 'Record systolic, diastolic and pulse readings',
  },
  {
    value: 'symptom',
    label: 'Symptom',
    icon: Thermometer,
    iconBg: 'bg-orange-100',
    iconColor: 'text-orange-600',
    description: 'Log a symptom and rate its severity out of 10',
  },
  {
    value: 'food',
    label: 'Food & Drink',
    icon: Utensils,
    iconBg: 'bg-green-100',
    iconColor: 'text-green-600',
    description: 'Track meals and drinks throughout the day',
  },
  {
    value: 'gym',
    label: 'Gym / Exercise',
    icon: Dumbbell,
    iconBg: 'bg-purple-100',
    iconColor: 'text-purple-600',
    description: 'Record a workout session with exercises and sets',
  },
]

const typeMeta = Object.fromEntries(types.map(t => [t.value, t]))

const activeType = computed(() => route.query.type || null)
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
