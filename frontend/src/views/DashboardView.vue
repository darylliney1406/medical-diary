<template>
  <div class="max-w-2xl mx-auto px-4 py-6 space-y-5">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Good {{ greeting }}, {{ firstName }}</h1>
      <p class="text-gray-500 text-sm mt-0.5">{{ formattedDate }}</p>
    </div>

    <div v-if="entries.latestBP" class="card">
      <p class="text-xs font-medium uppercase tracking-wide text-gray-400 mb-1">Latest Blood Pressure</p>
      <div class="flex items-end gap-3">
        <span class="text-4xl font-bold text-gray-900">{{ entries.latestBP.systolic }}/{{ entries.latestBP.diastolic }}</span>
        <span class="text-lg text-gray-500 mb-1">{{ entries.latestBP.pulse }} bpm</span>
      </div>
      <BPBadge :systolic="entries.latestBP.systolic" :diastolic="entries.latestBP.diastolic" class="mt-2" />
    </div>
    <div v-else class="card border-2 border-dashed border-gray-200 text-center py-6">
      <p class="text-sm text-gray-500">No BP readings yet</p>
      <button @click="router.push('/new-entry?type=bp')" class="btn-primary mt-3 text-sm px-4 py-2">Record first reading</button>
    </div>

    <div>
      <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">Quick add</h2>
      <div class="grid grid-cols-4 gap-2">
        <button v-for="q in quickAdd" :key="q.type" @click="router.push('/new-entry?type=' + q.type)"
          class="flex flex-col items-center gap-1.5 py-3 rounded-xl border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-all">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center" :class="q.iconBg">
            <component :is="q.icon" class="w-4 h-4" :class="q.iconColor" />
          </div>
          <span class="text-xs font-medium text-gray-600">{{ q.label }}</span>
        </button>
      </div>
    </div>

    <!-- Today's AI Summary -->
    <div class="card">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <Sparkles class="w-4 h-4 text-indigo-600" />
          <h2 class="text-sm font-semibold text-gray-900">Today's AI Summary</h2>
        </div>
        <button v-if="!dailySummary && !summaryLoading" @click="generateSummary" class="text-xs text-indigo-600 font-medium">Generate</button>
        <Loader2 v-if="summaryLoading" class="w-4 h-4 animate-spin text-indigo-400" />
      </div>
      <div v-if="dailySummary" class="markdown-content" v-html="renderMarkdown(dailySummary)"></div>
      <p v-else class="text-sm text-gray-400 italic">No summary yet for today. Click Generate.</p>
    </div>

    <!-- Recent entries — grouped by category -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wide">Recent entries</h2>
        <RouterLink to="/daily-log" class="text-xs text-indigo-600 font-medium">View all</RouterLink>
      </div>

      <div v-if="loading" class="space-y-3">
        <div v-for="i in 4" :key="i" class="h-20 bg-gray-100 rounded-xl animate-pulse"></div>
      </div>

      <div v-else-if="hasAnyEntries" class="space-y-1">
        <div v-for="cat in categories" :key="cat.key">
          <div v-if="cat.entries.length">
            <!-- Category header -->
            <button
              class="w-full flex items-center justify-between py-2 px-1 rounded-lg hover:bg-gray-50 transition-colors"
              @click="toggleCat(cat.key)"
            >
              <div class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-md flex items-center justify-center" :class="cat.bg">
                  <component :is="cat.icon" class="w-3.5 h-3.5" :class="cat.color" />
                </div>
                <span class="text-sm font-semibold text-gray-700">{{ cat.label }}</span>
                <span class="text-xs text-gray-400">({{ cat.entries.length }})</span>
              </div>
              <ChevronDown class="w-4 h-4 text-gray-400 transition-transform" :class="collapsedCats[cat.key] ? 'rotate-180' : ''" />
            </button>
            <div v-if="!collapsedCats[cat.key]" class="space-y-2 mb-2 pl-2 border-l-2 border-gray-100">
              <EntryCard
                v-for="entry in cat.entries"
                :key="entry.id"
                :entry="entry"
                :type="cat.key"
                @view="openDetail(entry)"
                @edit="openEdit(entry)"
                @delete="confirmDelete(entry)"
              />
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-8 text-gray-400">
        <BookOpen class="w-10 h-10 mx-auto mb-2 opacity-40" />
        <p class="text-sm">No entries yet. Start by adding your first reading.</p>
      </div>
    </div>
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
            <CalendarIcon class="w-4 h-4" />
            <span>{{ detailEntry.entry_date }}</span>
            <span v-if="detailEntry.entry_time">· {{ String(detailEntry.entry_time).slice(0,5) }}</span>
          </div>
          <!-- BP detail -->
          <template v-if="detailEntry._type === 'bp'">
            <div v-for="(r, i) in detailEntry.readings" :key="i" class="bg-gray-50 rounded-xl p-3">
              <p class="text-xs font-medium text-gray-500 mb-1">Reading {{ i + 1 }} · {{ String(r.recorded_at).slice(11,16) }}</p>
              <p class="text-2xl font-bold text-gray-900">{{ r.systolic }}/{{ r.diastolic }} <span class="text-base font-normal text-gray-500">{{ r.pulse }} bpm</span></p>
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
import { ref, computed, onMounted } from "vue"
import { useRouter, RouterLink } from "vue-router"
import { format } from "date-fns"
import {
  Sparkles, Loader2, BookOpen, Heart, Thermometer, Utensils, Dumbbell,
  ChevronDown, Trash2, Pencil, X, Calendar as CalendarIcon,
  Activity, Pill, UtensilsCrossed,
} from "lucide-vue-next"
import { useAuthStore } from "@/stores/auth"
import { useEntriesStore } from "@/stores/entries"
import { useToast } from "@/composables/useToast"
import { summariesApi } from "@/api"
import BPBadge from "@/components/BPBadge.vue"
import EntryCard from "@/components/EntryCard.vue"
import BPForm from "@/components/BPForm.vue"
import SymptomForm from "@/components/SymptomForm.vue"
import FoodForm from "@/components/FoodForm.vue"
import GymForm from "@/components/GymForm.vue"

const router = useRouter()
const auth = useAuthStore()
const entries = useEntriesStore()
const { toast } = useToast()
const loading = ref(false)
const dailySummary = ref(null)
const summaryLoading = ref(false)
const todayDate = format(new Date(), "yyyy-MM-dd")
const collapsedCats = ref({ bp: true, symptom: true, food: true, gym: true })

const pendingDelete = ref(null)
const deleting = ref(false)
const detailEntry = ref(null)
const editEntry = ref(null)
const editFormRef = ref(null)
const editError = ref('')
const saving = ref(false)

const quickAdd = [
  { type: "bp", label: "BP", icon: Heart, iconBg: "bg-blue-100", iconColor: "text-blue-600" },
  { type: "symptom", label: "Feeling", icon: Thermometer, iconBg: "bg-orange-100", iconColor: "text-orange-600" },
  { type: "food", label: "Food", icon: Utensils, iconBg: "bg-green-100", iconColor: "text-green-600" },
  { type: "gym", label: "Gym", icon: Dumbbell, iconBg: "bg-purple-100", iconColor: "text-purple-600" },
]

const categories = computed(() => [
  {
    key: 'bp',
    label: 'Blood Pressure',
    icon: Activity,
    bg: 'bg-blue-100',
    color: 'text-blue-600',
    entries: entries.bpEntries.slice(0, 3).map(e => ({ ...e, _type: 'bp' })),
  },
  {
    key: 'symptom',
    label: 'How I am feeling',
    icon: Pill,
    bg: 'bg-orange-100',
    color: 'text-orange-600',
    entries: entries.symptomEntries.slice(0, 3).map(e => ({ ...e, _type: 'symptom' })),
  },
  {
    key: 'food',
    label: 'Food & Drink',
    icon: UtensilsCrossed,
    bg: 'bg-green-100',
    color: 'text-green-600',
    entries: entries.foodEntries.slice(0, 3).map(e => ({ ...e, _type: 'food' })),
  },
  {
    key: 'gym',
    label: 'Gym',
    icon: Dumbbell,
    bg: 'bg-purple-100',
    color: 'text-purple-600',
    entries: entries.gymEntries.slice(0, 2).map(e => ({ ...e, _type: 'gym' })),
  },
])

const hasAnyEntries = computed(() => categories.value.some(c => c.entries.length > 0))

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return "morning"
  if (h < 17) return "afternoon"
  return "evening"
})
const firstName = computed(() => (auth.user?.name || "there").split(" ")[0])
const formattedDate = computed(() => format(new Date(), "EEEE, d MMMM yyyy"))

const detailTypeLabel = computed(() => {
  if (!detailEntry.value) return ''
  return { bp: 'Blood Pressure', symptom: 'How I am feeling', food: 'Food', gym: 'Gym' }[detailEntry.value._type] || ''
})
const editFormComponent = computed(() => {
  if (!editEntry.value) return null
  return { bp: BPForm, symptom: SymptomForm, food: FoodForm, gym: GymForm }[editEntry.value._type] || null
})

onMounted(async () => {
  loading.value = true
  await Promise.allSettled([
    entries.fetchBP({ limit: 5 }),
    entries.fetchSymptoms({ limit: 5 }),
    entries.fetchFood({ limit: 5 }),
    entries.fetchGym({ limit: 3 }),
  ])
  loading.value = false
  loadSummary()
})

async function loadSummary() {
  try {
    const { data } = await summariesApi.getDaily(todayDate)
    dailySummary.value = data.content || data.summary
  } catch { /* no summary yet */ }
}

async function generateSummary() {
  summaryLoading.value = true
  try {
    const { data } = await summariesApi.generateDaily(todayDate)
    dailySummary.value = data.content || data.summary
    toast("Summary generated")
  } catch {
    toast("Failed to generate summary", "error")
  } finally { summaryLoading.value = false }
}

function toggleCat(key) {
  collapsedCats.value[key] = !collapsedCats.value[key]
}

function openDetail(entry) { detailEntry.value = entry }
function openEdit(entry) { editEntry.value = { ...entry }; editError.value = '' }
function confirmDelete(entry) { pendingDelete.value = entry }

async function doDelete() {
  if (!pendingDelete.value) return
  deleting.value = true
  const entry = pendingDelete.value
  try {
    if (entry._type === 'bp') await entries.deleteBP(entry.id)
    else if (entry._type === 'symptom') await entries.deleteSymptom(entry.id)
    else if (entry._type === 'food') await entries.deleteFood(entry.id)
    else if (entry._type === 'gym') await entries.deleteGym(entry.id)
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
    if (editEntry.value._type === 'bp') await entries.updateBP(id, data)
    else if (editEntry.value._type === 'symptom') await entries.updateSymptom(id, data)
    else if (editEntry.value._type === 'food') await entries.updateFood(id, data)
    else if (editEntry.value._type === 'gym') await entries.updateGym(id, data)
    editEntry.value = null
    toast('Entry updated')
  } catch (e) {
    editError.value = e.response?.data?.detail || 'Failed to save changes'
  } finally { saving.value = false }
}

function renderMarkdown(md) {
  if (!md) return ''
  let html = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^---+$/gm, '<hr>')
  html = html.replace(/\n\n+/g, '</p><p class="mt-2">').replace(/\n/g, '<br>')
  return `<p>${html}</p>`
}
</script>

<style scoped>
.markdown-content :deep(h1) { @apply text-base font-bold text-gray-900 mt-3 mb-1; }
.markdown-content :deep(h2) { @apply text-sm font-bold text-gray-800 mt-2 mb-1; }
.markdown-content :deep(h3) { @apply text-sm font-semibold text-gray-700 mt-2 mb-0.5; }
.markdown-content :deep(p)  { @apply text-sm text-gray-700; }
.markdown-content :deep(strong) { @apply font-semibold; }
.markdown-content :deep(hr)  { @apply border-gray-200 my-2; }
</style>
