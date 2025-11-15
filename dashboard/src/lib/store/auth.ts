import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:55000/api/v1'

interface AuthState {
  isAuthenticated: boolean
  user: {
    email: string
    role: string
    id: string
  } | null
  accessToken: string | null
  refreshToken: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setTokens: (accessToken: string, refreshToken: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      refreshToken: null,

      login: async (email: string, password: string) => {
        // Trim whitespace from inputs
        const cleanEmail = email.trim()
        const cleanPassword = password.trim()

        try {
          // Call the real API login endpoint
          // OAuth2PasswordRequestForm expects form data
          const formData = new URLSearchParams()
          formData.append('username', cleanEmail)
          formData.append('password', cleanPassword)

          const response = await axios.post(
            `${API_URL}/auth/login`,
            formData,
            {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
            }
          )

          const { access_token, refresh_token } = response.data

          // Get user info from token (decode JWT)
          // For now, we'll set basic user info - in production, decode the token
          set({
            isAuthenticated: true,
            accessToken: access_token,
            refreshToken: refresh_token,
            user: {
              email: cleanEmail,
              role: 'admin', // Will be decoded from token in production
              id: 'user-001', // Will be decoded from token in production
            },
          })
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Invalid email or password'
          throw new Error(errorMessage)
        }
      },

      logout: () => {
        set({
          isAuthenticated: false,
          user: null,
          accessToken: null,
          refreshToken: null,
        })
      },

      setTokens: (accessToken: string, refreshToken: string) => {
        set({ accessToken, refreshToken })
      },
    }),
    {
      name: 'dlp-auth-v2',
    }
  )
)
