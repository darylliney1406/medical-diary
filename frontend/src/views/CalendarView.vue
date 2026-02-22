<template>
  <div class="max-w-2xl mx-auto px-4 py-6">
    <div class="flex items-center justify-between mb-5">
      <h1 class="text-xl font-bold text-gray-900">Calendar</h1>
      <button @click="showExport = true" class="btn-secondary text-sm px-3 py-1.5">Export PDF</button>
    </div>
    <div class="flex items-center justify-between mb-4 card">
      <button @click="prevMonth" class="p-2 rounded-lg hover:bg-gray-100"><ChevronLeft class="w-5 h-5" /></button>
      <h2 class="font-semibold text-gray-900">{{ monthLabel }}</h2>
      <button @click="nextMonth" class="p-2 rounded-lg hover:bg-gray-100"><ChevronRight class="w-5 h-5" /></button>
    </div>
    <div class="card p-3">
      <div class="grid grid-cols-7 mb-2">
        <div v-for="d in dayHeaders" :key="d" class="text-center text-xs font-medium text-gray-400 py-1">{{ d }}</div>
      </div>
      <div v-if="loading" class="grid grid-cols-7 gap-1">
        <div v-for="i in 35" :key="i" class="h-12 bg-gray-100 rounded-lg animate-pulse"></div>
      </div>
      <div v-else class="grid grid-cols-7 gap-1">
        <div v-for="day in calendarDays" :key="day.key"
          class="min-h-12 p-1 rounded-lg cursor-pointer hover:bg-gray-50"
          :class="[!day.isCurrentMonth && 'opacity-30', day.isToday && 'ring-2 ring-indigo-500', selectedDay === day.date && 'bg-indigo-100']"
          @click="selectDay(day)"
        >
          <span class="text-xs font-medium" :class="day.isToday ? 'text-indigo-700' : 'text-gray-700'">{{ day.dayNum }}</span>
          <div class="flex flex-wrap gap-0.5 mt-0.5">
            <span v-if="day.counts && day.counts.bp" class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
            <span v-if="day.counts && day.counts.symptom" class="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
            <span v-if="day.counts && day.counts.food" class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            <span v-if="day.counts && day.counts.gym" class="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
          </div>
        </div>
      </div>
    </div>
    <div class="flex items-center gap-4 mt-3 text-xs text-gray-500">
      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-blue-500"></span> BP</span>
      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-orange-500"></span> Symptom</span>
      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-green-500"></span> Food</span>
      <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-purple-500"></span> Gym</span>
    </div>
    <div v-if="selectedDay" class="mt-4 card">
      <div class="flex items-center justify-between mb-3">
        <h3 class="font-semibold text-gray-900">{{ selectedDayLabel }}</h3>
        <button @click="selectedDay = null" class="text-gray-400 hover:text-gray-600"><X class="w-4 h-4" /></button>
      </div>
      <p v-if="dayEntries.loading" class="text-sm text-gray-400">Loading...</p>
      <div v-else-if="dayEntries.all.length" class="space-y-2">
        <EntryCard v-for="entry in dayEntries.all" :key="entry._type+entry.id"
          :entry="entry" :type="entry._type" @edit="handleEdit" @delete="handleDelete" />
      </div>
      <p v-else class="text-sm text-gray-400 text-center py-4">No entries for this day.</p>
    </div>
    <div v-if="showExport" class="fixed inset-0 z-50 flex items-end md:items-center justify-center p-4 bg-black/40" @click.self="showExport = false">
      <div class="w-full max-w-md bg-white rounded-2xl shadow-xl p-6">
        <h3 class="text-lg font-semibold mb-4">Export as PDF</h3>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div><label class="label">From</label><input v-model="exportForm.start_date" type="date" class="input-field" /></div>
            <div><label class="label">To</label><input v-model="exportForm.end_date" type="date" class="input-field" /></div>
          </div>
          <label class="flex items-center gap-2 text-sm">
            <input v-model="exportForm.include_summary" type="checkbox" class="rounded" />
            Include AI summary
          </label>
        </div>
        <div class="flex gap-3 mt-4">
          <button @click="showExport = false" class="btn-secondary flex-1">Cancel</button>
          <button @click="downloadPdf" class="btn-primary flex-1" :disabled="exporting">
            <span v-if="exporting">Exporting...</span><span v-else>Download PDF</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, getDay, parseISO, isToday } from 'date-fns'
import { ChevronLeft, ChevronRight, X } from 'lucide-vue-next'
import { calendarApi, bpApi, symptomApi, foodApi, gymApi, exportApi } from '@/api'
import { useToast } from '@/composables/useToast'
import EntryCard from '@/components/EntryCard.vue'

const { toast } = useToast()
const loading = ref(false)
const currentDate = ref(new Date())
const calData = ref([])
const selectedDay = ref(null)
const showExport = ref(false)
const exporting = ref(false)
const dayHeaders = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const dayEntries = ref({ loading: false, all: [] })
const exportForm = ref({ start_date: format(new Date(), 'yyyy-MM-01'), end_date: format(new Date(), 'yyyy-MM-dd'), include_summary: true })

const monthLabel = computed(() => format(currentDate.value, 'MMMM yyyy'))

const calendarDays = computed(() => {
  const start = startOfMonth(currentDate.value)
  const end = endOfMonth(currentDate.value)
  const days = eachDayOfInterval({ start, end })
  const startDow = (getDay(start) + 6) % 7
  const result = []
  for (let i = 0; i < startDow; i++) result.push({ key: 'pad-'+i, dayNum: '', isCurrentMonth: false, date: null, counts: {} })
  for (const d of days) {
    const dateStr = format(d, 'yyyy-MM-dd')
    const calDay = calData.value.find(x => x.date === dateStr)
    result.push({ key: dateStr, dayNum: d.getDate(), isCurrentMonth: true, isToday: isToday(d), date: dateStr, counts: calDay?.counts || {} })
  }
  while (result.length % 7 !== 0) result.push({ key: 'pad-end-'+result.length, dayNum: '', isCurrentMonth: false, date: null, counts: {} })
  return result
})

const selectedDayLabel = computed(() => {
  if (!selectedDay.value) return ''
  try { return format(parseISO(selectedDay.value), 'EEEE, d MMMM yyyy') } catch { return selectedDay.value }
})

onMounted(fetchCalendar)
watch(currentDate, fetchCalendar)

async function fetchCalendar() {
  loading.value = true
  try {
    const y = currentDate.value.getFullYear()
    const m = currentDate.value.getMonth() + 1
    const { data } = await calendarApi.getMonth(y, m)
    calData.value = data.days || data
  } catch { calData.value = [] } finally { loading.value = false }
}

function prevMonth() { const d = new Date(currentDate.value); d.setMonth(d.getMonth() - 1); currentDate.value = d }
function nextMonth() { const d = new Date(currentDate.value); d.setMonth(d.getMonth() + 1); currentDate.value = d }

async function selectDay(day) {
  if (!day.date) return
  selectedDay.value = day.date
  dayEntries.value = { loading: true, all: [] }
  try {
    const [bp, sym, food, gym] = await Promise.allSettled([
      bpApi.list({ start_date: day.date, end_date: day.date }),
      symptomApi.list({ start_date: day.date, end_date: day.date }),
      foodApi.list({ start_date: day.date, end_date: day.date }),
      gymApi.list({ start_date: day.date, end_date: day.date }),
    ])
    const all = [
      ...(bp.value?.data?.items || bp.value?.data || []).map(e => ({ ...e, _type: 'bp' })),
      ...(sym.value?.data?.items || sym.value?.data || []).map(e => ({ ...e, _type: 'symptom' })),
      ...(food.value?.data?.items || food.value?.data || []).map(e => ({ ...e, _type: 'food' })),
      ...(gym.value?.data?.items || gym.value?.data || []).map(e => ({ ...e, _type: 'gym' })),
    ]
    dayEntries.value = { loading: false, all }
  } catch { dayEntries.value = { loading: false, all: [] } }
}

function handleEdit(entry) { console.log('edit', entry) }
function handleDelete(entry) { dayEntries.value.all = dayEntries.value.all.filter(e => e.id !== entry.id) }

async function downloadPdf() {
  exporting.value = true
  try {
    const { data } = await exportApi.pdf({ type: 'full', ...exportForm.value })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a'); a.href = url; a.download = 'medidiary-export.pdf'; a.click()
    URL.revokeObjectURL(url)
    showExport.value = false
    toast('PDF exported')
  } catch { toast('Export failed', 'error') } finally { exporting.value = false }
}
</script>
