<template>
  <RouterLink
    :to="item.to"
    class="flex flex-col items-center gap-0.5 px-3 py-2 transition-colors"
    :class="isActive ? 'text-indigo-600' : 'text-gray-500'"
  >
    <component :is="item.icon" class="w-6 h-6" />
    <span class="text-xs">{{ item.label }}</span>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

const props = defineProps({
  item: { type: Object, required: true },
})

const route = useRoute()
const isActive = computed(() => route.path === props.item.to || route.path.startsWith(props.item.to + '/'))
</script>
