import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

/** Axios instance with base URL and credentials for refresh cookie */
export const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

let _getToken = () => null
let _onUnauthorized = () => {}

/**
 * Configure the API module with store accessors.
 * @param {Object} opts
 * @param {() => string|null} opts.getToken
 * @param {() => void} opts.onUnauthorized
 */
export function configureApi({ getToken, onUnauthorized }) {
  _getToken = getToken
  _onUnauthorized = onUnauthorized
}

// Request interceptor: attach Authorization header
api.interceptors.request.use((config) => {
  const token = _getToken()
  if (token) {
    config.headers.Authorization = 'Bearer ' + token
  }
  return config
})

let refreshPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      if (!refreshPromise) {
        refreshPromise = api.post('/auth/refresh').finally(() => { refreshPromise = null })
      }
      try {
        const { data } = await refreshPromise
        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore()
        authStore.accessToken = data.access_token
        originalRequest.headers.Authorization = 'Bearer ' + data.access_token
        return api(originalRequest)
      } catch {
        _onUnauthorized()
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  validateMfa: (mfa_token, code) => api.post('/auth/mfa/validate', { mfa_token, code }),
  refresh: () => api.post('/auth/refresh'),
  logout: () => api.post('/auth/logout'),
}

export const profileApi = {
  get: () => api.get('/profile'),
  updateIdentity: (data) => api.patch('/profile/identity', data),
  addBodyMetrics: (data) => api.post('/profile/body-metrics', data),
  getDiagnoses: () => api.get('/profile/diagnoses'),
  addDiagnosis: (data) => api.post('/profile/diagnoses', data),
  updateDiagnosis: (id, data) => api.patch('/profile/diagnoses/' + id, data),
  deleteDiagnosis: (id) => api.delete('/profile/diagnoses/' + id),
  getMedications: () => api.get('/profile/medications'),
  addMedication: (data) => api.post('/profile/medications', data),
  updateMedication: (id, data) => api.patch('/profile/medications/' + id, data),
  deleteMedication: (id) => api.delete('/profile/medications/' + id),
}

export const tagsApi = {
  list: () => api.get('/tags'),
  create: (data) => api.post('/tags', data),
  update: (id, data) => api.patch('/tags/' + id, data),
  delete: (id) => api.delete('/tags/' + id),
}

export const bpApi = {
  list: (params) => api.get('/entries/bp', { params }),
  create: (data) => api.post('/entries/bp', data),
  update: (id, data) => api.patch('/entries/bp/' + id, data),
  delete: (id) => api.delete('/entries/bp/' + id),
}

export const symptomApi = {
  list: (params) => api.get('/entries/symptom', { params }),
  create: (data) => api.post('/entries/symptom', data),
  update: (id, data) => api.patch('/entries/symptom/' + id, data),
  delete: (id) => api.delete('/entries/symptom/' + id),
}

export const foodApi = {
  list: (params) => api.get('/entries/food', { params }),
  create: (data) => api.post('/entries/food', data),
  update: (id, data) => api.patch('/entries/food/' + id, data),
  delete: (id) => api.delete('/entries/food/' + id),
}

export const gymApi = {
  list: (params) => api.get('/entries/gym', { params }),
  create: (data) => api.post('/entries/gym', data),
  update: (id, data) => api.patch('/entries/gym/' + id, data),
  delete: (id) => api.delete('/entries/gym/' + id),
}

export const catalogueApi = {
  search: (params) => api.get('/catalogue', { params }),
  create: (data) => api.post('/catalogue', data),
  update: (id, data) => api.patch('/catalogue/' + id, data),
  delete: (id) => api.delete('/catalogue/' + id),
}

export const calendarApi = {
  getMonth: (year, month) => api.get('/calendar/' + year + '/' + month),
}

export const summariesApi = {
  getDaily: (date) => api.get('/summaries/daily/' + date),
  generateDaily: (date) => api.post('/summaries/daily/' + date + '/generate'),
  getWeekly: (isoWeek) => api.get('/summaries/weekly/' + isoWeek),
  generateWeekly: (isoWeek) => api.post('/summaries/weekly/' + isoWeek + '/generate'),
}

export const exportApi = {
  pdf: (data) => api.post('/export/pdf', data, { responseType: 'blob' }),
}

export const usersApi = {
  list: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.patch('/users/' + id, data),
  deactivate: (id) => api.post('/users/' + id + '/deactivate'),
  activate: (id) => api.post('/users/' + id + '/activate'),
  requestPasswordReset: (id) => api.post('/users/' + id + '/request-password-reset'),
}
