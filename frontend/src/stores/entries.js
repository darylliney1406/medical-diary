import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { bpApi, symptomApi, foodApi, gymApi } from '@/api'
import { format } from 'date-fns'

/**
 * Entries store - manages all diary entry types with pagination.
 */
export const useEntriesStore = defineStore('entries', () => {
  // BP
  const bpEntries = ref([])
  const bpLoading = ref(false)
  const bpTotal = ref(0)

  // Symptom
  const symptomEntries = ref([])
  const symptomLoading = ref(false)

  // Food
  const foodEntries = ref([])
  const foodLoading = ref(false)

  // Gym
  const gymEntries = ref([])
  const gymLoading = ref(false)

  // Combined recent entries for dashboard
  const recentEntries = computed(() => {
    const all = [
      ...bpEntries.value.map(e => ({ ...e, _type: 'bp' })),
      ...symptomEntries.value.map(e => ({ ...e, _type: 'symptom' })),
      ...foodEntries.value.map(e => ({ ...e, _type: 'food' })),
      ...gymEntries.value.map(e => ({ ...e, _type: 'gym' })),
    ]
    return all.sort((a, b) => new Date(b.entry_date) - new Date(a.entry_date)).slice(0, 5)
  })

  const latestBP = computed(() => {
    if (!bpEntries.value.length) return null
    const entry = bpEntries.value[0]
    if (!entry.readings?.length) return null
    return entry.readings[0]
  })

  /**
   * Fetch blood pressure entries.
   * @param {Object} params - Query params (start_date, end_date, page, limit)
   */
  async function fetchBP(params = {}) {
    bpLoading.value = true
    try {
      const { data } = await bpApi.list({ limit: 20, ...params })
      bpEntries.value = data.items || data
      bpTotal.value = data.total || data.length
    } finally {
      bpLoading.value = false
    }
  }

  async function createBP(payload) {
    const { data } = await bpApi.create(payload)
    bpEntries.value.unshift(data)
    return data
  }

  async function updateBP(id, payload) {
    const { data } = await bpApi.update(id, payload)
    const idx = bpEntries.value.findIndex(e => e.id === id)
    if (idx !== -1) bpEntries.value[idx] = data
    return data
  }

  async function deleteBP(id) {
    await bpApi.delete(id)
    bpEntries.value = bpEntries.value.filter(e => e.id !== id)
  }

  async function fetchSymptoms(params = {}) {
    symptomLoading.value = true
    try {
      const { data } = await symptomApi.list({ limit: 20, ...params })
      symptomEntries.value = data.items || data
    } finally {
      symptomLoading.value = false
    }
  }

  async function createSymptom(payload) {
    const { data } = await symptomApi.create(payload)
    symptomEntries.value.unshift(data)
    return data
  }

  async function updateSymptom(id, payload) {
    const { data } = await symptomApi.update(id, payload)
    const idx = symptomEntries.value.findIndex(e => e.id === id)
    if (idx !== -1) symptomEntries.value[idx] = data
    return data
  }

  async function deleteSymptom(id) {
    await symptomApi.delete(id)
    symptomEntries.value = symptomEntries.value.filter(e => e.id !== id)
  }

  async function fetchFood(params = {}) {
    foodLoading.value = true
    try {
      const { data } = await foodApi.list({ limit: 20, ...params })
      foodEntries.value = data.items || data
    } finally {
      foodLoading.value = false
    }
  }

  async function createFood(payload) {
    const { data } = await foodApi.create(payload)
    foodEntries.value.unshift(data)
    return data
  }

  async function updateFood(id, payload) {
    const { data } = await foodApi.update(id, payload)
    const idx = foodEntries.value.findIndex(e => e.id === id)
    if (idx !== -1) foodEntries.value[idx] = data
    return data
  }

  async function deleteFood(id) {
    await foodApi.delete(id)
    foodEntries.value = foodEntries.value.filter(e => e.id !== id)
  }

  async function fetchGym(params = {}) {
    gymLoading.value = true
    try {
      const { data } = await gymApi.list({ limit: 20, ...params })
      gymEntries.value = data.items || data
    } finally {
      gymLoading.value = false
    }
  }

  async function createGym(payload) {
    const { data } = await gymApi.create(payload)
    gymEntries.value.unshift(data)
    return data
  }

  async function updateGym(id, payload) {
    const { data } = await gymApi.update(id, payload)
    const idx = gymEntries.value.findIndex(e => e.id === id)
    if (idx !== -1) gymEntries.value[idx] = data
    return data
  }

  async function deleteGym(id) {
    await gymApi.delete(id)
    gymEntries.value = gymEntries.value.filter(e => e.id !== id)
  }

  return {
    bpEntries, bpLoading, bpTotal,
    symptomEntries, symptomLoading,
    foodEntries, foodLoading,
    gymEntries, gymLoading,
    recentEntries, latestBP,
    fetchBP, createBP, updateBP, deleteBP,
    fetchSymptoms, createSymptom, updateSymptom, deleteSymptom,
    fetchFood, createFood, updateFood, deleteFood,
    fetchGym, createGym, updateGym, deleteGym,
  }
})
