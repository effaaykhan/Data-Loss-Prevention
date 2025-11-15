import axios from 'axios'
import { useAuthStore } from './store/auth'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:55000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
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
          `${import.meta.env.VITE_API_URL || 'http://localhost:55000/api/v1'}/auth/refresh`,
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

// Helper functions for Dashboard
export const getStats = async () => {
  const { data } = await apiClient.get('/dashboard/overview')
  return data
}

export const getEventTimeSeries = async (params?: { interval?: string; hours?: number }) => {
  const { data } = await apiClient.get('/dashboard/timeline', {
    params: params || { hours: 24 },
  })
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

// Export individual functions for direct imports
export const getAgents = async (params?: any) => {
  const { data } = await apiClient.get('/agents', { params })
  return data
}

export const deleteAgent = async (agentId: string) => {
  const { data } = await apiClient.delete(`/agents/${agentId}`)
  return data
}

// Additional exports for direct imports
export const getAlerts = async () => {
  const { data } = await apiClient.get('/alerts')
  return data
}

export const searchEvents = async (params?: any) => {
  const { data } = await apiClient.get('/events', { params })
  return data
}

// Type exports
export type Agent = {
  id?: string
  agent_id: string
  name: string
  os: string
  ip_address: string
  status: string
  last_seen: string
  created_at: string
  version?: string
  hostname?: string
  os_version?: string
  capabilities?: Record<string, boolean>
}

export type Event = {
  id: string
  agent_id: string
  event_type: string
  severity: string
  classification_score?: number
  classification_labels?: string[]
  classification_type?: string
  file_path?: string
  timestamp: string | Date
  content?: string
  blocked?: boolean
  policy_id?: string | null
  action_taken?: string
  destination?: string | null
  source?: string
  user_email?: string
}

export const api = {
  // Dashboard
  getDashboardOverview: async () => {
    const { data } = await apiClient.get('/dashboard/overview')
    return data
  },

  getEventTimeline: async (hours: number = 24) => {
    const { data } = await apiClient.get('/dashboard/timeline', {
      params: { hours },
    })
    return data
  },

  getAgentsStats: async () => {
    const { data } = await apiClient.get('/dashboard/stats/agents')
    return data
  },

  getClassificationStats: async () => {
    const { data } = await apiClient.get('/dashboard/stats/classification')
    return data
  },

  // Agents
  getAgents: async (params?: any) => {
    const { data } = await apiClient.get('/agents', { params })
    return data
  },

  getAgent: async (agentId: string) => {
    const { data } = await apiClient.get(`/agents/${agentId}`)
    return data
  },

  createAgent: async (agent: any) => {
    const { data } = await apiClient.post('/agents', agent)
    return data
  },

  deleteAgent: async (agentId: string) => {
    const { data } = await apiClient.delete(`/agents/${agentId}`)
    return data
  },

  getAgentsSummary: async () => {
    const { data} = await apiClient.get('/agents/stats/summary')
    return data
  },

  // Events
  getEvents: async (params?: any) => {
    const { data } = await apiClient.get('/events', { params })
    return data
  },

  getEvent: async (eventId: string) => {
    const { data } = await apiClient.get(`/events/${eventId}`)
    return data
  },

  getEventStats: async () => {
    const { data } = await apiClient.get('/events/stats/summary')
    return data
  },

  // Classification
  getClassifiedFiles: async (params?: any) => {
    const { data } = await apiClient.get('/classification/files', { params })
    return data
  },

  getClassifiedFile: async (fileId: string) => {
    const { data } = await apiClient.get(`/classification/files/${fileId}`)
    return data
  },

  getClassificationSummary: async () => {
    const { data } = await apiClient.get('/classification/stats/summary')
    return data
  },

  getClassificationByType: async () => {
    const { data } = await apiClient.get('/classification/stats/by-type')
    return data
  },

  getDetectionPatterns: async () => {
    const { data } = await apiClient.get('/classification/patterns')
    return data
  },

  // Policies
  getPolicies: async (params?: any) => {
    const { data } = await apiClient.get('/policies', { params })
    return data
  },

  getPolicy: async (policyId: string) => {
    const { data } = await apiClient.get(`/policies/${policyId}`)
    return data
  },

  createPolicy: async (policy: any) => {
    const { data } = await apiClient.post('/policies', policy)
    return data
  },

  updatePolicy: async (policyId: string, policy: any) => {
    const { data } = await apiClient.put(`/policies/${policyId}`, policy)
    return data
  },

  deletePolicy: async (policyId: string) => {
    const { data } = await apiClient.delete(`/policies/${policyId}`)
    return data
  },

  getPolicyStats: async () => {
    const { data } = await apiClient.get('/policies/stats/summary')
    return data
  },

  // Users
  getCurrentUser: async () => {
    const { data } = await apiClient.get('/users/me')
    return data
  },

  getUsers: async (params?: any) => {
    const { data } = await apiClient.get('/users', { params })
    return data
  },

  getUser: async (userId: string) => {
    const { data } = await apiClient.get(`/users/${userId}`)
    return data
  },

  getUserStats: async () => {
    const { data } = await apiClient.get('/users/stats/summary')
    return data
  },

  // Alerts
  getAlerts: async () => {
    const { data } = await apiClient.get('/alerts')
    return data
  },

  acknowledgeAlert: async (alertId: string) => {
    const { data } = await apiClient.post(`/alerts/${alertId}/acknowledge`)
    return data
  },
}

export default apiClient
