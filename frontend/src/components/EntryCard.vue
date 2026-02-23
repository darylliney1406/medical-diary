<template>
  <div
    class="card cursor-pointer active:bg-gray-50 transition-colors select-none"
    :class="isUrgent ? 'border-red-300 bg-red-50' : ''"
    @click="emit('view', entry)"
  >
    <div class="flex items-start gap-3">
      <!-- Type icon -->
      <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" :class="iconBg">
        <component :is="typeIcon" class="w-5 h-5" :class="iconColor" />
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-xs font-medium uppercase tracking-wide" :class="iconColor">{{ typeLabel }}</span>
          <span class="text-xs text-gray-400">{{ formattedDate }}</span>
          <span v-if="isUrgent" class="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-red-100 text-red-700 font-medium">Urgent</span>
        </div>

        <!-- BP specific -->
        <template v-if="type === 'bp'">
          <div v-for="(r, i) in entry.readings" :key="i" class="flex items-center gap-2 mt-1">
            <span class="text-lg font-bold text-gray-900">{{ r.systolic }}/{{ r.diastolic }}</span>
            <span class="text-sm text-gray-500">{{ r.pulse }} bpm</span>
            <BPBadge :systolic="r.systolic" :diastolic="r.diastolic" />
          </div>
          <p v-if="entry.notes" class="text-sm text-gray-600 mt-1 line-clamp-2">{{ entry.notes }}</p>
        </template>

        <!-- Symptom specific -->
        <template v-else-if="type === 'symptom'">
          <p class="text-sm text-gray-900 font-medium line-clamp-2">{{ entry.description }}</p>
          <div v-if="entry.severity" class="flex items-center gap-2 mt-1">
            <div class="flex-1 bg-gray-100 rounded-full h-1.5 max-w-24">
              <div class="h-1.5 rounded-full" :class="severityColor" :style="{ width: (entry.severity * 10) + '%' }"></div>
            </div>
            <span class="text-xs text-gray-500">{{ entry.severity }}/10</span>
          </div>
        </template>

        <!-- Food specific -->
        <template v-else-if="type === 'food'">
          <p class="text-sm font-medium text-gray-900">{{ entry.meal_type && mealLabel(entry.meal_type) }} - {{ entry.description }}</p>
          <p v-if="entry.quantity" class="text-xs text-gray-500 mt-0.5">{{ entry.quantity }}</p>
        </template>

        <!-- Gym specific -->
        <template v-else-if="type === 'gym'">
          <p class="text-sm text-gray-900">{{ entry.exercises?.length || 0 }} exercises</p>
          <p v-if="entry.session_notes" class="text-xs text-gray-500 mt-0.5 line-clamp-1">{{ entry.session_notes }}</p>
        </template>

        <!-- Tags -->
        <div v-if="entry.tags?.length" class="flex flex-wrap gap-1 mt-2">
          <span v-for="tag in entry.tags" :key="tag.id || tag" class="tag-chip">{{ tag.name || tag }}</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-1" @click.stop>
        <button @click="emit('edit', entry)" class="p-1.5 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors">
          <Pencil class="w-4 h-4" />
        </button>
        <button @click="emit('delete', entry)" class="p-1.5 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors">
          <Trash2 class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { format, parseISO } from 'date-fns'
import { Activity, Pill, UtensilsCrossed, Dumbbell, Pencil, Trash2 } from 'lucide-vue-next'
import BPBadge from './BPBadge.vue'

const props = defineProps({
  entry: { type: Object, required: true },
  type: { type: String, required: true }, // 'bp' | 'symptom' | 'food' | 'gym'
})

const emit = defineEmits(['edit', 'delete', 'view'])

const typeConfig = {
  bp: { label: 'Blood Pressure', icon: Activity, bg: 'bg-blue-100', color: 'text-blue-600' },
  symptom: { label: 'Symptom', icon: Pill, bg: 'bg-orange-100', color: 'text-orange-600' },
  food: { label: 'Food', icon: UtensilsCrossed, bg: 'bg-green-100', color: 'text-green-600' },
  gym: { label: 'Gym', icon: Dumbbell, bg: 'bg-purple-100', color: 'text-purple-600' },
}

const config = computed(() => typeConfig[props.type] || typeConfig.bp)
const typeLabel = computed(() => config.value.label)
const typeIcon = computed(() => config.value.icon)
const iconBg = computed(() => config.value.bg)
const iconColor = computed(() => config.value.color)

const formattedDate = computed(() => {
  try {
    return format(parseISO(props.entry.entry_date), 'dd MMM')
  } catch {
    return props.entry.entry_date || ''
  }
})

const isUrgent = computed(() => props.entry.tags?.some(t => (t.name || t) === 'urgent'))

const severityColor = computed(() => {
  const s = props.entry.severity || 0
  if (s <= 3) return 'bg-green-400'
  if (s <= 6) return 'bg-yellow-400'
  return 'bg-red-500'
})

function mealLabel(type) {
  return { breakfast: 'Breakfast', lunch: 'Lunch', dinner: 'Dinner', snack: 'Snack', drink: 'Drink' }[type] || type
}
</script>
