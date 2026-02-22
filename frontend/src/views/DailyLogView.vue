<template>
  <div class="max-w-2xl mx-auto px-4 py-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold text-gray-900">Daily Log</h1>
      <div class="flex items-center gap-2">
        <button @click="prevWeek" class="p-2 rounded-lg hover:bg-gray-100"><ChevronLeft class="w-4 h-4" /></button>
        <span class="text-sm font-medium text-gray-700 min-w-28 text-center">{{ weekLabel }}</span>
        <button @click="nextWeek" class="p-2 rounded-lg hover:bg-gray-100"><ChevronRight class="w-4 h-4" /></button>
      </div>
    </div>

    <div v-if="loading" class="space-y-4">
      <div v-for="i in 5" :key="i" class="h-24 bg-gray-100 rounded-xl animate-pulse"></div>
    </div>

    <div v-else class="space-y-4">
      <div v-for="day in weekDays" :key="day.date" class="space-y-2">
        <!-- Day header -->
        <button
          class="w-full flex items-center justify-between text-left"
          @click="toggleDay(day.date)"
        >
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold text-gray-900" :class="day.isToday ? 'text-indigo-700' : ''">{{ day.label }}</span>
            <span v-if="day.isToday" class="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">Today</span>
            <span class="text-xs text-gray-400">{{ day.entries.length }} entries</span>
          </div>
          <ChevronDown class="w-4 h-4 text-gray-400 transition-transform" :class="collapsedDays[day.date] ? 'rotate-180' : ''" />
        </button>

        <div v-if="!collapsedDays[day.date] && day.entries.length" class="space-y-2 pl-2 border-l-2 border-gray-100">
          <EntryCard v-for="entry in day.entries" :key="entry._type+entry.id"
            :entry="entry" :type="entry._type" @edit="handleEdit" @delete="handleDelete(entry)" />
        </div>
        <p v-else-if="!collapsedDays[day.date]" class="text-sm text-gray-400 pl-2">No entries.</p>
      </div>
    </div>

    <!-- AI Summary -->
    <div class="mt-6 card">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <Sparkles class="w-4 h-4 text-indigo-600" />
          <h2 class="text-sm font-semibold">Weekly AI Summary</h2>
        </div>
        <button @click="generateSummary" :disabled="summaryLoading" class="text-xs text-indigo-600 font-medium">
          <Loader2 v-if="summaryLoading" class="w-3 h-3 animate-spin inline" />
          <span v-else>Generate</span>
        </button>
      </div>
      <p v-if="summary" class="text-sm text-gray-700 leading-relaxed">{{ summary }}</p>
      <p v-else class="text-sm text-gray-400 italic">No summary generated yet.</p>
    </div>

    <!-- Export button -->
    <button @click="exportWeek" class="mt-4 w-full btn-secondary flex items-center justify-center gap-2">
      <Download class="w-4 h-4" /> Export week as PDF
    </button>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { startOfWeek, endOfWeek, eachDayOfInterval, format, isToday, addWeeks, subWeeks, getISOWeek } from 'date-fns'
import { ChevronLeft, ChevronRight, ChevronDown, Sparkles, Loader2, Download } from 'lucide-vue-next'
import { bpApi, symptomApi, foodApi, gymApi, summariesApi, exportApi } from '@/api'
import { useToast } from '@/composables/useToast'
import EntryCard from '@/components/EntryCard.vue'
const { toast } = useToast()
const loading = ref(false)
const currentWeekStart = ref(startOfWeek(new Date(), { weekStartsOn: 1 }))
const allEntries = ref([])
const summary = ref(null)
const summaryLoading = ref(false)
const collapsedDays = ref({})
const weekLabel = computed(() => {
  const wS = currentWeekStart.value
  const wE = endOfWeek(wS, { weekStartsOn: 1 })
  return format(wS, "d MMM") + " - " + format(wE, "d MMM yyyy")
})
const weekDays = computed(() => {
  const wS = currentWeekStart.value
  const wE = endOfWeek(wS, { weekStartsOn: 1 })
  const days = eachDayOfInterval({ start: wS, end: wE })
  return days.map(d => {
    const ds = format(d, "yyyy-MM-dd")
    return { date: ds, label: format(d, "EEEE, d MMMM"), isToday: isToday(d),
      entries: allEntries.value.filter(e => e.entry_date === ds) }
  })
})
const isoWeek = computed(() => {
  const yr = format(currentWeekStart.value, "yyyy")
  const wk = String(getISOWeek(currentWeekStart.value)).padStart(2, "0")
  const separator = "-W"
  return yr + separator + wk
})
onMounted(fetchWeek)
watch(currentWeekStart, fetchWeek)
async function fetchWeek() {
  loading.value = true
  summary.value = null
  const startStr = format(currentWeekStart.value, "yyyy-MM-dd")
  const endStr = format(endOfWeek(currentWeekStart.value, { weekStartsOn: 1 }), "yyyy-MM-dd")
  try {
    const params = { start_date: startStr, end_date: endStr, limit: 100 }
    const bpRes = bpApi.list(params)
    const symRes = symptomApi.list(params)
    const foodRes = foodApi.list(params)
    const gymRes = gymApi.list(params)
    const sumRes = summariesApi.getWeekly(isoWeek.value)
    const results = await Promise.allSettled([bpRes, symRes, foodRes, gymRes, sumRes])
    const [bp, sym, food, gym, sum] = results
    allEntries.value = [
      ...(bp.value?.data?.items || bp.value?.data || []).map(e => ({ ...e, _type: "bp" })),
      ...(sym.value?.data?.items || sym.value?.data || []).map(e => ({ ...e, _type: "symptom" })),
      ...(food.value?.data?.items || food.value?.data || []).map(e => ({ ...e, _type: "food" })),
      ...(gym.value?.data?.items || gym.value?.data || []).map(e => ({ ...e, _type: "gym" })),
    ]
    if (sum.status === "fulfilled") summary.value = sum.value?.data?.content || sum.value?.data?.summary
  } finally { loading.value = false }
}
function prevWeek() { currentWeekStart.value = subWeeks(currentWeekStart.value, 1) }
function nextWeek() { currentWeekStart.value = addWeeks(currentWeekStart.value, 1) }
function toggleDay(date) { collapsedDays.value[date] = !collapsedDays.value[date] }
function handleEdit(entry) {}
function handleDelete(entry) {
  allEntries.value = allEntries.value.filter(e => !(e.id === entry.id && e._type === entry._type))
}
async function generateSummary() {
  summaryLoading.value = true
  try {
    const { data } = await summariesApi.generateWeekly(isoWeek.value)
    summary.value = data.content || data.summary
    toast("Summary generated")
  } catch { toast("Failed to generate", "error") } finally { summaryLoading.value = false }
}
async function exportWeek() {
  try {
    const s = format(currentWeekStart.value, "yyyy-MM-dd")
    const e = format(endOfWeek(currentWeekStart.value, { weekStartsOn: 1 }), "yyyy-MM-dd")
    const { data } = await exportApi.pdf({ type: "daily", start_date: s, end_date: e, include_summary: true })
    const url = URL.createObjectURL(data)
    const a = document.createElement("a"); a.href = url; a.download = "week-log.pdf"; a.click()
    URL.revokeObjectURL(url)
  } catch { toast("Export failed", "error") }
}
</script>
