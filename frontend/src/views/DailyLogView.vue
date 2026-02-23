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
        <button class="w-full flex items-center justify-between text-left" @click="toggleDay(day.date)">
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold text-gray-900" :class="day.isToday ? 'text-indigo-700' : ''">{{ day.label }}</span>
            <span v-if="day.isToday" class="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">Today</span>
            <span class="text-xs text-gray-400">{{ day.entries.length }} entries</span>
          </div>
          <ChevronDown class="w-4 h-4 text-gray-400 transition-transform" :class="collapsedDays[day.date] ? 'rotate-180' : ''" />
        </button>
        <div v-if="!collapsedDays[day.date] && day.entries.length" class="space-y-2 pl-2 border-l-2 border-gray-100">
          <EntryCard v-for="entry in day.entries" :key="entry._type+entry.id"
            :entry="entry" :type="entry._type"
            @view="openDetail(entry)"
            @edit="openEdit(entry)"
            @delete="confirmDelete(entry)" />
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
      <div v-if="summary" class="markdown-content" v-html="renderMarkdown(summary)"></div>
      <p v-else class="text-sm text-gray-400 italic">No summary generated yet.</p>
    </div>

    <button @click="exportWeek" class="mt-4 w-full btn-secondary flex items-center justify-center gap-2">
      <Download class="w-4 h-4" /> Export week as PDF
    </button>
  </div>

  <!-- ── Delete confirmation ─────────────────────────────── -->
  <Teleport to="body">
    <div v-if="pendingDelete" class="fixed inset-0 z-50 flex items-end md:items-center justify-center p-4 bg-black/40" @click.self="pendingDelete = null">
      <div class="w-full max-w-sm bg-white rounded-2xl shadow-xl p-6 text-center">
        <Trash2 class="w-8 h-8 text-red-500 mx-auto mb-3" />
        <p class="font-semibold text-gray-900 mb-1">Delete this entry?</p>
        <p class="text-sm text-gray-500 mb-5">This cannot be undone.</p>
        <div class="flex gap-3">
          <button @click="pendingDelete = null" class="btn-secondary flex-1">Cancel</button>
          <button @click="doDelete" class="btn-danger flex-1" :disabled="deleting">
            <Loader2 v-if="deleting" class="w-4 h-4 animate-spin inline mr-1" />Delete
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- ── Entry detail sheet ─────────────────────────────── -->
  <Teleport to="body">
    <div v-if="detailEntry" class="fixed inset-0 z-50 flex items-end md:items-center justify-center p-4 bg-black/40" @click.self="detailEntry = null">
      <div class="w-full max-w-lg bg-white rounded-2xl shadow-xl max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 border-b border-gray-100 sticky top-0 bg-white rounded-t-2xl">
          <span class="font-semibold text-gray-900">{{ detailTypeLabel }}</span>
          <div class="flex items-center gap-2">
            <button @click="openEdit(detailEntry); detailEntry = null" class="p-1.5 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-indigo-50">
              <Pencil class="w-4 h-4" />
            </button>
            <button @click="detailEntry = null" class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-50">
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>
        <div class="p-4 space-y-3 text-sm">
          <div class="flex items-center gap-2 text-gray-500">
            <Calendar class="w-4 h-4" />
            <span>{{ detailEntry.entry_date }}</span>
            <span v-if="detailEntry.entry_time">· {{ detailEntry.entry_time }}</span>
          </div>
          <!-- BP detail -->
          <template v-if="detailEntry._type === 'bp'">
            <div v-for="(r, i) in detailEntry.readings" :key="i" class="bg-gray-50 rounded-xl p-3">
              <p class="text-xs font-medium text-gray-500 mb-1">Reading {{ i + 1 }}</p>
              <p class="text-2xl font-bold text-gray-900">{{ r.systolic }}/{{ r.diastolic }} <span class="text-base font-normal text-gray-500">{{ r.pulse }} bpm</span></p>
              <p v-if="r.recorded_at" class="text-xs text-gray-400 mt-1">{{ r.recorded_at }}</p>
            </div>
          </template>
          <!-- Symptom detail -->
          <template v-else-if="detailEntry._type === 'symptom'">
            <p class="font-medium text-gray-900">{{ detailEntry.description }}</p>
            <div v-if="detailEntry.severity" class="flex items-center gap-2">
              <div class="flex-1 bg-gray-100 rounded-full h-2">
                <div class="h-2 rounded-full" :class="detailEntry.severity <= 3 ? 'bg-green-400' : detailEntry.severity <= 6 ? 'bg-yellow-400' : 'bg-red-500'" :style="{width: (detailEntry.severity * 10) + '%'}"></div>
              </div>
              <span class="text-gray-600 font-medium">{{ detailEntry.severity }}/10</span>
            </div>
          </template>
          <!-- Food detail -->
          <template v-else-if="detailEntry._type === 'food'">
            <p class="font-medium text-gray-900 capitalize">{{ detailEntry.meal_type }} — {{ detailEntry.description }}</p>
            <p v-if="detailEntry.quantity" class="text-gray-600">Quantity: {{ detailEntry.quantity }}</p>
          </template>
          <!-- Gym detail -->
          <template v-else-if="detailEntry._type === 'gym'">
            <div v-for="ex in detailEntry.exercises" :key="ex.id" class="bg-gray-50 rounded-lg p-2">
              <p class="font-medium">{{ ex.machine }}</p>
              <p class="text-xs text-gray-500">
                <span v-if="ex.sets">{{ ex.sets }} sets</span>
                <span v-if="ex.reps"> × {{ ex.reps }} reps</span>
                <span v-if="ex.weight_kg"> · {{ ex.weight_kg }} kg</span>
                <span v-if="ex.duration_min"> · {{ ex.duration_min }} min</span>
              </p>
            </div>
          </template>
          <!-- Notes -->
          <p v-if="detailEntry.notes || detailEntry.session_notes" class="text-gray-600 bg-gray-50 rounded-lg p-3">
            {{ detailEntry.notes || detailEntry.session_notes }}
          </p>
          <!-- Tags -->
          <div v-if="detailEntry.tags?.length" class="flex flex-wrap gap-1">
            <span v-for="tag in detailEntry.tags" :key="tag.id" class="tag-chip">{{ tag.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- ── Edit sheet ─────────────────────────────────────── -->
  <Teleport to="body">
    <div v-if="editEntry" class="fixed inset-0 z-50 flex items-end md:items-center justify-center p-4 bg-black/40" @click.self="editEntry = null">
      <div class="w-full max-w-lg bg-white rounded-2xl shadow-xl max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 border-b border-gray-100 sticky top-0 bg-white rounded-t-2xl">
          <span class="font-semibold text-gray-900">Edit entry</span>
          <button @click="editEntry = null" class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-50"><X class="w-5 h-5" /></button>
        </div>
        <div class="p-4">
          <component :is="editFormComponent" ref="editFormRef" :initial-data="editEntry" />
          <div v-if="editError" class="mt-3 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{{ editError }}</div>
          <div class="flex gap-3 mt-4">
            <button @click="editEntry = null" class="btn-secondary flex-1">Cancel</button>
            <button @click="saveEdit" class="btn-primary flex-1" :disabled="saving">
              <Loader2 v-if="saving" class="w-4 h-4 animate-spin inline mr-1" />Save
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, watch, shallowRef } from 'vue'
import { startOfWeek, endOfWeek, eachDayOfInterval, format, isToday, addWeeks, subWeeks, getISOWeek } from 'date-fns'
import { ChevronLeft, ChevronRight, ChevronDown, Sparkles, Loader2, Download, Trash2, Pencil, X, Calendar } from 'lucide-vue-next'
import { bpApi, symptomApi, foodApi, gymApi, summariesApi, exportApi } from '@/api'
import { useEntriesStore } from '@/stores/entries'
import { useToast } from '@/composables/useToast'
import EntryCard from '@/components/EntryCard.vue'
import BPForm from '@/components/BPForm.vue'
import SymptomForm from '@/components/SymptomForm.vue'
import FoodForm from '@/components/FoodForm.vue'
import GymForm from '@/components/GymForm.vue'

const { toast } = useToast()
const entries = useEntriesStore()
const loading = ref(false)
const currentWeekStart = ref(startOfWeek(new Date(), { weekStartsOn: 1 }))
const allEntries = ref([])
const summary = ref(null)
const summaryLoading = ref(false)
const collapsedDays = ref({})
const pendingDelete = ref(null)
const deleting = ref(false)
const detailEntry = ref(null)
const editEntry = ref(null)
const editFormRef = ref(null)
const editError = ref('')
const saving = ref(false)

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
  return yr + "-W" + wk
})
const detailTypeLabel = computed(() => {
  if (!detailEntry.value) return ''
  return { bp: 'Blood Pressure', symptom: 'Symptom', food: 'Food', gym: 'Gym' }[detailEntry.value._type] || ''
})
const editFormComponent = computed(() => {
  if (!editEntry.value) return null
  return { bp: BPForm, symptom: SymptomForm, food: FoodForm, gym: GymForm }[editEntry.value._type] || null
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
    const results = await Promise.allSettled([
      bpApi.list(params), symptomApi.list(params), foodApi.list(params), gymApi.list(params),
      summariesApi.getWeekly(isoWeek.value),
    ])
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

function openDetail(entry) { detailEntry.value = entry }
function openEdit(entry) { editEntry.value = { ...entry }; editError.value = '' }

function confirmDelete(entry) { pendingDelete.value = entry }

async function doDelete() {
  if (!pendingDelete.value) return
  deleting.value = true
  const entry = pendingDelete.value
  try {
    if (entry._type === 'bp') await bpApi.delete(entry.id)
    else if (entry._type === 'symptom') await symptomApi.delete(entry.id)
    else if (entry._type === 'food') await foodApi.delete(entry.id)
    else if (entry._type === 'gym') await gymApi.delete(entry.id)
    allEntries.value = allEntries.value.filter(e => !(e.id === entry.id && e._type === entry._type))
    pendingDelete.value = null
    toast('Entry deleted')
  } catch { toast('Failed to delete', 'error') } finally { deleting.value = false }
}

async function saveEdit() {
  if (!editFormRef.value || !editEntry.value) return
  saving.value = true
  editError.value = ''
  try {
    const data = editFormRef.value.getFormData()
    const id = editEntry.value.id
    let updated
    if (editEntry.value._type === 'bp') updated = (await bpApi.update(id, data)).data
    else if (editEntry.value._type === 'symptom') updated = (await symptomApi.update(id, data)).data
    else if (editEntry.value._type === 'food') updated = (await foodApi.update(id, data)).data
    else if (editEntry.value._type === 'gym') updated = (await gymApi.update(id, data)).data
    const idx = allEntries.value.findIndex(e => e.id === id && e._type === editEntry.value._type)
    if (idx !== -1) allEntries.value[idx] = { ...updated, _type: editEntry.value._type }
    editEntry.value = null
    toast('Entry updated')
  } catch (e) {
    editError.value = e.response?.data?.detail || 'Failed to save changes'
  } finally { saving.value = false }
}

async function generateSummary() {
  summaryLoading.value = true
  try {
    const { data } = await summariesApi.generateWeekly(isoWeek.value)
    summary.value = data.content || data.summary
    toast("Summary generated")
  } catch { toast("Failed to generate", "error") } finally { summaryLoading.value = false }
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

async function exportWeek() {
  try {
    const s = format(currentWeekStart.value, "yyyy-MM-dd")
    const e = format(endOfWeek(currentWeekStart.value, { weekStartsOn: 1 }), "yyyy-MM-dd")
    const { data } = await exportApi.pdf({ type: "weekly", start_date: s, end_date: e, include_summary: true })
    const url = URL.createObjectURL(data)
    const a = document.createElement("a"); a.href = url; a.download = "week-log.pdf"; a.click()
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
