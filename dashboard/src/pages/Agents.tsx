import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Server, Trash2, RefreshCw } from 'lucide-react'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'
import { getAgents, deleteAgent, type Agent } from '@/lib/api'
import { formatRelativeTime, formatDate } from '@/lib/utils'

export default function Agents() {
  const queryClient = useQueryClient()

  // Fetch agents with more frequent refresh for real-time updates
  const {
    data: agents,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['agents'],
    queryFn: getAgents,
    refetchInterval: 10000, // Refresh every 10s for real-time updates
    staleTime: 0, // Always consider data stale to prevent caching
    cacheTime: 0, // Don't cache data to ensure fresh results
  })

  // Delete agent mutation
  const deleteMutation = useMutation({
    mutationFn: deleteAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })

  const handleDelete = (agentId: string) => {
    if (confirm('Are you sure you want to delete this agent?')) {
      deleteMutation.mutate(agentId)
    }
  }

  if (isLoading) {
    return <LoadingSpinner size="lg" />
  }

  if (error) {
    return (
      <ErrorMessage
        message="Failed to load agents"
        retry={() => refetch()}
      />
    )
  }

  // All agents shown are active (backend filters out dead agents automatically)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage and monitor DLP agents
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn-secondary"
          disabled={isLoading}
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Server className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Agents</p>
              <p className="text-2xl font-bold text-gray-900">
                {agents?.length || 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Agents that have sent heartbeat within the last 5 minutes
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Agents Table */}
      <div className="card p-0">
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Agent ID</th>
                <th>Name</th>
                <th>OS</th>
                <th>IP Address</th>
                <th>Last Seen</th>
                <th>Registered</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {agents?.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12">
                    <Server className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600 font-medium">No active agents</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Agents will appear here once they register and send heartbeat
                    </p>
                  </td>
                </tr>
              ) : (
                agents?.map((agent) => (
                  <tr key={agent.agent_id}>
                    <td>
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {agent.agent_id}
                      </code>
                    </td>
                    <td>
                      <div>
                        <div className="font-medium text-gray-900">
                          {agent.name}
                        </div>
                        {agent.hostname && (
                          <div className="text-xs text-gray-500">
                            {agent.hostname}
                          </div>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <span>{agent.os}</span>
                        {agent.os_version && (
                          <span className="text-xs text-gray-500">
                            {agent.os_version}
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <code className="text-xs">{agent.ip_address}</code>
                    </td>
                    <td>
                      <span 
                        className="text-sm text-gray-600 cursor-help"
                        title={formatDate(agent.last_seen, 'PPpp')}
                      >
                        {formatRelativeTime(agent.last_seen)}
                      </span>
                    </td>
                    <td>
                      <span className="text-sm text-gray-600">
                        {formatRelativeTime(agent.created_at)}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleDelete(agent.agent_id)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Delete agent entry"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
