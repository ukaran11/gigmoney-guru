import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (phone: string, password: string) =>
    api.post('/auth/login', { phone, password }),
  register: (phone: string, password: string, name: string, city?: string) =>
    api.post('/auth/register', { phone, password, name, city: city || 'Mumbai' }),
}

// User API
export const userAPI = {
  getProfile: () => api.get('/user/profile'),
  updateProfile: (data: { name?: string; preferred_language?: string }) =>
    api.put('/user/profile', data),
}

// State API (Dashboard)
export const stateAPI = {
  getToday: () => api.get('/state/today'),
  getForecast: (days?: number) => api.get(`/state/forecast${days ? `?days=${days}` : ''}`),
}

// Agent API
export const agentAPI = {
  runDaily: (mode?: string, targetDate?: string) =>
    api.post('/agent/run-daily', null, { params: { mode: mode || 'react', target_date: targetDate } }),
  runAgent: (agentName: string) => api.post(`/agent/run/${agentName}`),
  getDecisions: (limit?: number) => api.get('/agent/decisions', { params: { limit } }),
}

// Advances API
export const advancesAPI = {
  list: (status?: string, limit?: number) =>
    api.get('/advances/', { params: { status, limit } }),
  getAvailable: () => api.get('/advances/available'),
  request: (amount: number, reason?: string, dueDays?: number) =>
    api.post('/advances/request', { amount, reason, due_days: dueDays }),
  repay: (advanceId: string) => api.post(`/advances/${advanceId}/repay`),
  getStats: () => api.get('/advances/stats'),
}

// Goals API
export const goalsAPI = {
  list: (status?: string) => api.get('/goals/', { params: { status } }),
  create: (data: { name: string; emoji?: string; target_amount: number; target_date?: string; priority?: number }) =>
    api.post('/goals/', data),
  get: (goalId: string) => api.get(`/goals/${goalId}`),
  update: (goalId: string, data: { name?: string; target_amount?: number; status?: string }) =>
    api.put(`/goals/${goalId}`, data),
  contribute: (goalId: string, amount: number) =>
    api.post(`/goals/${goalId}/contribute`, null, { params: { amount } }),
  delete: (goalId: string) => api.delete(`/goals/${goalId}`),
}

// Chat API
export const chatAPI = {
  sendMessage: (message: string) => api.post('/chat/message', { message }),
  getHistory: (limit?: number, before?: string) =>
    api.get('/chat/history', { params: { limit, before } }),
  clearHistory: () => api.delete('/chat/history'),
  quickAction: (action: string) => api.post('/chat/quick-action', null, { params: { action } }),
}

// Demo API
export const demoAPI = {
  seedRavi: () => api.post('/demo/seed-ravi'),
  simulateDay: (scenario?: string) =>
    api.post('/demo/simulate-day', null, { params: { scenario } }),
  reset: () => api.delete('/demo/reset'),
}

export default api
