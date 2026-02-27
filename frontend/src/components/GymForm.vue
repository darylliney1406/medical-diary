<template>
  <div class="space-y-4">
    <!-- Date -->
    <div>
      <label class="label">Date <span class="text-red-500">*</span></label>
      <input v-model="form.entry_date" type="date" class="input-field" :max="today" required />
    </div>

    <!-- Exercises -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <label class="label mb-0">Exercises <span class="text-red-500">*</span></label>
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

            <!-- Machine name with autocomplete -->
            <div class="relative flex-1">
              <input
                v-model="ex.machine"
                type="text"
                class="input-field w-full"
                placeholder="Exercise / machine name"
                @input="onExerciseInput(i)"
                @focus="onExerciseFocus(i)"
                @blur="onExerciseBlur(i)"
              />
              <!-- Suggestions dropdown -->
              <div
                v-if="ex._showSuggestions && ex._suggestions.length"
                class="absolute z-10 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden"
              >
                <button
                  v-for="s in ex._suggestions"
                  :key="s.id"
                  type="button"
                  @mousedown.prevent
                  @click="selectExercise(i, s)"
                  class="w-full text-left px-4 py-2.5 hover:bg-gray-50 text-sm font-medium text-gray-900"
                >
                  {{ s.name }}
                </button>
              </div>
            </div>

            <!-- Mode toggle -->
            <div class="flex rounded-lg border border-gray-200 overflow-hidden text-xs">
              <button type="button" @click="ex._mode = 'cardio'" class="px-2 py-1 font-medium transition-colors" :class="ex._mode === 'cardio' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600'">Cardio</button>
              <button type="button" @click="ex._mode = 'weights'" class="px-2 py-1 font-medium transition-colors" :class="ex._mode === 'weights' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600'">Weights</button>
            </div>

            <button type="button" @click="removeExercise(i)" class="text-gray-300 hover:text-red-500">
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- Save to exercise list option -->
          <div v-if="!ex._fromCatalogue && ex.machine" class="flex items-center gap-2">
            <input v-model="ex._saveToList" type="checkbox" :id="'save-ex-' + i" class="rounded" />
            <label :for="'save-ex-' + i" class="text-sm text-gray-600">Save to exercise list</label>
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

    <!-- Tags -->
    <div>
      <label class="label">Tags</label>
      <TagSelector v-model="form.tags" />
    </div>

    <!-- Notes (was Session Notes) -->
    <div>
      <label class="label">Notes</label>
      <textarea v-model="form.session_notes" class="input-field" rows="2" placeholder="How was the session?"></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { format } from 'date-fns'
import { X, ChevronUp, ChevronDown } from 'lucide-vue-next'
import { exerciseCatalogueApi } from '@/api'
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
    _fromCatalogue: true,
    _saveToList: false,
    _showSuggestions: false,
    _suggestions: [],
  }))
}

const d = props.initialData
const form = ref({
  entry_date: d?.entry_date ?? today,
  session_notes: d?.session_notes ?? '',
  tags: d?.tags ?? [],
  exercises: parseExercises(d?.exercises),
})

const searchTimers = {}

async function loadSuggestions(i, query) {
  try {
    const { data } = await exerciseCatalogueApi.search(query ? { search: query } : {})
    form.value.exercises[i]._suggestions = (data.items || data).slice(0, 8)
  } catch {
    form.value.exercises[i]._suggestions = []
  }
}

async function onExerciseFocus(i) {
  form.value.exercises[i]._showSuggestions = true
  if (form.value.exercises[i]._suggestions.length === 0) {
    await loadSuggestions(i, form.value.exercises[i].machine)
  }
}

function onExerciseBlur(i) {
  setTimeout(() => {
    if (form.value.exercises[i]) {
      form.value.exercises[i]._showSuggestions = false
    }
  }, 200)
}

function onExerciseInput(i) {
  form.value.exercises[i]._fromCatalogue = false
  if (searchTimers[i]) clearTimeout(searchTimers[i])
  searchTimers[i] = setTimeout(() => loadSuggestions(i, form.value.exercises[i].machine), 300)
}

function selectExercise(i, suggestion) {
  form.value.exercises[i].machine = suggestion.name
  form.value.exercises[i]._fromCatalogue = true
  form.value.exercises[i]._saveToList = false
  form.value.exercises[i]._showSuggestions = false
}

function addExercise() {
  form.value.exercises.push({
    machine: '',
    _mode: 'weights',
    duration_min: null,
    sets: null,
    reps: null,
    weight_kg: null,
    _fromCatalogue: false,
    _saveToList: false,
    _showSuggestions: false,
    _suggestions: [],
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
  if (!form.value.entry_date) throw new Error('Date is required')
  if (form.value.exercises.length === 0) throw new Error('At least one exercise is required')
  for (let i = 0; i < form.value.exercises.length; i++) {
    if (!form.value.exercises[i].machine?.trim()) throw new Error(`Exercise ${i + 1}: name is required`)
  }
  const newExerciseNames = form.value.exercises
    .filter(ex => !ex._fromCatalogue && ex._saveToList && ex.machine?.trim())
    .map(ex => ex.machine.trim())
  return {
    entry_date: form.value.entry_date,
    session_notes: form.value.session_notes,
    tag_ids: form.value.tags.map(t => t.id),
    exercises: form.value.exercises.map(({ _mode, _fromCatalogue, _saveToList, _showSuggestions, _suggestions, ...ex }) => ex),
    _newExerciseNames: newExerciseNames,
  }
}

function reset() {
  form.value = { entry_date: today, session_notes: '', tags: [], exercises: [] }
}

defineExpose({ getFormData, reset })
</script>
