<template>
  <div class="space-y-2">
    <div class="flex flex-wrap gap-1.5">
      <button
        v-for="tag in availableTags"
        :key="tag.id"
        type="button"
        @click="toggleTag(tag)"
        class="px-3 py-1 rounded-full text-sm font-medium border transition-colors"
        :class="isSelected(tag) ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-400'"
      >
        {{ tag.name }}
      </button>
      <button
        type="button"
        @click="showCreate = !showCreate"
        class="px-3 py-1 rounded-full text-sm font-medium border border-dashed border-gray-300 text-gray-500 hover:border-indigo-400"
      >
        + New tag
      </button>
    </div>

    <div v-if="showCreate" class="flex gap-2">
      <input v-model="newTagName" type="text" class="input-field flex-1" placeholder="Tag name" @keydown.enter.prevent="createTag" />
      <button type="button" @click="createTag" class="btn-primary px-3 py-2">Add</button>
    </div>

    <div v-if="loading" class="text-sm text-gray-400">Loading tags...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { tagsApi } from '@/api'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const availableTags = ref([])
const loading = ref(false)
const showCreate = ref(false)
const newTagName = ref('')

onMounted(fetchTags)

async function fetchTags() {
  loading.value = true
  try {
    const { data } = await tagsApi.list()
    availableTags.value = data.items || data
  } catch (e) {
    console.warn('Could not load tags', e)
  } finally {
    loading.value = false
  }
}

function isSelected(tag) {
  return props.modelValue.some(t => t.id === tag.id)
}

function toggleTag(tag) {
  const current = [...props.modelValue]
  const idx = current.findIndex(t => t.id === tag.id)
  if (idx > -1) {
    current.splice(idx, 1)
  } else {
    current.push(tag)
  }
  emit('update:modelValue', current)
}

async function createTag() {
  if (!newTagName.value.trim()) return
  try {
    const { data } = await tagsApi.create({ name: newTagName.value.trim() })
    availableTags.value.push(data)
    toggleTag(data)
    newTagName.value = ''
    showCreate.value = false
  } catch (e) {
    console.error('Failed to create tag', e)
  }
}
</script>
