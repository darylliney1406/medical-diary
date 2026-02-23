<template>
  <div class="space-y-4">
    <!-- Date -->
    <div>
      <label class="label">Date</label>
      <input v-model="form.entry_date" type="date" class="input-field" :max="today" />
    </div>

    <!-- Session Notes -->
    <div>
      <label class="label">Session notes</label>
      <textarea v-model="form.session_notes" class="input-field" rows="2" placeholder="How was the session?"></textarea>
    </div>

    <!-- Tags -->
    <div>
      <label class="label">Tags</label>
      <TagSelector v-model="form.tags" />
    </div>

    <!-- Exercises -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <label class="label mb-0">Exercises</label>
        <button type="button" @click="addExercise" class="text-sm text-indigo-600 font-medium hover:text-indigo-700">
          + Add exercise
        </button>
      </div>

      <div class="space-y-3">
        <div
          v-for="(ex, i) in form.exercises"
          :key="i"
          class="bg-gray-50 rounded-xl p-3 space-y-3"
        >
          <div class="flex items-center gap-2">
            <!-- Reorder buttons -->
            <div class="flex flex-col gap-0.5">
              <button type="button" @click="moveUp(i)" :disabled="i === 0" class="text-gray-300 hover:text-gray-500 disabled:opacity-30">
                <ChevronUp class="w-4 h-4" />
              </button>
              <button type="button" @click="moveDown(i)" :disabled="i === form.exercises.length - 1" class="text-gray-300 hover:text-gray-500 disabled:opacity-30">
                <ChevronDown class="w-4 h-4" />
              </button>
            </div>

            <!-- Machine name -->
            <input
              v-model="ex.machine"
              type="text"
              class="input-field flex-1"
              placeholder="Exercise / machine name"
            />

            <!-- Mode toggle -->
            <div class="flex rounded-lg border border-gray-200 overflow-hidden text-xs">
              <button type="button" @click="ex._mode = 'cardio'" class="px-2 py-1 font-medium transition-colors" :class="ex._mode === 'cardio' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600'">Cardio</button>
              <button type="button" @click="ex._mode = 'weights'" class="px-2 py-1 font-medium transition-colors" :class="ex._mode === 'weights' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600'">Weights</button>
            </div>

            <button type="button" @click="removeExercise(i)" class="text-gray-300 hover:text-red-500">
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- Cardio mode: duration only -->
          <div v-if="ex._mode === 'cardio'">
            <label class="label text-xs">Duration (minutes)</label>
            <input v-model.number="ex.duration_min" type="number" min="1" class="input-field" placeholder="30" />
          </div>

          <!-- Weights mode: sets, reps, weight -->
          <div v-else class="grid grid-cols-3 gap-2">
            <div>
              <label class="label text-xs">Sets</label>
              <input v-model.number="ex.sets" type="number" min="1" class="input-field" placeholder="3" />
            </div>
            <div>
              <label class="label text-xs">Reps</label>
              <input v-model.number="ex.reps" type="number" min="1" class="input-field" placeholder="12" />
            </div>
            <div>
              <label class="label text-xs">Weight (kg)</label>
              <input v-model.number="ex.weight_kg" type="number" min="0" step="0.5" class="input-field" placeholder="20" />
            </div>
          </div>
        </div>
      </div>

      <p v-if="form.exercises.length === 0" class="text-sm text-gray-400 text-center py-4 border-2 border-dashed border-gray-200 rounded-xl">
        No exercises yet. Tap "+ Add exercise" to get started.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { format } from 'date-fns'
import { X, ChevronUp, ChevronDown } from 'lucide-vue-next'
import TagSelector from './TagSelector.vue'

const props = defineProps({ initialData: { type: Object, default: null } })

const today = format(new Date(), 'yyyy-MM-dd')

function parseExercises(exercises) {
  if (!exercises?.length) return []
  return exercises.map(ex => ({
    machine: ex.machine ?? '',
    _mode: ex.duration_min != null ? 'cardio' : 'weights',
    duration_min: ex.duration_min ?? null,
    sets: ex.sets ?? null,
    reps: ex.reps ?? null,
    weight_kg: ex.weight_kg ?? null,
  }))
}

const d = props.initialData
const form = ref({
  entry_date: d?.entry_date ?? today,
  session_notes: d?.session_notes ?? '',
  tags: d?.tags ?? [],
  exercises: parseExercises(d?.exercises),
})

function addExercise() {
  form.value.exercises.push({
    machine: '',
    _mode: 'weights',
    duration_min: null,
    sets: null,
    reps: null,
    weight_kg: null,
  })
}

function removeExercise(i) {
  form.value.exercises.splice(i, 1)
}

function moveUp(i) {
  if (i > 0) {
    const arr = form.value.exercises
    ;[arr[i - 1], arr[i]] = [arr[i], arr[i - 1]]
  }
}

function moveDown(i) {
  const arr = form.value.exercises
  if (i < arr.length - 1) {
    ;[arr[i], arr[i + 1]] = [arr[i + 1], arr[i]]
  }
}

function getFormData() {
  return {
    entry_date: form.value.entry_date,
    session_notes: form.value.session_notes,
    tag_ids: form.value.tags.map(t => t.id),
    exercises: form.value.exercises.map(({ _mode, ...ex }) => ex),
  }
}

function reset() {
  form.value = { entry_date: today, session_notes: '', tags: [], exercises: [] }
}

defineExpose({ getFormData, reset })
</script>
