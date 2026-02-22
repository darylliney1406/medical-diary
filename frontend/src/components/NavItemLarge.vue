<template>
  <RouterLink
    :to="item.to"
    class="flex flex-col items-center gap-2 p-3 rounded-xl bg-gray-50 text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 transition-colors"
    :class="isActive ? 'bg-indigo-50 text-indigo-700' : ''"
    @click="emit('click')"
  >
    <component :is="item.icon" class="w-6 h-6" />
    <span class="text-xs font-medium">{{ item.label }}</span>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

const props = defineProps({
  item: { type: Object, required: true },
})
const emit = defineEmits(['click'])
const route = useRoute()
const isActive = computed(() => route.path === props.item.to)
</script>
