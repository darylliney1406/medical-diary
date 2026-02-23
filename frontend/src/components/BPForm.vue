<template>
  <div class="space-y-4">
    <!-- Date -->
    <div>
      <label class="label">Date</label>
      <input v-model="form.entry_date" type="date" class="input-field" :max="today" />
    </div>

    <!-- Readings -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <label class="label mb-0">Readings</label>
        <button v-if="form.readings.length < 3" type="button" @click="addReading" class="text-sm text-indigo-600 font-medium hover:text-indigo-700">
          + Add reading
        </button>
      </div>

      <div class="space-y-3">
        <div v-for="(reading, i) in form.readings" :key="i" class="bg-gray-50 rounded-xl p-3 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-700">Reading {{ i + 1 }}</span>
            <button v-if="form.readings.length > 1" type="button" @click="removeReading(i)" class="text-red-400 hover:text-red-600">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="grid grid-cols-3 gap-2">
            <div>
              <label class="label text-xs">Systolic</label>
              <input
                v-model.number="reading.systolic"
                type="number"
                min="50" max="300"
                class="input-field"
                placeholder="120"
                @input="validateReading(i)"
              />
            </div>
            <div>
              <label class="label text-xs">Diastolic</label>
              <input
                v-model.number="reading.diastolic"
                type="number"
                min="30" max="200"
                class="input-field"
                placeholder="80"
                @input="validateReading(i)"
              />
            </div>
            <div>
              <label class="label text-xs">Pulse</label>
              <input
                v-model.number="reading.pulse"
                type="number"
                min="30" max="250"
                class="input-field"
                placeholder="72"
              />
            </div>
          </div>

          <!-- Time -->
          <div>
            <label class="label text-xs">Time</label>
            <input v-model="reading.recorded_at" type="time" class="input-field" />
          </div>

          <!-- Live BP badge -->
          <div v-if="reading.systolic && reading.diastolic" class="flex items-center gap-2">
            <BPBadge :systolic="reading.systolic" :diastolic="reading.diastolic" />
            <span v-if="readingErrors[i]" class="text-xs text-red-600">{{ readingErrors[i] }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tags -->
    <div>
      <label class="label">Tags</label>
      <TagSelector v-model="form.tags" />
    </div>

    <!-- Notes -->
    <div>
      <label class="label">Notes</label>
      <textarea v-model="form.notes" class="input-field" rows="3" placeholder="Any notes about this reading..."></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { format } from 'date-fns'
import { X } from 'lucide-vue-next'
import BPBadge from './BPBadge.vue'
import TagSelector from './TagSelector.vue'

const props = defineProps({ initialData: { type: Object, default: null } })

const today = format(new Date(), 'yyyy-MM-dd')
const now = format(new Date(), 'HH:mm')

function parseReadings(readings) {
  if (!readings?.length) return [{ systolic: null, diastolic: null, pulse: null, recorded_at: now }]
  return readings.map(r => ({
    systolic: r.systolic ?? null,
    diastolic: r.diastolic ?? null,
    pulse: r.pulse ?? null,
    recorded_at: r.recorded_at ? String(r.recorded_at).slice(11, 16) : now,
  }))
}

const d = props.initialData
const form = ref({
  entry_date: d?.entry_date ?? today,
  notes: d?.notes ?? '',
  tags: d?.tags ?? [],
  readings: parseReadings(d?.readings),
})

const readingErrors = ref({})

function addReading() {
  if (form.value.readings.length < 3) {
    form.value.readings.push({ systolic: null, diastolic: null, pulse: null, recorded_at: format(new Date(), 'HH:mm') })
  }
}

function removeReading(i) {
  form.value.readings.splice(i, 1)
}

function validateReading(i) {
  const r = form.value.readings[i]
  if (r.systolic && (r.systolic < 50 || r.systolic > 300)) {
    readingErrors.value[i] = 'Systolic must be 50-300'
  } else if (r.diastolic && (r.diastolic < 30 || r.diastolic > 200)) {
    readingErrors.value[i] = 'Diastolic must be 30-200'
  } else {
    delete readingErrors.value[i]
  }
}

function getFormData() {
  return {
    entry_date: form.value.entry_date,
    notes: form.value.notes,
    tag_ids: form.value.tags.map(t => t.id),
    readings: form.value.readings
      .filter(r => r.systolic && r.diastolic)
      .map(r => ({
        systolic: r.systolic,
        diastolic: r.diastolic,
        pulse: r.pulse,
        recorded_at: form.value.entry_date + 'T' + r.recorded_at + ':00',
      })),
  }
}

function reset() {
  form.value = {
    entry_date: today,
    notes: '',
    tags: [],
    readings: [{ systolic: null, diastolic: null, pulse: null, recorded_at: format(new Date(), 'HH:mm') }],
  }
}

defineExpose({ getFormData, reset })
</script>
