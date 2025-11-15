import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Server, Circle, Trash2, RefreshCw } from 'lucide-react'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'
import { getAgents, deleteAgent, type Agent } from '@/lib/api'
import { formatRelativeTime, getStatusColor, cn } from '@/lib/utils'

export default function Agents() {
  const queryClient = useQueryClient()

  // Fetch agents
  const {
    data: agents,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['agents'],
    queryFn: getAgents,
    refetchInterval: 10000, // Refresh every 10s
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

  const activeAgents = agents?.filter((a) => a.status === 'active') || []
  const inactiveAgents = agents?.filter((a) => a.status === 'inactive') || []
  const pendingAgents = agents?.filter((a) => a.status === 'pending') || []

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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Server className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Agents</p>
              <p className="text-2xl font-bold text-gray-900">
                {agents?.length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Circle className="h-5 w-5 text-green-600 fill-current" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active</p>
              <p className="text-2xl font-bold text-green-600">
                {activeAgents.length}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Circle className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Inactive</p>
              <p className="text-2xl font-bold text-gray-600">
                {inactiveAgents.length}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Circle className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-yellow-600">
                {pendingAgents.length}
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
                <th>Status</th>
                <th>Last Seen</th>
                <th>Registered</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {agents?.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12">
                    <Server className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600 font-medium">No agents found</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Agents will appear here once they register
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
                      <span className={cn('badge', getStatusColor(agent.status))}>
                        <Circle className="h-2 w-2 fill-current" />
                        {agent.status}
                      </span>
                    </td>
                    <td>
                      <span className="text-sm text-gray-600">
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
                        title="Delete agent"
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
