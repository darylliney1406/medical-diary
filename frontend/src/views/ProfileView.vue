<template>
  <div class="max-w-2xl mx-auto px-4 py-6">
    <h1 class="text-xl font-bold text-gray-900 mb-5">Profile</h1>

    <!-- AI Data Banner -->
    <div class="mb-5 rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-sm">
      <div class="flex items-start gap-3">
        <Info class="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
        <div class="space-y-2">
          <p class="font-medium text-indigo-900">What gets shared with AI summaries</p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
            <div>
              <p class="text-xs font-semibold text-green-700 uppercase tracking-wide mb-1">Sent to AI</p>
              <ul class="text-xs text-gray-700 space-y-0.5">
                <li>✓ Age (calculated, not date of birth)</li>
                <li>✓ Allergies &amp; intolerances</li>
                <li>✓ Body metrics (height, weight, BMI, gender, activity level)</li>
                <li>✓ Diagnoses</li>
                <li>✓ Active medications</li>
              </ul>
            </div>
            <div>
              <p class="text-xs font-semibold text-red-600 uppercase tracking-wide mb-1">Never sent to AI</p>
              <ul class="text-xs text-gray-700 space-y-0.5">
                <li>✗ Date of birth</li>
                <li>✗ NHS number</li>
                <li>✗ Blood type</li>
                <li>✗ GP details</li>
                <li>✗ Emergency contact</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="flex overflow-x-auto gap-1 mb-5 pb-1">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors"
        :class="activeTab === tab.id ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Personal Details -->
    <div v-if="activeTab === 'identity'" class="card space-y-4">
      <h2 class="font-semibold text-gray-900">Personal Details</h2>
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="h-10 bg-gray-100 rounded-lg animate-pulse"></div>
      </div>
      <form v-else @submit.prevent="saveIdentity" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label class="label">Date of birth</label><input v-model="identity.date_of_birth" type="date" class="input-field" /></div>
          <div><label class="label">NHS number</label><input v-model="identity.nhs_number" type="text" class="input-field" placeholder="XXX XXX XXXX" /></div>
          <div><label class="label">Blood type</label>
            <select v-model="identity.blood_type" class="input-field">
              <option value="">Unknown</option>
              <option v-for="bt in bloodTypes" :key="bt" :value="bt">{{ bt }}</option>
            </select>
          </div>
          <div><label class="label">GP Name</label><input v-model="identity.gp_name" type="text" class="input-field" /></div>
          <div><label class="label">GP Surgery</label><input v-model="identity.gp_surgery" type="text" class="input-field" /></div>
          <div><label class="label">Emergency contact name</label><input v-model="identity.emergency_contact_name" type="text" class="input-field" placeholder="Name and relationship" /></div>
          <div><label class="label">Emergency contact phone</label><input v-model="identity.emergency_contact_phone" type="text" class="input-field" placeholder="Phone number" /></div>
        </div>
        <div><label class="label">Allergies</label><textarea v-model="identity.allergies" class="input-field" rows="2"></textarea></div>
        <div class="flex justify-end">
          <button type="submit" class="btn-primary" :disabled="saving">
            <Loader2 v-if="saving" class="w-4 h-4 animate-spin inline mr-1" />Save changes
          </button>
        </div>
      </form>
    </div>

    <!-- Body Metrics -->
    <div v-if="activeTab === 'metrics'" class="card space-y-4">
      <h2 class="font-semibold text-gray-900">Body Metrics</h2>
      <form @submit.prevent="saveMetrics" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div><label class="label">Height (cm)</label><input v-model.number="metrics.height_cm" type="number" class="input-field" /></div>
          <div><label class="label">Weight (kg)</label><input v-model.number="metrics.weight_kg" type="number" step="0.1" class="input-field" /></div>
        </div>
        <button type="submit" class="btn-primary">Add metrics</button>
      </form>
    </div>

    <!-- Diagnoses -->
    <div v-if="activeTab === 'diagnoses'" class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-gray-900">Diagnoses</h2>
        <button @click="showDiagnosisForm = true" class="btn-primary text-sm px-3 py-1.5">+ Add</button>
      </div>
      <div v-for="d in diagnoses" :key="d.id" class="card">
        <div class="flex items-start justify-between">
          <div>
            <p class="font-medium text-gray-900">{{ d.condition_name }}</p>
            <p class="text-sm text-gray-500 mt-0.5">{{ d.diagnosed_at }}</p>
            <p v-if="d.notes" class="text-sm text-gray-600 mt-1">{{ d.notes }}</p>
          </div>
          <button @click="deleteDiagnosis(d.id)" class="text-gray-300 hover:text-red-500"><Trash2 class="w-4 h-4" /></button>
        </div>
      </div>
      <div v-if="showDiagnosisForm" class="card">
        <form @submit.prevent="addDiagnosis" class="space-y-3">
          <div><label class="label">Condition name</label><input v-model="newDiagnosis.condition_name" type="text" class="input-field" required /></div>
          <div><label class="label">Diagnosed date</label><input v-model="newDiagnosis.diagnosed_at" type="date" class="input-field" /></div>
          <div><label class="label">Notes</label><textarea v-model="newDiagnosis.notes" class="input-field" rows="2"></textarea></div>
          <div class="flex gap-2">
            <button type="button" @click="showDiagnosisForm = false" class="btn-secondary flex-1">Cancel</button>
            <button type="submit" class="btn-primary flex-1">Add</button>
          </div>
        </form>
      </div>
      <p v-if="!diagnoses.length && !showDiagnosisForm" class="text-sm text-gray-400 text-center py-6">No diagnoses recorded.</p>
    </div>

    <!-- Medications -->
    <div v-if="activeTab === 'medications'" class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-gray-900">Medications</h2>
        <button @click="showMedForm = true" class="btn-primary text-sm px-3 py-1.5">+ Add</button>
      </div>
      <div v-for="med in medications" :key="med.id" class="card">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <p class="font-medium text-gray-900">{{ med.name }}</p>
              <span class="text-xs px-2 py-0.5 rounded-full" :class="med.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'">
                {{ med.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <p class="text-sm text-gray-500">{{ med.dosage }} {{ med.frequency }}</p>
          </div>
          <div class="flex gap-2">
            <button @click="toggleMedication(med)" class="text-gray-400 hover:text-green-500"><ToggleLeft class="w-5 h-5" /></button>
            <button @click="deleteMedication(med.id)" class="text-gray-300 hover:text-red-500"><Trash2 class="w-4 h-4" /></button>
          </div>
        </div>
      </div>
      <div v-if="showMedForm" class="card">
        <form @submit.prevent="addMedication" class="space-y-3">
          <div><label class="label">Medication name</label><input v-model="newMed.name" type="text" class="input-field" required /></div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="label">Dose</label><input v-model="newMed.dosage" type="text" class="input-field" placeholder="e.g. 10mg" /></div>
            <div><label class="label">Frequency</label><input v-model="newMed.frequency" type="text" class="input-field" placeholder="e.g. once daily" /></div>
          </div>
          <div class="flex gap-2">
            <button type="button" @click="showMedForm = false" class="btn-secondary flex-1">Cancel</button>
            <button type="submit" class="btn-primary flex-1">Add</button>
          </div>
        </form>
      </div>
      <p v-if="!medications.length && !showMedForm" class="text-sm text-gray-400 text-center py-6">No medications recorded.</p>
    </div>

    <!-- Account Settings -->
    <div v-if="activeTab === 'account'" class="card space-y-4">
      <h2 class="font-semibold text-gray-900">Account Settings</h2>
      <div class="border-t border-gray-100 pt-4">
        <h3 class="text-sm font-medium text-gray-700 mb-3">Change Password</h3>
        <form @submit.prevent="changePassword" class="space-y-3">
          <div><label class="label">Current password</label><input v-model="pwForm.current" type="password" class="input-field" /></div>
          <div><label class="label">New password</label><input v-model="pwForm.new" type="password" class="input-field" /></div>
          <div><label class="label">Confirm new password</label><input v-model="pwForm.confirm" type="password" class="input-field" /></div>
          <button type="submit" class="btn-primary">Update password</button>
        </form>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { Loader2, Trash2, ToggleLeft, Info } from 'lucide-vue-next'
import { profileApi } from '@/api'
import { useToast } from '@/composables/useToast'
const { toast } = useToast()
const loading = ref(false)
const saving = ref(false)
const activeTab = ref('identity')
const tabs = [
  { id: 'identity', label: 'Personal Details' },
  { id: 'metrics', label: 'Body Metrics' },
  { id: 'diagnoses', label: 'Diagnoses' },
  { id: 'medications', label: 'Medications' },
  { id: 'account', label: 'Account' },
]
const bloodTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const identity = ref({ date_of_birth: "", nhs_number: "", blood_type: "", gp_name: "", gp_surgery: "", allergies: "", emergency_contact_name: "", emergency_contact_phone: "" })
const metrics = ref({ height_cm: null, weight_kg: null })
const diagnoses = ref([])
const medications = ref([])
const showDiagnosisForm = ref(false)
const showMedForm = ref(false)
const newDiagnosis = ref({ condition_name: "", diagnosed_at: "", notes: "" })
const newMed = ref({ name: "", dosage: "", frequency: "", is_active: true })
const pwForm = ref({ current: "", new: "", confirm: "" })
onMounted(async () => {
  loading.value = true
  try {
    const { data } = await profileApi.get()
    if (data.identity) Object.assign(identity.value, data.identity)
    if (data.body_metrics) Object.assign(metrics.value, data.body_metrics)
    if (data.diagnoses) diagnoses.value = data.diagnoses
    if (data.medications) medications.value = data.medications
  } finally { loading.value = false }
})
async function saveIdentity() {
  saving.value = true
  try { await profileApi.updateIdentity(identity.value); toast("Saved") }
  catch { toast("Failed to save", "error") } finally { saving.value = false }
}
async function saveMetrics() {
  try { await profileApi.addBodyMetrics(metrics.value); toast("Metrics saved") }
  catch { toast("Failed", "error") }
}
async function addDiagnosis() {
  try {
    const { data } = await profileApi.addDiagnosis(newDiagnosis.value)
    diagnoses.value.push(data)
    newDiagnosis.value = { condition_name: "", diagnosed_at: "", notes: "" }
    showDiagnosisForm.value = false
    toast("Diagnosis added")
  } catch { toast("Failed", "error") }
}
async function deleteDiagnosis(id) {
  if (!confirm("Delete this diagnosis?")) return
  try { await profileApi.deleteDiagnosis(id); diagnoses.value = diagnoses.value.filter(d => d.id !== id); toast("Deleted") }
  catch { toast("Failed", "error") }
}
async function addMedication() {
  try {
    const { data } = await profileApi.addMedication(newMed.value)
    medications.value.push(data)
    newMed.value = { name: "", dosage: "", frequency: "", is_active: true }
    showMedForm.value = false
    toast("Medication added")
  } catch { toast("Failed", "error") }
}
async function toggleMedication(med) {
  try {
    const { data } = await profileApi.updateMedication(med.id, { is_active: !med.is_active })
    const idx = medications.value.findIndex(m => m.id === med.id)
    if (idx !== -1) medications.value[idx] = data
  } catch { toast("Failed", "error") }
}
async function deleteMedication(id) {
  if (!confirm("Delete this medication?")) return
  try { await profileApi.deleteMedication(id); medications.value = medications.value.filter(m => m.id !== id); toast("Deleted") }
  catch { toast("Failed", "error") }
}
async function changePassword() { toast("Password change not yet implemented", "info") }
</script>
