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
          <component :is="q.icon" class="w-6 h-6" />
          <span class="text-xs font-medium text-gray-600">{{ q.label }}</span>
        </button>
      </div>
    </div>

    <div class="card">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <Sparkles class="w-4 h-4 text-indigo-600" />
          <h2 class="text-sm font-semibold text-gray-900">Today's AI Summary</h2>
        </div>
        <button v-if="!dailySummary" @click="generateSummary" class="text-xs text-indigo-600 font-medium">Generate</button>
        <Loader2 v-if="summaryLoading" class="w-4 h-4 animate-spin text-indigo-400" />
      </div>
      <p v-if="dailySummary" class="text-sm text-gray-700 leading-relaxed">{{ dailySummary }}</p>
      <p v-else class="text-sm text-gray-400 italic">No summary yet for today. Click Generate.</p>
    </div>

    <div>
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wide">Recent entries</h2>
        <RouterLink to="/daily-log" class="text-xs text-indigo-600 font-medium">View all</RouterLink>
      </div>
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 3" :key="i" class="h-20 bg-gray-100 rounded-xl animate-pulse"></div>
      </div>
      <div v-else-if="entries.recentEntries.length" class="space-y-3">
        <EntryCard v-for="entry in entries.recentEntries" :key="entry._type + entry.id"
          :entry="entry" :type="entry._type" @edit="handleEdit" @delete="handleDelete" />
      </div>
      <div v-else class="text-center py-8 text-gray-400">
        <BookOpen class="w-10 h-10 mx-auto mb-2 opacity-40" />
        <p class="text-sm">No entries yet. Start by adding your first reading.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter, RouterLink } from "vue-router"
import { format } from "date-fns"
import { Activity, Sparkles, Loader2, BookOpen, Heart, Thermometer, Utensils, Dumbbell } from "lucide-vue-next"
import { useAuthStore } from "@/stores/auth"
import { useEntriesStore } from "@/stores/entries"
import { useToast } from "@/composables/useToast"
import { getBPCategory } from "@/composables/useBPCategory"
import { summariesApi } from "@/api"
import BPBadge from "@/components/BPBadge.vue"
import EntryCard from "@/components/EntryCard.vue"

const router = useRouter()
const auth = useAuthStore()
const entries = useEntriesStore()
const { toast } = useToast()
const loading = ref(false)
const dailySummary = ref(null)
const summaryLoading = ref(false)
const todayDate = format(new Date(), "yyyy-MM-dd")

const quickAdd = [
  { type: "bp", label: "BP", icon: Heart },
  { type: "symptom", label: "Symptom", icon: Thermometer },
  { type: "food", label: "Food", icon: Utensils },
  { type: "gym", label: "Gym", icon: Dumbbell },
]

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return "morning"
  if (h < 17) return "afternoon"
  return "evening"
})

const firstName = computed(() => (auth.user?.name || "there").split(" ")[0])
const formattedDate = computed(() => format(new Date(), "EEEE, d MMMM yyyy"))

onMounted(async () => {
  loading.value = true
  await Promise.allSettled([
    entries.fetchBP({ limit: 5 }),
    entries.fetchSymptoms({ limit: 5 }),
    entries.fetchFood({ limit: 3 }),
    entries.fetchGym({ limit: 2 }),
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

async function handleEdit(entry) {
  router.push("/new-entry?type=" + entry._type + "&id=" + entry.id)
}

async function handleDelete(entry) {
  if (!confirm("Delete this entry?")) return
  const actions = { bp: entries.deleteBP, symptom: entries.deleteSymptom, food: entries.deleteFood, gym: entries.deleteGym }
  try { await actions[entry._type](entry.id); toast("Deleted") }
  catch { toast("Failed to delete", "error") }
}
</script>
