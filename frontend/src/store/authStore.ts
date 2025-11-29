import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authAPI, userAPI } from '../lib/api'

interface User {
  id: string
  phone: string
  email?: string
  name: string | null
  preferred_language: string
  onboarding_complete: boolean
}

interface AuthState {
  token: string | null
  user: User | null
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (phone: string, password: string) => Promise<void>
  register: (phone: string, password: string, name: string) => Promise<void>
  logout: () => void
  fetchProfile: () => Promise<void>
  updateProfile: (data: { name?: string; preferred_language?: string }) => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: localStorage.getItem('token'),
      user: null,
      isLoading: false,
      error: null,

      login: async (phone: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authAPI.login(phone, password)
          const { access_token, user_id, name } = response.data
          localStorage.setItem('token', access_token)
          set({ token: access_token, user: { id: user_id, phone, name, preferred_language: 'en', onboarding_complete: false }, isLoading: false })
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Login failed', 
            isLoading: false 
          })
          throw error
        }
      },

      register: async (phone: string, password: string, name: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authAPI.register(phone, password, name)
          const { access_token, user_id } = response.data
          localStorage.setItem('token', access_token)
          set({ token: access_token, user: { id: user_id, phone, name, preferred_language: 'en', onboarding_complete: false }, isLoading: false })
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Registration failed', 
            isLoading: false 
          })
          throw error
        }
      },

      logout: () => {
        localStorage.removeItem('token')
        set({ token: null, user: null })
      },

      fetchProfile: async () => {
        if (!get().token) return
        set({ isLoading: true })
        try {
          const response = await userAPI.getProfile()
          set({ user: response.data.user, isLoading: false })
        } catch (error: any) {
          set({ isLoading: false })
          if (error.response?.status === 401) {
            get().logout()
          }
        }
      },

      updateProfile: async (data) => {
        set({ isLoading: true, error: null })
        try {
          await userAPI.updateProfile(data)
          // Refresh profile
          await get().fetchProfile()
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Update failed', 
            isLoading: false 
          })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
      onRehydrateStorage: () => (state) => {
        // Ensure token is synced to localStorage after rehydration
        if (state?.token) {
          localStorage.setItem('token', state.token)
        }
      },
    }
  )
)
