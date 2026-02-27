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

    <!-- Meal Type -->
    <div>
      <label class="label">Meal type <span class="text-red-500">*</span></label>
      <div class="grid grid-cols-5 gap-2">
        <button
          v-for="m in mealTypes"
          :key="m.value"
          type="button"
          @click="form.meal_type = m.value"
          class="flex flex-col items-center gap-1 py-2 px-1 rounded-lg border text-xs font-medium transition-colors"
          :class="form.meal_type === m.value ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-gray-200 text-gray-600 hover:border-gray-300'"
        >
          <component :is="m.icon" class="w-5 h-5" />
          {{ m.label }}
        </button>
      </div>
      <p v-if="!form.meal_type" class="text-xs text-gray-400 mt-1">Please select a meal type</p>
    </div>

    <!-- Description with catalogue search -->
    <div>
      <label class="label">Food / Drink <span class="text-red-500">*</span></label>
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          class="input-field"
          placeholder="Search saved items or type freely..."
          @input="onSearchInput"
          @focus="onFocus"
          @blur="onBlur"
        />
        <!-- Catalogue suggestions -->
        <div
          v-if="showSuggestions && suggestions.length"
          class="absolute z-10 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden"
        >
          <button
            v-for="item in suggestions"
            :key="item.id"
            type="button"
            @mousedown.prevent
            @click="selectCatalogueItem(item)"
            class="w-full text-left px-4 py-2.5 hover:bg-gray-50 flex items-center justify-between"
          >
            <span class="text-sm font-medium text-gray-900">{{ item.name }}</span>
            <span class="text-xs text-gray-400">{{ item.typical_portion }}</span>
          </button>
        </div>
      </div>
      <!-- Save to catalogue option -->
      <div v-if="!selectedFromCatalogue && searchQuery" class="flex items-center gap-2 mt-2">
        <input v-model="saveToLog" type="checkbox" id="save-cat" class="rounded" />
        <label for="save-cat" class="text-sm text-gray-600">Save to food catalogue</label>
      </div>
    </div>

    <!-- Quantity -->
    <div>
      <label class="label">Quantity / portion <span class="text-red-500">*</span></label>
      <input v-model="form.quantity" type="text" class="input-field" placeholder="e.g. 1 cup, 200g, 1 slice" required />
    </div>

    <!-- Tags -->
    <div>
      <label class="label">Tags</label>
      <TagSelector v-model="form.tags" />
    </div>

    <!-- Notes -->
    <div>
      <label class="label">Notes</label>
      <textarea v-model="form.notes" class="input-field" rows="2" placeholder="Any notes..."></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { format } from 'date-fns'
import { Sunrise, Sun, Moon, Apple, Droplets } from 'lucide-vue-next'
import { catalogueApi } from '@/api'
import TagSelector from './TagSelector.vue'

const props = defineProps({ initialData: { type: Object, default: null } })

const today = format(new Date(), 'yyyy-MM-dd')
const now = format(new Date(), 'HH:mm')

const mealTypes = [
  { value: 'breakfast', label: 'Breakfast', icon: Sunrise },
  { value: 'lunch', label: 'Lunch', icon: Sun },
  { value: 'dinner', label: 'Dinner', icon: Moon },
  { value: 'snack', label: 'Snack', icon: Apple },
  { value: 'drink', label: 'Drink', icon: Droplets },
]

const d = props.initialData
const form = ref({
  entry_date: d?.entry_date ?? today,
  entry_time: d?.entry_time ? String(d.entry_time).slice(0, 5) : now,
  meal_type: d?.meal_type ?? null,
  description: d?.description ?? '',
  quantity: d?.quantity ?? '',
  catalogue_item_id: d?.catalogue_item_id ?? null,
  notes: d?.notes ?? '',
  tags: d?.tags ?? [],
})

const searchQuery = ref(d?.description ?? '')
const suggestions = ref([])
const showSuggestions = ref(false)
const selectedFromCatalogue = ref(false)
const saveToLog = ref(false)

let searchTimer = null
let blurTimer = null

async function onFocus() {
  showSuggestions.value = true
  if (blurTimer) { clearTimeout(blurTimer); blurTimer = null }
  // Preload all items when focused with empty or short query
  if (!searchQuery.value || suggestions.value.length === 0) {
    try {
      const { data } = await catalogueApi.search({ search: searchQuery.value || '' })
      suggestions.value = (data.items || data).slice(0, 8)
    } catch { suggestions.value = [] }
  }
}

function onBlur() {
  blurTimer = setTimeout(() => { showSuggestions.value = false }, 200)
}

async function onSearchInput() {
  selectedFromCatalogue.value = false
  form.value.catalogue_item_id = null
  if (searchTimer) clearTimeout(searchTimer)
  if (!searchQuery.value) {
    suggestions.value = []
    // Reload all items
    try {
      const { data } = await catalogueApi.search({})
      suggestions.value = (data.items || data).slice(0, 8)
    } catch { suggestions.value = [] }
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      const { data } = await catalogueApi.search({ search: searchQuery.value })
      suggestions.value = (data.items || data).slice(0, 8)
    } catch { suggestions.value = [] }
  }, 300)
}

function selectCatalogueItem(item) {
  searchQuery.value = item.name
  form.value.description = item.name
  form.value.catalogue_item_id = item.id
  if (item.typical_portion) form.value.quantity = item.typical_portion
  selectedFromCatalogue.value = true
  showSuggestions.value = false
}

function getFormData() {
  if (!form.value.entry_date) throw new Error('Date is required')
  if (!form.value.entry_time) throw new Error('Time is required')
  if (!form.value.meal_type) throw new Error('Meal type is required')
  if (!searchQuery.value?.trim()) throw new Error('Food / Drink description is required')
  if (!form.value.quantity?.trim()) throw new Error('Quantity / portion is required')
  const { tags, ...rest } = form.value
  return {
    ...rest,
    description: searchQuery.value || form.value.description,
    tag_ids: tags.map(t => t.id),
    _saveToLog: saveToLog.value && !selectedFromCatalogue.value,
  }
}

function reset() {
  form.value = {
    entry_date: today,
    entry_time: format(new Date(), 'HH:mm'),
    meal_type: null,
    description: '',
    quantity: '',
    catalogue_item_id: null,
    notes: '',
    tags: [],
  }
  searchQuery.value = ''
  suggestions.value = []
  selectedFromCatalogue.value = false
  saveToLog.value = false
}

defineExpose({ getFormData, reset })
</script>
