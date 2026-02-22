<template>
  <span
    v-if="category"
    class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold"
    :class="category.classes"
  >
    {{ category.label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { getBPCategory } from '@/composables/useBPCategory'

const props = defineProps({
  systolic: { type: Number, default: null },
  diastolic: { type: Number, default: null },
})

const category = computed(() => {
  if (!props.systolic || !props.diastolic) return null
  return getBPCategory(props.systolic, props.diastolic)
})
</script>
