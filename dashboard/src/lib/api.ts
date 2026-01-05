import axios from 'axios'
import { useAuthStore } from './store/auth'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:55000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
  maxRedirects: 5, // Follow redirects (default is 5, but explicit is better)
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  // Get token from store (will be hydrated from localStorage by Zustand persist)
  const token = useAuthStore.getState().accessToken
  // Fallback: try to get token directly from localStorage if store hasn't hydrated yet
  let authToken = token
  if (!authToken) {
    try {
      const authData = localStorage.getItem('dlp-auth-v2')
      if (authData) {
        const parsed = JSON.parse(authData)
        authToken = parsed?.state?.accessToken
      }
    } catch (e) {
      // Ignore errors
    }
  }
  if (authToken && config.headers) {
    config.headers['Authorization'] = `Bearer ${authToken}`
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
        window.location.href = '/login'
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

export const clearAllEvents = async () => {
  const { data } = await apiClient.delete('/events/clear')
  return data
}

export const initiateGoogleDriveConnection = async () => {
  const { data } = await apiClient.post('/google-drive/connect')
  return data as { auth_url: string; state: string }
}

export const getGoogleDriveConnections = async () => {
  const { data } = await apiClient.get('/google-drive/connections')
  return data
}

export const listGoogleDriveFolders = async (
  connectionId: string,
  parentId: string = 'root',
  pageToken?: string
) => {
  const { data } = await apiClient.get(`/google-drive/connections/${connectionId}/folders`, {
    params: {
      parent_id: parentId,
      page_token: pageToken,
    },
  })
  return data
}

export const getGoogleDriveProtectedFolders = async (connectionId: string) => {
  const { data } = await apiClient.get(`/google-drive/connections/${connectionId}/protected-folders`)
  return data
}

export const updateGoogleDriveBaseline = async (
  connectionId: string,
  payload?: { folderIds?: string[]; startTime?: string }
) => {
  const body: Record<string, any> = {}
  if (payload?.folderIds && payload.folderIds.length > 0) {
    body.folder_ids = payload.folderIds
  }
  if (payload?.startTime) {
    body.start_time = payload.startTime
  }
  const { data } = await apiClient.post(`/google-drive/connections/${connectionId}/baseline`, body)
  return data
}

export const triggerGoogleDrivePoll = async () => {
  const { data } = await apiClient.post('/google-drive/poll')
  return data as {
    status: string
    task_id?: string | null
    message?: string
  }
}

// Type exports
export type Agent = {
  id?: string
  agent_id: string
  name: string
  os: string
  ip_address: string
  // Status field removed - agents are considered active if they've sent heartbeat within timeout period
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
  event_subtype?: string
  severity: string
  description?: string
  classification_score?: number
  classification_labels?: string[]
  classification_type?: string
  file_path?: string
  file_name?: string
  file_id?: string
  mime_type?: string
  folder_id?: string
  folder_name?: string
  folder_path?: string
  timestamp: string | Date
  content?: string
  clipboard_content?: string
  blocked?: boolean
  policy_id?: string | null
  action_taken?: string
  destination?: string | null
  source?: string
  user_email?: string
  matched_policies?: any[]
  metadata?: Record<string, any>
  details?: Record<string, any>
}

export type GoogleDriveProtectedFolderStatus = {
  folder_id: string
  folder_name?: string
  folder_path?: string
  last_seen_timestamp?: string
}

export type GoogleDrivePollResponse = {
  status: string
  task_id?: string | null
  message?: string
}

// OneDrive API functions
export const initiateOneDriveConnection = async () => {
  const { data } = await apiClient.post('/onedrive/connect')
  return data
}

export const getOneDriveConnections = async () => {
  const { data } = await apiClient.get('/onedrive/connections')
  return data
}

export const listOneDriveFolders = async (
  connectionId: string,
  parentId: string = 'root',
  pageToken?: string
) => {
  const { data } = await apiClient.get(`/onedrive/connections/${connectionId}/folders`, {
    params: { parent_id: parentId, page_token: pageToken },
  })
  return data
}

export const getOneDriveProtectedFolders = async (connectionId: string) => {
  const { data } = await apiClient.get(`/onedrive/connections/${connectionId}/protected-folders`)
  return data
}

export const updateOneDriveBaseline = async (
  connectionId: string,
  payload?: { folderIds?: string[]; startTime?: string }
) => {
  const body = payload || {}
  const { data } = await apiClient.post(`/onedrive/connections/${connectionId}/baseline`, body)
  return data
}

export const triggerOneDrivePoll = async () => {
  const { data } = await apiClient.post('/onedrive/poll')
  return data
}

export type OneDriveProtectedFolderStatus = {
  folder_id: string
  folder_name?: string
  folder_path?: string
  last_seen_timestamp?: string
}

export type OneDrivePollResponse = {
  status: string
  task_id?: string | null
  message?: string
}

export const api = {
  // Dashboard
  getDashboardOverview: async () => {
    const { data } = await apiClient.get('/dashboard/overview')
    return data
    },
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

// Stats functions (aliases for backwards compatibility) - removed duplicates, using exports from above

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
  // Use trailing slash to avoid redirect
  const { data } = await apiClient.get('/policies/', { params })
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

export const enablePolicy = async (policyId: string) => {
  const { data } = await apiClient.post(`/policies/${policyId}/enable`)
  return data
}

export const disablePolicy = async (policyId: string) => {
  const { data } = await apiClient.post(`/policies/${policyId}/disable`)
  return data
}

export const refreshPolicyBundles = async () => {
  const { data } = await apiClient.post('/policies/cache/refresh')
  return data
}

// Events helper used by dashboard pages
export const getEvents = async (params?: any) => {
  const { data } = await apiClient.get('/events', { params })
  // The backend returns a paginated envelope; the dashboard expects a flat list.
  return data.events || []
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
export const acknowledgeAlert = async (alertId: string) => {
  const { data } = await apiClient.post(`/alerts/${alertId}/acknowledge`)
  return data
}

export default apiClient
