import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, FileText, Calendar, Shield, AlertTriangle, Ban, X, ArrowRight, File, HardDrive, Usb, ChevronDown, ChevronUp, Trash2 } from 'lucide-react'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'
import { searchEvents, getAgents, clearAllEvents, type Event, type Agent } from '@/lib/api'
import { formatDate, getSeverityColor, cn, truncate, formatDateTimeIST } from '@/lib/utils'
import toast from 'react-hot-toast'

// Event Detail Modal Component
function EventDetailModal({ 
  event, 
  onClose, 
  isBlockedTransfer, 
  formatFileSize, 
  getDriveLetter 
}: { 
  event: any
  onClose: () => void
  isBlockedTransfer: boolean
  formatFileSize: (bytes: number) => string
  getDriveLetter: (path: string) => string
}) {
  const [showRawData, setShowRawData] = useState(false)

  if (isBlockedTransfer) {
    // User-friendly display for blocked transfers
    const blocked = event.blocked !== false // Default to true if not specified
    const sourcePath = event.file_path || ''
    const destPath = event.destination || ''
    const fileName = event.file_name || sourcePath.split(/[/\\]/).pop() || 'Unknown'
    const fileSize = event.file_size ? formatFileSize(event.file_size) : 'Unknown size'
    const driveLetter = getDriveLetter(destPath)

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50" onClick={onClose}>
        <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl ${blocked ? 'bg-red-100 border border-red-300' : 'bg-orange-100 border border-orange-300'}`}>
                <Shield className={`w-8 h-8 ${blocked ? 'text-red-600' : 'text-orange-600'}`} />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">
                  {blocked ? 'File Transfer Blocked' : 'Transfer Attempt Detected'}
                </h3>
                <p className="text-gray-500 text-sm mt-1">{formatDateTimeIST(event.timestamp)}</p>
              </div>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* Status Badge */}
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium ${
                blocked 
                  ? 'bg-green-100 border-green-300 text-green-700' 
                  : 'bg-red-100 border-red-300 text-red-700'
              }`}>
                <Ban className="w-4 h-4" />
                {blocked ? 'Successfully Blocked' : 'Block Failed'}
              </span>
              <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium uppercase ${
                event.severity === 'critical' 
                  ? 'bg-red-100 border-red-300 text-red-700'
                  : 'bg-orange-100 border-orange-300 text-orange-700'
              }`}>
                {event.severity}
              </span>
            </div>

            {/* Transfer Flow Visualization */}
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
              <div className="flex items-center justify-between gap-4">
                {/* Source */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <File className="w-5 h-5 text-blue-600" />
                    <label className="text-sm text-gray-600 uppercase font-medium">Source</label>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <p className="text-gray-900 font-semibold text-lg mb-1">{fileName}</p>
                    <p className="text-gray-600 text-sm font-mono truncate" title={sourcePath}>
                      {sourcePath}
                    </p>
                    <p className="text-gray-500 text-xs mt-2">{fileSize}</p>
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex flex-col items-center gap-2">
                  <ArrowRight className="w-6 h-6 text-gray-400" />
                  <span className="text-xs text-gray-500 font-medium">Copied to</span>
                </div>

                {/* Destination */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <HardDrive className="w-5 h-5 text-red-600" />
                    <label className="text-sm text-gray-600 uppercase font-medium">Destination</label>
                  </div>
                  <div className="bg-white rounded-lg p-4 border border-red-300">
                    <div className="flex items-center gap-2 mb-1">
                      <Usb className="w-4 h-4 text-red-600" />
                      <p className="text-red-600 font-semibold">{driveLetter || 'USB Drive'}</p>
                    </div>
                    <p className="text-gray-600 text-sm font-mono truncate" title={destPath}>
                      {destPath}
                    </p>
                    <p className="text-red-600 text-xs mt-2 font-medium">Blocked</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Event Details Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <label className="text-xs text-gray-600 uppercase font-medium mb-1 block">Agent</label>
                <p className="text-gray-900 font-medium">{event.agent_id}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <label className="text-xs text-gray-600 uppercase font-medium mb-1 block">User</label>
                <p className="text-gray-900 font-medium">{event.user_email}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <label className="text-xs text-gray-600 uppercase font-medium mb-1 block">Transfer Type</label>
                <p className="text-gray-900 font-medium capitalize">{event.transfer_type || 'USB Copy'}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <label className="text-xs text-gray-600 uppercase font-medium mb-1 block">Action Taken</label>
                <p className="text-gray-900 font-medium capitalize">{event.action_taken || event.action || 'Blocked'}</p>
              </div>
            </div>

            {/* File Hash (if available) */}
            {event.file_hash && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <label className="text-xs text-gray-600 uppercase font-medium mb-2 block">File Hash (SHA256)</label>
                <p className="text-gray-700 font-mono text-xs break-all">{event.file_hash}</p>
              </div>
            )}

            {/* Raw JSON Data (Expandable) */}
            <div className="border-t border-gray-200 pt-4">
              <button
                onClick={() => setShowRawData(!showRawData)}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors w-full"
              >
                {showRawData ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                <span className="text-sm font-medium">View Raw Event Data</span>
              </button>
              {showRawData && (
                <div className="mt-4 bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <pre className="text-xs text-gray-700 overflow-x-auto">
                    {JSON.stringify(event, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Standard display for other event types
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-6 z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h3 className="text-2xl font-bold text-gray-900">Event Details</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="text-sm text-gray-600">Description</label>
            <p className="text-gray-900 font-medium">{event.description}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-600">Event Type</label>
              <p className="text-gray-900 font-medium capitalize">{event.event_type}</p>
            </div>
            <div>
              <label className="text-sm text-gray-600">Severity</label>
              <p className="text-gray-900 font-medium capitalize">{event.severity}</p>
            </div>
            <div>
              <label className="text-sm text-gray-600">Action Taken</label>
              <p className="text-gray-900 font-medium capitalize">{event.action_taken || event.action || 'N/A'}</p>
            </div>
            <div>
              <label className="text-sm text-gray-600">Timestamp</label>
              <p className="text-gray-900 font-medium">{formatDateTimeIST(event.timestamp)}</p>
            </div>
            <div>
              <label className="text-sm text-gray-600">User</label>
              <p className="text-gray-900 font-medium">{event.user_email}</p>
            </div>
            <div>
              <label className="text-sm text-gray-600">Agent</label>
              <p className="text-gray-900 font-medium">{event.agent_id}</p>
            </div>
          </div>
          {event.file_path && (
            <div>
              <label className="text-sm text-gray-600">File Path</label>
              <p className="text-gray-900 font-mono text-sm">{event.file_path}</p>
            </div>
          )}
          {event.details && (
            <div>
              <label className="text-sm text-gray-600">Additional Details</label>
              <p className="text-gray-900 font-mono text-sm bg-gray-50 p-4 rounded-lg">
                {JSON.stringify(event.details, null, 2)}
              </p>
            </div>
          )}
          
          {/* Raw JSON Data (Expandable) */}
          <div className="border-t border-gray-200 pt-4">
            <button
              onClick={() => setShowRawData(!showRawData)}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors w-full"
            >
              {showRawData ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              <span className="text-sm font-medium">View Raw Event Data</span>
            </button>
            {showRawData && (
              <div className="mt-4 bg-gray-50 rounded-lg p-4 border border-gray-200">
                <pre className="text-xs text-gray-700 overflow-x-auto">
                  {JSON.stringify(event, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

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

  // Helper function to format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  // Check if event is a blocked transfer
  const isBlockedTransfer = (event: any): boolean => {
    // Check if it's a file event with transfer-related indicators
    if (event.event_type !== 'file') return false
    
    // Check for transfer-related fields
    const hasTransferSubtype = event.event_subtype === 'transfer_blocked' || event.event_subtype === 'transfer_attempt'
    const hasTransferType = event.transfer_type === 'usb_copy'
    const hasDestination = event.destination && event.destination !== null
    const hasBlockedField = event.blocked === true || event.blocked === false // Explicitly set
    const descriptionMatches = event.description?.toLowerCase().includes('transfer blocked') || 
                                event.description?.toLowerCase().includes('file transfer')
    
    // Must have file_path and at least one transfer indicator
    return event.file_path && (
      (hasTransferSubtype && hasDestination) ||
      (hasTransferType && hasDestination) ||
      (hasBlockedField && hasDestination && descriptionMatches)
    )
  }

  // Extract USB drive letter from destination path
  const getDriveLetter = (path: string): string => {
    if (!path) return ''
    const match = path.match(/^([A-Z]):/)
    return match ? match[1] + ':' : ''
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

  const handleClearLogs = async () => {
    if (!confirm('Are you sure you want to clear all events? This action cannot be undone.')) {
      return
    }

    try {
      const result = await clearAllEvents()
      toast.success(`Successfully cleared ${result.deleted_count} events`)
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to clear events')
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
          <button
            onClick={handleClearLogs}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={events.length === 0}
          >
            <Trash2 className="w-4 h-4" />
            Clear Logs
          </button>
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
        <EventDetailModal 
          event={selectedEvent} 
          onClose={() => setSelectedEvent(null)}
          isBlockedTransfer={isBlockedTransfer(selectedEvent)}
          formatFileSize={formatFileSize}
          getDriveLetter={getDriveLetter}
        />
      )}
    </div>
  )
}
