<template>
  <div class="max-w-2xl mx-auto px-4 py-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold text-gray-900">Weekly Summary</h1>
      <div class="flex items-center gap-2">
        <button @click="prevWeek" class="p-2 rounded-lg hover:bg-gray-100"><ChevronLeft class="w-4 h-4" /></button>
        <span class="text-sm font-medium text-gray-700 min-w-32 text-center">{{ weekLabel }}</span>
        <button @click="nextWeek" class="p-2 rounded-lg hover:bg-gray-100"><ChevronRight class="w-4 h-4" /></button>
      </div>
    </div>

    <div v-if="loading" class="space-y-4">
      <div v-for="i in 4" :key="i" class="h-32 bg-gray-100 rounded-xl animate-pulse"></div>
    </div>

    <div v-else class="space-y-4">
      <!-- BP Stats -->
      <div class="card">
        <h2 class="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Activity class="w-4 h-4 text-blue-500" /> Blood Pressure
        </h2>
        <div v-if="bpStats.sessions.length" class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-gray-50 rounded-lg p-3">
              <p class="text-xs text-gray-500 mb-1">Morning avg (pre-meds)</p>
              <p class="text-lg font-bold">{{ bpStats.morningAvg }}</p>
            </div>
            <div class="bg-gray-50 rounded-lg p-3">
              <p class="text-xs text-gray-500 mb-1">Evening avg (post-meds)</p>
              <p class="text-lg font-bold">{{ bpStats.eveningAvg }}</p>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs text-gray-500 border-b border-gray-100">
                  <th class="pb-2">Date</th>
                  <th class="pb-2">Time</th>
                  <th class="pb-2">Reading</th>
                  <th class="pb-2">Category</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-50">
                <tr v-for="session in bpStats.sessions" :key="session.id" class="py-2">
                  <td class="py-1.5">{{ session.date }}</td>
                  <td class="py-1.5 text-gray-500">{{ session.time }}</td>
                  <td class="py-1.5 font-medium">{{ session.reading }}</td>
                  <td class="py-1.5"><BPBadge :systolic="session.sys" :diastolic="session.dia" /></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <p v-else class="text-sm text-gray-400 text-center py-4">No BP readings this week.</p>
      </div>

      <!-- Symptoms -->
      <div class="card">
        <h2 class="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <AlertCircle class="w-4 h-4 text-orange-500" /> Symptoms
        </h2>
        <div v-if="symptomEntries.length" class="space-y-2">
          <div v-for="s in symptomEntries" :key="s.id" class="flex items-start gap-3 p-2 bg-gray-50 rounded-lg">
            <span class="text-xs text-gray-400 mt-0.5 whitespace-nowrap">{{ s.entry_date }}</span>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ s.description }}</p>
              <p v-if="s.severity" class="text-xs text-gray-500">Severity: {{ s.severity }}/10</p>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-gray-400 text-center py-4">No symptoms logged this week.</p>
      </div>

      <!-- AI Summary -->
      <div class="card">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <Sparkles class="w-4 h-4 text-indigo-600" />
            <h2 class="font-semibold text-gray-900">AI Summary</h2>
          </div>
          <button @click="generateSummary" :disabled="summaryLoading" class="text-xs text-indigo-600 font-medium">
            <Loader2 v-if="summaryLoading" class="w-3 h-3 animate-spin inline" />
            <span v-else>Generate</span>
          </button>
        </div>
        <div v-if="aiSummary" class="markdown-content" v-html="renderMarkdown(aiSummary)"></div>
        <p v-else class="text-sm text-gray-400 italic">No AI summary yet. Click Generate to create one.</p>
      </div>

      <button @click="exportPdf" class="w-full btn-secondary flex items-center justify-center gap-2">
        <Download class="w-4 h-4" /> Export as PDF
      </button>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { startOfWeek, endOfWeek, format, addWeeks, subWeeks, getISOWeek } from 'date-fns'
import { ChevronLeft, ChevronRight, Activity, AlertCircle, Sparkles, Loader2, Download } from 'lucide-vue-next'
import { bpApi, symptomApi, summariesApi, exportApi } from '@/api'
import { useToast } from '@/composables/useToast'
import BPBadge from '@/components/BPBadge.vue'
const { toast } = useToast()
const loading = ref(false)
const currentWeekStart = ref(startOfWeek(new Date(), { weekStartsOn: 1 }))
const bpData = ref([])
const symptomEntries = ref([])
const aiSummary = ref(null)
const summaryLoading = ref(false)
const weekLabel = computed(() => {
  const wS = currentWeekStart.value
  const wE = endOfWeek(wS, { weekStartsOn: 1 })
  return format(wS, "d MMM") + " to " + format(wE, "d MMM yyyy")
})
const isoWeek = computed(() => {
  const yr = format(currentWeekStart.value, "yyyy")
  const wk = String(getISOWeek(currentWeekStart.value)).padStart(2, "0")
  return yr + "-W" + wk
})
const bpStats = computed(() => {
  const sessions = []
  for (const entry of bpData.value) {
    for (const r of (entry.readings || [])) {
      sessions.push({ id: r.id || Math.random(), date: entry.entry_date, time: r.recorded_at || "",
        reading: r.systolic + "/" + r.diastolic + " (" + r.pulse + " bpm)", sys: r.systolic, dia: r.diastolic })
    }
  }
  const morning = sessions.filter(s => { const h = parseInt(s.time.split(":")[0]); return h >= 6 && h < 12 })
  const evening = sessions.filter(s => { const h = parseInt(s.time.split(":")[0]); return h >= 18 })
  const avg = (arr, key) => arr.length ? Math.round(arr.reduce((a,s) => a + s[key], 0) / arr.length) : null
  const morningAvg = morning.length ? avg(morning, "sys") + "/" + avg(morning, "dia") : "N/A"
  const eveningAvg = evening.length ? avg(evening, "sys") + "/" + avg(evening, "dia") : "N/A"
  return { sessions, morningAvg, eveningAvg }
})
onMounted(fetchWeek)
watch(currentWeekStart, fetchWeek)
async function fetchWeek() {
  loading.value = true; aiSummary.value = null
  const s = format(currentWeekStart.value, "yyyy-MM-dd")
  const e = format(endOfWeek(currentWeekStart.value, { weekStartsOn: 1 }), "yyyy-MM-dd")
  try {
    const [bp, sym, sum] = await Promise.allSettled([
      bpApi.list({ start_date: s, end_date: e, limit: 200 }),
      symptomApi.list({ start_date: s, end_date: e, limit: 100 }),
      summariesApi.getWeekly(isoWeek.value),
    ])
    bpData.value = bp.value?.data?.items || bp.value?.data || []
    symptomEntries.value = sym.value?.data?.items || sym.value?.data || []
    if (sum.status === "fulfilled") aiSummary.value = sum.value?.data?.content || sum.value?.data?.summary
  } finally { loading.value = false }
}
function prevWeek() { currentWeekStart.value = subWeeks(currentWeekStart.value, 1) }
function nextWeek() { currentWeekStart.value = addWeeks(currentWeekStart.value, 1) }
async function generateSummary() {
  summaryLoading.value = true
  try {
    const { data } = await summariesApi.generateWeekly(isoWeek.value)
    aiSummary.value = data.content || data.summary
    toast("Summary generated")
  } catch { toast("Failed", "error") } finally { summaryLoading.value = false }
}
function renderMarkdown(md) {
  if (!md) return ''
  let html = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^---+$/gm, '<hr>')
  html = html.replace(/((?:^.*\|.*$\n?)+)/gm, (block) => {
    const rows = block.trim().split('\n').filter(r => !/^[\s|:-]+$/.test(r))
    if (rows.length < 1) return block
    const toRow = (r, tag) => '<tr>' + r.split('|').slice(1,-1).map(c => `<${tag} class="px-2 py-1 border border-gray-200">${c.trim()}</${tag}>`).join('') + '</tr>'
    const [head, ...body] = rows
    return `<table class="w-full text-xs border-collapse my-2"><thead class="bg-gray-50">${toRow(head,'th')}</thead><tbody>${body.map(r=>toRow(r,'td')).join('')}</tbody></table>`
  })
  html = html.replace(/\n\n+/g, '</p><p class="mt-2">').replace(/\n/g, '<br>')
  return `<p>${html}</p>`
}
async function exportPdf() {
  try {
    const s = format(currentWeekStart.value, "yyyy-MM-dd")
    const e = format(endOfWeek(currentWeekStart.value, { weekStartsOn: 1 }), "yyyy-MM-dd")
    const { data } = await exportApi.pdf({ type: "weekly", start_date: s, end_date: e, include_summary: true })
    const url = URL.createObjectURL(data)
    const a = document.createElement("a"); a.href = url; a.download = "weekly-summary.pdf"; a.click()
    URL.revokeObjectURL(url)
  } catch { toast("Export failed", "error") }
}
</script>

<style scoped>
.markdown-content :deep(h1) { @apply text-base font-bold text-gray-900 mt-3 mb-1; }
.markdown-content :deep(h2) { @apply text-sm font-bold text-gray-800 mt-3 mb-1; }
.markdown-content :deep(h3) { @apply text-sm font-semibold text-gray-700 mt-2 mb-0.5; }
.markdown-content :deep(h4) { @apply text-xs font-semibold text-gray-600 mt-1; }
.markdown-content :deep(p)  { @apply text-sm text-gray-700; }
.markdown-content :deep(strong) { @apply font-semibold; }
.markdown-content :deep(hr)  { @apply border-gray-200 my-2; }
.markdown-content :deep(table) { @apply w-full text-xs border-collapse my-2 overflow-x-auto block; }
.markdown-content :deep(th)  { @apply bg-gray-100 font-semibold text-left; }
</style>
