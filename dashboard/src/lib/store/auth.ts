import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import axios from 'axios'

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
    (set) => ({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      refreshToken: null,

      login: async (email: string, password: string) => {
        // Call real backend API
        const cleanEmail = email.trim()
        const cleanPassword = password.trim()

        try {
          // OAuth2 requires form data with username/password fields
          const formData = new URLSearchParams()
          formData.append('username', cleanEmail)
          formData.append('password', cleanPassword)

          const response = await axios.post('/api/v1/auth/login', formData, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          })

          const { access_token, refresh_token } = response.data

          // Decode token to get user info (simple base64 decode of JWT payload)
          const tokenPayload = JSON.parse(atob(access_token.split('.')[1]))

          set({
            isAuthenticated: true,
            accessToken: access_token,
            refreshToken: refresh_token,
            user: {
              email: tokenPayload.email || cleanEmail,
              role: tokenPayload.role || 'admin',
              id: tokenPayload.sub || 'unknown',
            },
          })
        } catch (error: any) {
          console.error('Login error:', error)
          if (error.response?.status === 401) {
            throw new Error('Invalid username or password')
          } else if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail)
          } else {
            throw new Error('Login failed. Please try again.')
          }
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
