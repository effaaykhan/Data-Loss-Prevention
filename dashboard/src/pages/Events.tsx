import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, FileText, Calendar, Shield, AlertTriangle } from 'lucide-react'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'
import { searchEvents, getAgents, type Event, type Agent } from '@/lib/api'
import { formatDate, getSeverityColor, cn, truncate } from '@/lib/utils'

export default function Events() {
  const [kqlQuery, setKqlQuery] = useState('')
  const [activeQuery, setActiveQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)

  // Fetch agents to map agent_id to agent name
  const { data: agentsData } = useQuery({
    queryKey: ['agents'],
    queryFn: getAgents,
    refetchInterval: 30000, // Refresh every 30s
  })

  // Create agent lookup map: agent_id -> agent name
  const agentMap = useMemo(() => {
    const map = new Map<string, string>()
    if (agentsData && Array.isArray(agentsData)) {
      agentsData.forEach((agent: Agent) => {
        if (agent?.agent_id && agent?.name) {
          map.set(agent.agent_id, agent.name)
        }
      })
    }
    return map
  }, [agentsData])

  // Helper function to get agent name from agent_id
  const getAgentName = (agentId?: string): string => {
    if (!agentId) return 'Unknown Agent'
    const agentName = agentMap.get(agentId)
    return agentName || agentId // Return agent_id if name not found, not "Unknown Agent"
  }

  // Fetch events
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['events', activeQuery],
    queryFn: () =>
      activeQuery
        ? searchEvents({ query: activeQuery, limit: 100 })
        : searchEvents({ limit: 100 }),
    refetchInterval: 15000, // Refresh every 15s
  })

  const events = data?.events || []
  const total = data?.total || 0

  const handleSearch = () => {
    setActiveQuery(kqlQuery)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  // Quick filter examples
  const quickFilters = [
    { label: 'Critical Events', query: 'event.severity:critical' },
    { label: 'Blocked Events', query: 'blocked:true' },
    { label: 'File Events', query: 'event.type:file' },
    { label: 'USB Events', query: 'event.type:usb' },
    { label: 'Clipboard Events', query: 'event.type:clipboard' },
    { label: 'With Classifications', query: 'classification:*' },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Events</h1>
        <p className="mt-1 text-sm text-gray-600">
          Search and analyze DLP events using KQL (Kibana Query Language)
        </p>
      </div>

      {/* Search Bar */}
      <div className="card">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder='Search with KQL (e.g., event.type:"file" AND event.severity:"high")'
              className="input pl-10"
              value={kqlQuery}
              onChange={(e) => setKqlQuery(e.target.value)}
              onKeyPress={handleKeyPress}
            />
          </div>
          <button onClick={handleSearch} className="btn-primary">
            Search
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary"
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>
        </div>

        {/* Quick Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm font-medium text-gray-700 mb-2">
              Quick Filters:
            </p>
            <div className="flex flex-wrap gap-2">
              {quickFilters.map((filter) => (
                <button
                  key={filter.label}
                  onClick={() => {
                    setKqlQuery(filter.query)
                    setActiveQuery(filter.query)
                  }}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* KQL Help */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-600">
            <strong>KQL Examples:</strong> field:value, field:"exact value",
            field:* (wildcard), field:(value1 OR value2), field &gt; 100, NOT field:value
          </p>
        </div>
      </div>

      {/* Results */}
      <div className="card p-0">
        {/* Results Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900">Search Results</h3>
            <p className="text-sm text-gray-600 mt-1">
              {total.toLocaleString()} events found
              {activeQuery && (
                <span className="ml-2">
                  for query: <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">{activeQuery}</code>
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Results List */}
        <div className="divide-y divide-gray-200">
          {isLoading ? (
            <LoadingSpinner />
          ) : error ? (
            <div className="p-6">
              <ErrorMessage message="Failed to load events" retry={() => refetch()} />
            </div>
          ) : events.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 font-medium">No events found</p>
              <p className="text-sm text-gray-500 mt-1">
                Try adjusting your search query
              </p>
            </div>
          ) : (
            events.map((event) => (
              <div
                key={event.id || event.event_id}
                className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => setSelectedEvent(event)}
              >
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div
                    className={cn(
                      'p-2 rounded-lg',
                      event.blocked
                        ? 'bg-red-100'
                        : event.severity === 'critical'
                        ? 'bg-red-50'
                        : event.severity === 'high'
                        ? 'bg-orange-50'
                        : 'bg-blue-50'
                    )}
                  >
                    {event.event_type === 'file' ? (
                      <FileText className="h-5 w-5 text-gray-700" />
                    ) : event.event_type === 'usb' ? (
                      <Shield className="h-5 w-5 text-gray-700" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-gray-700" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={cn(
                          'badge',
                          getSeverityColor(event.severity)
                        )}
                      >
                        {event.severity}
                      </span>
                      <span className="badge badge-info">
                        {event.event_type}
                      </span>
                      {event.blocked && (
                        <span className="badge badge-danger">blocked</span>
                      )}
                      {event.classification_labels && event.classification_labels.length > 0 && (
                        <span className="badge bg-purple-100 text-purple-800">
                          {event.classification_labels[0]}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <span>
                        <span className="text-gray-500">Agent:</span>{' '}
                        <span className="font-medium text-gray-900">
                          {getAgentName(event.agent_id)}
                        </span>
                      </span>
                      <span className="text-gray-400">•</span>
                      <span>{formatDate(event.timestamp, 'PPpp')}</span>
                      <span className="text-gray-400">•</span>
                      <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">
                        {event.id || event.event_id}
                      </code>
                    </div>

                    {/* Event Details */}
                    {event.file_path && (
                      <p className="mt-2 text-sm text-gray-700">
                        <strong>File:</strong> {truncate(event.file_path, 80)}
                      </p>
                    )}

                    {event.usb && (
                      <p className="mt-2 text-sm text-gray-700">
                        <strong>USB:</strong> {event.usb.vendor} {event.usb.product}
                        {event.usb.serial && ` (${event.usb.serial})`}
                      </p>
                    )}

                    {event.policy && (
                      <p className="mt-2 text-sm text-gray-700">
                        <strong>Policy:</strong> {event.policy.policy_name} (
                        {event.policy.action})
                      </p>
                    )}

                    {event.content_redacted && (
                      <div className="mt-2 p-2 bg-gray-100 rounded text-xs font-mono">
                        {truncate(event.content_redacted, 200)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50"
          onClick={() => setSelectedEvent(null)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Event Details
              </h3>
              <code className="text-xs text-gray-500">{selectedEvent.event_id}</code>
            </div>
            <div className="p-6">
              <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto">
                {JSON.stringify(selectedEvent, null, 2)}
              </pre>
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
