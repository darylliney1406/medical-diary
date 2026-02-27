<template>
  <div class="space-y-4">
    <!-- Date and Time -->
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="label">Date <span class="text-red-500">*</span></label>
        <input v-model="form.entry_date" type="date" class="input-field" :max="today" required />
      </div>
      <div>
        <label class="label">Time <span class="text-red-500">*</span></label>
        <input v-model="form.entry_time" type="time" class="input-field" required />
      </div>
    </div>

    <!-- Description -->
    <div>
      <label class="label">Description <span class="text-red-500">*</span></label>
      <textarea
        v-model="form.description"
        class="input-field"
        rows="4"
        placeholder="Describe how you are feeling in detail..."
        required
      ></textarea>
    </div>

    <!-- Severity -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <label class="label mb-0">Severity <span class="text-red-500">*</span></label>
        <span class="text-sm font-medium" :class="severityColor">{{ severityLabel }}</span>
      </div>
      <div class="relative pt-1">
        <input
          v-model.number="form.severity"
          type="range"
          min="1"
          max="10"
          class="w-full h-2 rounded-full appearance-none cursor-pointer bg-gradient-to-r from-green-300 via-yellow-300 to-red-400"
        />
        <div class="flex justify-between text-xs text-gray-400 mt-1">
          <span>Mild</span>
          <span>Moderate</span>
          <span>Severe</span>
        </div>
      </div>
      <div class="flex justify-between mt-1">
        <Smile class="w-5 h-5 text-green-500" title="Mild" />
        <Meh class="w-5 h-5 text-yellow-500" title="Moderate" />
        <Frown class="w-5 h-5 text-red-500" title="Severe" />
      </div>
    </div>

    <!-- Tags -->
    <div>
      <label class="label">Tags</label>
      <TagSelector v-model="form.tags" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { format } from 'date-fns'
import { Smile, Meh, Frown } from 'lucide-vue-next'
import TagSelector from './TagSelector.vue'

const props = defineProps({ initialData: { type: Object, default: null } })

const today = format(new Date(), 'yyyy-MM-dd')
const now = format(new Date(), 'HH:mm')

const d = props.initialData
const form = ref({
  entry_date: d?.entry_date ?? today,
  entry_time: d?.entry_time ? String(d.entry_time).slice(0, 5) : now,
  description: d?.description ?? '',
  severity: d?.severity ?? 5,
  tags: d?.tags ?? [],
})

const severityLabel = computed(() => {
  const s = form.value.severity
  if (!s) return ''
  if (s <= 3) return 'Mild (' + s + '/10)'
  if (s <= 6) return 'Moderate (' + s + '/10)'
  return 'Severe (' + s + '/10)'
})

const severityColor = computed(() => {
  const s = form.value.severity
  if (!s) return 'text-gray-400'
  if (s <= 3) return 'text-green-600'
  if (s <= 6) return 'text-yellow-600'
  return 'text-red-600'
})

function getFormData() {
  if (!form.value.entry_date) throw new Error('Date is required')
  if (!form.value.entry_time) throw new Error('Time is required')
  if (!form.value.description?.trim()) throw new Error('Description is required')
  if (!form.value.severity) throw new Error('Severity is required')
  const { tags, ...rest } = form.value
  return { ...rest, tag_ids: tags.map(t => t.id) }
}

function reset() {
  form.value = {
    entry_date: today,
    entry_time: format(new Date(), 'HH:mm'),
    description: '',
    severity: 5,
    tags: [],
  }
}

defineExpose({ getFormData, reset })
</script>
