import axios from 'axios'
import { useAuthStore } from './store/auth'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token && config.headers) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = useAuthStore.getState().refreshToken
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL}/auth/refresh`,
          { refresh_token: refreshToken }
        )

        const { access_token, refresh_token } = response.data
        useAuthStore.getState().setTokens(access_token, refresh_token)

        if (originalRequest.headers) {
          originalRequest.headers['Authorization'] = `Bearer ${access_token}`
        }
        return apiClient(originalRequest)
      } catch (refreshError) {
        useAuthStore.getState().logout()
        window.location.href = '/'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// Dashboard functions
export const getDashboardOverview = async () => {
  const { data } = await apiClient.get('/dashboard/overview')
  return data
}

export const getEventTimeline = async (hours: number = 24) => {
  const { data } = await apiClient.get('/dashboard/timeline', {
    params: { hours },
  })
  return data
}

export const getAgentsStats = async () => {
  const { data } = await apiClient.get('/dashboard/stats/agents')
  return data
}

export const getClassificationStats = async () => {
  const { data } = await apiClient.get('/dashboard/stats/classification')
  return data
}

// Stats functions (aliases for backwards compatibility)
export const getStats = async () => {
  const { data } = await apiClient.get('/events/stats/summary')
  return data
}

export const getEventTimeSeries = async (params?: any) => {
  const { data } = await apiClient.get('/events/timeline', { params })
  return data
}

export const getEventsByType = async () => {
  const { data } = await apiClient.get('/events/stats/by-type')
  return data
}

export const getEventsBySeverity = async () => {
  const { data } = await apiClient.get('/events/stats/by-severity')
  return data
}

// Agents functions
export const getAgents = async (params?: any) => {
  const { data } = await apiClient.get('/agents', { params })
  return data
}

export const getAgent = async (agentId: string) => {
  const { data } = await apiClient.get(`/agents/${agentId}`)
  return data
}

export const createAgent = async (agent: any) => {
  const { data } = await apiClient.post('/agents', agent)
  return data
}

export const deleteAgent = async (agentId: string) => {
  const { data } = await apiClient.delete(`/agents/${agentId}`)
  return data
}

export const getAgentsSummary = async () => {
  const { data} = await apiClient.get('/agents/stats/summary')
  return data
}

// Events functions
export const getEvents = async (params?: any) => {
  const { data } = await apiClient.get('/events', { params })
  return data
}

export const searchEvents = async (params?: any) => {
  const { data } = await apiClient.get('/events/search', { params })
  return data
}

export const getEvent = async (eventId: string) => {
  const { data } = await apiClient.get(`/events/${eventId}`)
  return data
}

export const getEventStats = async () => {
  const { data } = await apiClient.get('/events/stats/summary')
  return data
}

// Classification functions
export const getClassifiedFiles = async (params?: any) => {
  const { data } = await apiClient.get('/classification/files', { params })
  return data
}

export const getClassifiedFile = async (fileId: string) => {
  const { data } = await apiClient.get(`/classification/files/${fileId}`)
  return data
}

export const getClassificationSummary = async () => {
  const { data } = await apiClient.get('/classification/stats/summary')
  return data
}

export const getClassificationByType = async () => {
  const { data } = await apiClient.get('/classification/stats/by-type')
  return data
}

export const getDetectionPatterns = async () => {
  const { data } = await apiClient.get('/classification/patterns')
  return data
}

// Policies functions
export const getPolicies = async (params?: any) => {
  const { data } = await apiClient.get('/policies', { params })
  return data
}

export const getPolicy = async (policyId: string) => {
  const { data } = await apiClient.get(`/policies/${policyId}`)
  return data
}

export const createPolicy = async (policy: any) => {
  const { data } = await apiClient.post('/policies', policy)
  return data
}

export const updatePolicy = async (policyId: string, policy: any) => {
  const { data } = await apiClient.put(`/policies/${policyId}`, policy)
  return data
}

export const deletePolicy = async (policyId: string) => {
  const { data } = await apiClient.delete(`/policies/${policyId}`)
  return data
}

export const getPolicyStats = async () => {
  const { data } = await apiClient.get('/policies/stats/summary')
  return data
}

// Users functions
export const getCurrentUser = async () => {
  const { data } = await apiClient.get('/users/me')
  return data
}

export const getUsers = async (params?: any) => {
  const { data } = await apiClient.get('/users', { params })
  return data
}

export const getUser = async (userId: string) => {
  const { data } = await apiClient.get(`/users/${userId}`)
  return data
}

export const getUserStats = async () => {
  const { data } = await apiClient.get('/users/stats/summary')
  return data
}

// Alerts functions
export const getAlerts = async () => {
  const { data } = await apiClient.get('/alerts')
  return data
}

export const acknowledgeAlert = async (alertId: string) => {
  const { data } = await apiClient.post(`/alerts/${alertId}/acknowledge`)
  return data
}

export default apiClient
