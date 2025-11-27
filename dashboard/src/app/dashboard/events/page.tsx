'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { AlertTriangle, Usb, Clipboard, Cloud, Ban, Bell, Eye, Filter, Download, Search, Loader2, X, Shield, ArrowRight, File, HardDrive, ChevronDown, ChevronUp, Trash2, RefreshCcw } from 'lucide-react'
import { getEvents as fetchEvents, getEventStats, clearAllEvents, triggerGoogleDrivePoll } from '@/lib/api'
import { formatDateTimeIST } from '@/lib/utils'
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

  // Helper function to get action icon
  const getActionIcon = (action: string) => {
    switch (action) {
      case 'blocked': return <Ban className="w-4 h-4" />
      case 'alerted': return <Bell className="w-4 h-4" />
      case 'quarantined': return <Download className="w-4 h-4" />
      default: return <Eye className="w-4 h-4" />
    }
  }

  if (isBlockedTransfer) {
    // User-friendly display for blocked transfers
    const blocked = event.blocked !== false // Default to true if not specified
    const sourcePath = event.file_path || ''
    const destPath = event.destination || ''
    const fileName = event.file_name || sourcePath.split(/[/\\]/).pop() || 'Unknown'
    const fileSize = event.file_size ? formatFileSize(event.file_size) : 'Unknown size'
    const driveLetter = getDriveLetter(destPath)

    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
        <div className="bg-gray-800 rounded-2xl max-w-3xl w-full border border-gray-700 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl ${blocked ? 'bg-red-900/30 border border-red-500/50' : 'bg-orange-900/30 border border-orange-500/50'}`}>
                <Shield className={`w-8 h-8 ${blocked ? 'text-red-400' : 'text-orange-400'}`} />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">
                  {blocked ? 'File Transfer Blocked' : 'Transfer Attempt Detected'}
                </h3>
                <p className="text-gray-400 text-sm mt-1">{formatDateTimeIST(event.timestamp)}</p>
              </div>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* Status Badge */}
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium ${
                blocked 
                  ? 'bg-green-900/30 border-green-500/50 text-green-400' 
                  : 'bg-red-900/30 border-red-500/50 text-red-400'
              }`}>
                <Ban className="w-4 h-4" />
                {blocked ? 'Successfully Blocked' : 'Block Failed'}
              </span>
              <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium uppercase ${
                event.severity === 'critical' 
                  ? 'bg-red-900/30 border-red-500/50 text-red-400'
                  : 'bg-orange-900/30 border-orange-500/50 text-orange-400'
              }`}>
                {event.severity}
              </span>
            </div>

            {/* Transfer Flow Visualization */}
            <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center justify-between gap-4">
                {/* Source */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <File className="w-5 h-5 text-blue-400" />
                    <label className="text-sm text-gray-400 uppercase font-medium">Source</label>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <p className="text-white font-semibold text-lg mb-1">{fileName}</p>
                    <p className="text-gray-400 text-sm font-mono truncate" title={sourcePath}>
                      {sourcePath}
                    </p>
                    <p className="text-gray-500 text-xs mt-2">{fileSize}</p>
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex flex-col items-center gap-2">
                  <ArrowRight className="w-6 h-6 text-gray-500" />
                  <span className="text-xs text-gray-500 font-medium">Copied to</span>
                </div>

                {/* Destination */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <HardDrive className="w-5 h-5 text-red-400" />
                    <label className="text-sm text-gray-400 uppercase font-medium">Destination</label>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-red-500/30">
                    <div className="flex items-center gap-2 mb-1">
                      <Usb className="w-4 h-4 text-red-400" />
                      <p className="text-red-400 font-semibold">{driveLetter || 'USB Drive'}</p>
                    </div>
                    <p className="text-gray-400 text-sm font-mono truncate" title={destPath}>
                      {destPath}
                    </p>
                    <p className="text-red-400 text-xs mt-2 font-medium">Blocked</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Event Details Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-900/30 rounded-lg p-4 border border-gray-700">
                <label className="text-xs text-gray-400 uppercase font-medium mb-1 block">Agent</label>
                <p className="text-white font-medium">{event.agent_id}</p>
              </div>
              <div className="bg-gray-900/30 rounded-lg p-4 border border-gray-700">
                <label className="text-xs text-gray-400 uppercase font-medium mb-1 block">User</label>
                <p className="text-white font-medium">{event.user_email}</p>
              </div>
              <div className="bg-gray-900/30 rounded-lg p-4 border border-gray-700">
                <label className="text-xs text-gray-400 uppercase font-medium mb-1 block">Transfer Type</label>
                <p className="text-white font-medium capitalize">{event.transfer_type || 'USB Copy'}</p>
              </div>
              <div className="bg-gray-900/30 rounded-lg p-4 border border-gray-700">
                <label className="text-xs text-gray-400 uppercase font-medium mb-1 block">Action Taken</label>
                <p className="text-white font-medium capitalize">{event.action_taken || event.action || 'Blocked'}</p>
              </div>
            </div>

            {/* File Hash (if available) */}
            {event.file_hash && (
              <div className="bg-gray-900/30 rounded-lg p-4 border border-gray-700">
                <label className="text-xs text-gray-400 uppercase font-medium mb-2 block">File Hash (SHA256)</label>
                <p className="text-gray-300 font-mono text-xs break-all">{event.file_hash}</p>
              </div>
            )}

            {/* Content Snippet for Transfer Events */}
            {event.content && (
              <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <Eye className="w-5 h-5 text-purple-400" />
                  <label className="text-sm text-gray-400 uppercase font-medium">File Content Preview</label>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 max-h-48 overflow-y-auto">
                  <pre className="text-white font-mono text-xs whitespace-pre-wrap break-words">
                    {event.content.length > 1000 ? event.content.substring(0, 1000) + '\n\n... (truncated)' : event.content}
                  </pre>
                </div>
              </div>
            )}

            {/* Matched Policies for Transfer Events */}
            {event.matched_policies && event.matched_policies.length > 0 && (
              <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <Shield className="w-5 h-5 text-indigo-400" />
                  <label className="text-sm text-gray-400 uppercase font-medium">Policy That Triggered Action</label>
                </div>
                <div className="space-y-3">
                  {event.matched_policies.map((policy: any, idx: number) => (
                    <div key={idx} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                      <p className="text-white font-semibold">{policy.policy_name || 'Unknown Policy'}</p>
                      {policy.severity && (
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium mt-2 ${
                          policy.severity === 'critical' ? 'bg-red-900/30 text-red-400' :
                          policy.severity === 'high' ? 'bg-orange-900/30 text-orange-400' :
                          'bg-yellow-900/30 text-yellow-400'
                        }`}>
                          {policy.severity}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Raw JSON Data (Expandable) */}
            <div className="border-t border-gray-700 pt-4">
              <button
                onClick={() => setShowRawData(!showRawData)}
                className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors w-full"
              >
                {showRawData ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                <span className="text-sm font-medium">View Raw Event Data</span>
              </button>
              {showRawData && (
                <div className="mt-4 bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                  <pre className="text-xs text-gray-300 overflow-x-auto">
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

  // Enhanced display for different event types
  const eventType = event.event_type?.toLowerCase() || 'file'
  const isClipboard = eventType === 'clipboard'
  const isFile = eventType === 'file' && !isBlockedTransfer
  
  // Get content to display
  const displayContent = isClipboard 
    ? (event.clipboard_content || event.content || '')
    : (event.content || event.content_redacted || '')
  
  // Get classification labels
  const classificationLabels = event.classification_labels || []
  const classification = event.classification || []
  
  // Get matched policies
  const matchedPolicies = event.matched_policies || []
  
  // Get file metadata
  const fileName = event.file_name || (event.file_path ? event.file_path.split(/[/\\]/).pop() : 'Unknown')
  const fileSize = event.file_size ? formatFileSize(event.file_size) : null
  const fileExtension = fileName.includes('.') ? fileName.split('.').pop()?.toUpperCase() : null

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-gray-800 rounded-2xl max-w-4xl w-full border border-gray-700 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl ${
              event.severity === 'critical' ? 'bg-red-900/30 border border-red-500/50' :
              event.severity === 'high' ? 'bg-orange-900/30 border border-orange-500/50' :
              'bg-yellow-900/30 border border-yellow-500/50'
            }`}>
              {isClipboard ? (
                <Clipboard className={`w-8 h-8 ${event.severity === 'critical' ? 'text-red-400' : 'text-orange-400'}`} />
              ) : (
                <File className={`w-8 h-8 ${event.severity === 'critical' ? 'text-red-400' : 'text-orange-400'}`} />
              )}
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white">
                {isClipboard ? 'Clipboard Violation' : isFile ? (
                  // Show action type for file events (Google Drive or regular file events)
                  event.event_subtype ? (
                    event.event_subtype.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                  ) : event.description || 'File Violation'
                ) : 'Event Details'}
              </h3>
              <p className="text-gray-400 text-sm mt-1">{formatDateTimeIST(event.timestamp)}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Severity and Action Badges */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium uppercase ${
              event.severity === 'critical' ? 'bg-red-900/30 border-red-500/50 text-red-400' :
              event.severity === 'high' ? 'bg-orange-900/30 border-orange-500/50 text-orange-400' :
              event.severity === 'medium' ? 'bg-yellow-900/30 border-yellow-500/50 text-yellow-400' :
              'bg-green-900/30 border-green-500/50 text-green-400'
            }`}>
              {event.severity}
            </span>
            {/* Show event subtype/action for Google Drive events */}
            {event.event_subtype && (
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium bg-blue-900/30 border-blue-500/50 text-blue-400">
                <File className="w-4 h-4" />
                {event.event_subtype.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            )}
            <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium ${
              event.action_taken === 'blocked' ? 'bg-red-900/30 border-red-500/50 text-red-400' :
              event.action_taken === 'alerted' ? 'bg-yellow-900/30 border-yellow-500/50 text-yellow-400' :
              'bg-gray-900/30 border-gray-500/50 text-gray-400'
            }`}>
              {getActionIcon(event.action_taken || event.action || 'logged')}
              {event.action_taken || event.action || 'Logged'}
            </span>
          </div>

          {/* Clipboard Event - Show Clipboard Content */}
          {isClipboard && displayContent && (
            <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 mb-4">
                <Clipboard className="w-5 h-5 text-blue-400" />
                <label className="text-sm text-gray-400 uppercase font-medium">Clipboard Content</label>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <p className="text-white font-mono text-sm whitespace-pre-wrap break-words">
                  {displayContent}
                </p>
              </div>
            </div>
          )}

          {/* File Event - Show File Info and Content */}
          {isFile && (
            <>
              {/* File Information */}
              <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <File className="w-5 h-5 text-blue-400" />
                  <label className="text-sm text-gray-400 uppercase font-medium">File Information</label>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">File Name</label>
                    <p className="text-white font-semibold text-lg">{fileName}</p>
                  </div>
                  {event.file_path && (
                    <div>
                      <label className="text-xs text-gray-500 mb-1 block">File Path</label>
                      <p className="text-white font-mono text-sm break-all">{event.file_path}</p>
                    </div>
                  )}
                  <div className="grid grid-cols-3 gap-4">
                    {fileSize && (
                      <div>
                        <label className="text-xs text-gray-500 mb-1 block">Size</label>
                        <p className="text-white font-medium">{fileSize}</p>
                      </div>
                    )}
                    {fileExtension && (
                      <div>
                        <label className="text-xs text-gray-500 mb-1 block">Extension</label>
                        <p className="text-white font-medium">.{fileExtension}</p>
                      </div>
                    )}
                    {event.file_hash && (
                      <div>
                        <label className="text-xs text-gray-500 mb-1 block">Hash (SHA256)</label>
                        <p className="text-white font-mono text-xs break-all" title={event.file_hash}>
                          {event.file_hash.substring(0, 16)}...
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* File Content Snippet */}
              {displayContent && (
                <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
                  <div className="flex items-center gap-2 mb-4">
                    <Eye className="w-5 h-5 text-purple-400" />
                    <label className="text-sm text-gray-400 uppercase font-medium">Content That Triggered Violation</label>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 max-h-64 overflow-y-auto">
                    <pre className="text-white font-mono text-xs whitespace-pre-wrap break-words">
                      {displayContent.length > 2000 ? displayContent.substring(0, 2000) + '\n\n... (truncated)' : displayContent}
                    </pre>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Classification Labels - What Was Detected */}
          {classificationLabels.length > 0 && (
            <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                <label className="text-sm text-gray-400 uppercase font-medium">Detected Sensitive Data</label>
              </div>
              <div className="flex flex-wrap gap-2">
                {classificationLabels.map((label: string, idx: number) => {
                  const conf = classification[idx]?.confidence || event.classification_score || 1.0
                  return (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border bg-red-900/30 border-red-500/50 text-red-400 text-sm font-medium"
                    >
                      <Shield className="w-4 h-4" />
                      {label}
                      {conf < 1.0 && <span className="text-xs opacity-75">({Math.round(conf * 100)}%)</span>}
                    </span>
                  )
                })}
              </div>
            </div>
          )}

          {/* Matched Policies */}
          {matchedPolicies.length > 0 && (
            <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-5 h-5 text-indigo-400" />
                <label className="text-sm text-gray-400 uppercase font-medium">Matched Policies</label>
              </div>
              <div className="space-y-3">
                {matchedPolicies.map((policy: any, idx: number) => (
                  <div key={idx} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-white font-semibold">{policy.policy_name || 'Unknown Policy'}</p>
                        {policy.matched_rules && policy.matched_rules.length > 0 && (
                          <div className="mt-2 space-y-1">
                            <p className="text-xs text-gray-500">Matched Rules:</p>
                            {policy.matched_rules.map((rule: any, ruleIdx: number) => (
                              <p key={ruleIdx} className="text-xs text-gray-400 font-mono ml-2">
                                • {rule.field} {rule.operator} {Array.isArray(rule.value) ? rule.value.join(', ') : rule.value}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                          policy.severity === 'critical' ? 'bg-red-900/30 text-red-400' :
                          policy.severity === 'high' ? 'bg-orange-900/30 text-orange-400' :
                          'bg-yellow-900/30 text-yellow-400'
                        }`}>
                          {policy.severity}
                        </span>
                        {policy.priority && (
                          <span className="text-xs text-gray-500">Priority: {policy.priority}</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Standard Event Details Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-900/30 rounded-lg p-4 border border-gray-700">
              <label className="text-xs text-gray-400 uppercase font-medium mb-1 block">Event Type</label>
              <p className="text-white font-medium capitalize">
                {event.event_subtype ? event.event_subtype.replace(/_/g, ' ') : event.event_type}
              </p>
            </div>
            <div className="bg-gray-900/30 rounded-lg p-4 border border-gray-700">
              <label className="text-xs text-gray-400 uppercase font-medium mb-1 block">User</label>
              <p className="text-white font-medium">{event.user_email}</p>
            </div>
            <div className="bg-gray-900/30 rounded-lg p-4 border border-gray-700">
              <label className="text-xs text-gray-400 uppercase font-medium mb-1 block">Agent</label>
              <p className="text-white font-medium">{event.agent_id}</p>
            </div>
            <div className="bg-gray-900/30 rounded-lg p-4 border border-gray-700">
              <label className="text-xs text-gray-400 uppercase font-medium mb-1 block">Description</label>
              <p className="text-white font-medium text-sm">{event.description || 'N/A'}</p>
            </div>
          </div>

          {/* Raw JSON Data (Expandable) */}
          <div className="border-t border-gray-700 pt-4">
            <button
              onClick={() => setShowRawData(!showRawData)}
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors w-full"
            >
              {showRawData ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              <span className="text-sm font-medium">View Raw Event Data</span>
            </button>
            {showRawData && (
              <div className="mt-4 bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                <pre className="text-xs text-gray-300 overflow-x-auto">
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

export default function EventsPage() {
  const [selectedType, setSelectedType] = useState('all')
  const [selectedEvent, setSelectedEvent] = useState<any>(null)
  const [kqlQuery, setKqlQuery] = useState('')
  const [startTime, setStartTime] = useState<string>('')
  const [endTime, setEndTime] = useState<string>('')
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Fetch events from API
  const { data: events = [], isLoading, refetch } = useQuery({
    queryKey: ['events', { startTime, endTime }],
    queryFn: () =>
      fetchEvents({
        start_time: startTime || undefined,
        end_time: endTime || undefined,
      }),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Fetch event stats
  const { data: eventStats, refetch: refetchStats } = useQuery({
    queryKey: ['event-stats'],
    queryFn: () => getEventStats(),
    refetchInterval: 30000,
  })

  // Simple KQL parser for filtering
  const parseKQLQuery = (query: string, event: any): boolean => {
    if (!query.trim()) return true

    const lowerQuery = query.toLowerCase()
    const lowerEvent = JSON.stringify(event).toLowerCase()

    // Simple keyword search
    if (!lowerQuery.includes(':') && !lowerQuery.includes('and') && !lowerQuery.includes('or')) {
      return lowerEvent.includes(lowerQuery)
    }

    // Parse field:value patterns
    const patterns = lowerQuery.split(/\s+and\s+|\s+or\s+/i)
    let results: boolean[] = []

    patterns.forEach(pattern => {
      const match = pattern.match(/(\w+):"?([^"]+)"?/)
      if (match) {
        const [, field, value] = match
        const eventValue = (event[field] || '').toString().toLowerCase()
        results.push(eventValue.includes(value.toLowerCase()))
      } else {
        results.push(lowerEvent.includes(pattern.trim()))
      }
    })

    // Handle AND/OR logic
    if (lowerQuery.includes(' and ')) {
      return results.every(r => r)
    } else if (lowerQuery.includes(' or ')) {
      return results.some(r => r)
    }

    return results.length > 0 ? results[0] : true
  }

  // Filter events
  const filteredEvents = events.filter((event: any) => {
    // Type filter
    if (selectedType !== 'all' && event.event_type !== selectedType) {
      return false
    }

    // KQL filter
    return parseKQLQuery(kqlQuery, event)
  })

  const stats = {
    total: events.length,
    critical: events.filter((e: any) => e.severity === 'critical').length,
    blocked: events.filter((e: any) => e.action === 'blocked').length,
    usb: events.filter((e: any) => e.event_type === 'usb').length,
    cloud: events.filter((e: any) => e.event_type === 'cloud').length,
    clipboard: events.filter((e: any) => e.event_type === 'clipboard').length,
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'usb': return <Usb className="w-5 h-5" />
      case 'clipboard': return <Clipboard className="w-5 h-5" />
      case 'cloud': return <Cloud className="w-5 h-5" />
      default: return <AlertTriangle className="w-5 h-5" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-900/30 border-red-500/50'
      case 'high': return 'text-orange-400 bg-orange-900/30 border-orange-500/50'
      case 'medium': return 'text-yellow-400 bg-yellow-900/30 border-yellow-500/50'
      case 'low': return 'text-green-400 bg-green-900/30 border-green-500/50'
      default: return 'text-gray-400 bg-gray-900/30 border-gray-500/50'
    }
  }

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'blocked': return <Ban className="w-4 h-4" />
      case 'alerted': return <Bell className="w-4 h-4" />
      case 'quarantined': return <Download className="w-4 h-4" />
      default: return <Eye className="w-4 h-4" />
    }
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case 'blocked': return 'text-red-400 bg-red-900/30 border-red-500/50'
      case 'alerted': return 'text-yellow-400 bg-yellow-900/30 border-yellow-500/50'
      case 'quarantined': return 'text-blue-400 bg-blue-900/30 border-blue-500/50'
      default: return 'text-gray-400 bg-gray-900/30 border-gray-500/50'
    }
  }

  const exportEvents = () => {
    const csv = [
      ['Timestamp', 'Type', 'Severity', 'Action', 'User', 'Agent', 'Description'].join(','),
      ...filteredEvents.map((e: any) =>
        [e.timestamp, e.event_type, e.severity, e.action, e.user_email, e.agent_id, `"${e.description}"`].join(',')
      )
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `dlp-events-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Events exported successfully!')
  }

  const handleClearLogs = async () => {
    if (!confirm('Are you sure you want to clear all events? This action cannot be undone.')) {
      return
    }

    try {
      const result = await clearAllEvents()
      toast.success(`Successfully cleared ${result.deleted_count} events`)
      refetch()
      refetchStats()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to clear events')
    }
  }

  const handleManualRefresh = async () => {
    setIsRefreshing(true)
    try {
      const response = await triggerGoogleDrivePoll()
      if (response?.status === 'queued') {
        toast.success('Google Drive polling queued. Updating events…')
      } else if (response?.status === 'skipped') {
        toast.success(response?.message || 'No Google Drive policies configured. Events refreshed.')
      } else {
        toast.success(response?.message || 'Manual refresh triggered.')
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Failed to trigger manual refresh')
    } finally {
      await Promise.all([refetch(), refetchStats()])
      setIsRefreshing(false)
    }
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

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold text-white">DLP Events</h1>
            <p className="text-gray-400 mt-2">Monitor and analyze data loss prevention events in real-time</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleManualRefresh}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-600 text-gray-200 hover:border-indigo-500 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isRefreshing}
            >
              {isRefreshing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCcw className="w-4 h-4" />
              )}
              Manual Refresh
            </button>
            <button
              onClick={exportEvents}
              className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all"
              disabled={filteredEvents.length === 0}
            >
              <Download className="w-5 h-5" />
              Export Events
            </button>
            <button
              onClick={handleClearLogs}
              className="flex items-center gap-2 bg-gradient-to-r from-red-600 to-red-700 text-white px-6 py-3 rounded-xl hover:from-red-700 hover:to-red-800 shadow-lg hover:shadow-xl transition-all"
              disabled={events.length === 0}
            >
              <Trash2 className="w-5 h-5" />
              Clear Logs
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Events</p>
                <p className="text-3xl font-bold text-white mt-2">{stats.total}</p>
              </div>
              <AlertTriangle className="w-12 h-12 text-indigo-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Critical Events</p>
                <p className="text-3xl font-bold text-red-400 mt-2">{stats.critical}</p>
              </div>
              <Ban className="w-12 h-12 text-red-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Blocked</p>
                <p className="text-3xl font-bold text-red-400 mt-2">{stats.blocked}</p>
              </div>
              <Ban className="w-12 h-12 text-red-400" />
            </div>
          </div>
        </div>

        {/* Time Range + KQL Search Bar */}
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Time Range (UTC)
              </label>
              <div className="flex flex-col md:flex-row gap-3">
                <input
                  type="datetime-local"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-900/50 border-2 border-gray-600 rounded-xl text-white placeholder-gray-500 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/20 transition-all text-sm"
                />
                <input
                  type="datetime-local"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-900/50 border-2 border-gray-600 rounded-xl text-white placeholder-gray-500 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/20 transition-all text-sm"
                />
              </div>
            </div>
          </div>

          <label className="block text-sm font-medium text-gray-200 mb-3">
            <Search className="w-4 h-4 inline-block mr-2" />
            Search Events (KQL - Kibana Query Language)
          </label>
          <div className="relative">
            <input
              type="text"
              value={kqlQuery}
              onChange={(e) => setKqlQuery(e.target.value)}
              placeholder='severity:"critical" AND event_type:"usb" OR user_email:"john.doe"'
              className="w-full px-4 py-3 pr-10 bg-gray-900/50 border-2 border-gray-600 rounded-xl text-white font-mono text-sm placeholder-gray-500 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/20 transition-all"
            />
            {kqlQuery && (
              <button
                onClick={() => setKqlQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            Examples: <code className="text-indigo-400">severity:"critical"</code>, <code className="text-indigo-400">event_type:"usb" AND action:"blocked"</code>
          </div>
        </div>

        {/* Event Type Filter */}
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={() => setSelectedType('all')}
            className={`px-4 py-2 rounded-lg border transition-all ${
              selectedType === 'all'
                ? 'bg-indigo-900/30 border-indigo-500 text-white'
                : 'bg-gray-800/30 border-gray-600 text-gray-400 hover:border-gray-500'
            }`}
          >
            <Filter className="w-4 h-4 inline-block mr-2" />
            All Events ({events.length})
          </button>
          <button
            onClick={() => setSelectedType('usb')}
            className={`px-4 py-2 rounded-lg border transition-all ${
              selectedType === 'usb'
                ? 'bg-indigo-900/30 border-indigo-500 text-white'
                : 'bg-gray-800/30 border-gray-600 text-gray-400 hover:border-gray-500'
            }`}
          >
            <Usb className="w-4 h-4 inline-block mr-2" />
            USB ({stats.usb})
          </button>
          <button
            onClick={() => setSelectedType('cloud')}
            className={`px-4 py-2 rounded-lg border transition-all ${
              selectedType === 'cloud'
                ? 'bg-indigo-900/30 border-indigo-500 text-white'
                : 'bg-gray-800/30 border-gray-600 text-gray-400 hover:border-gray-500'
            }`}
          >
            <Cloud className="w-4 h-4 inline-block mr-2" />
            Cloud ({stats.cloud})
          </button>
          <button
            onClick={() => setSelectedType('clipboard')}
            className={`px-4 py-2 rounded-lg border transition-all ${
              selectedType === 'clipboard'
                ? 'bg-indigo-900/30 border-indigo-500 text-white'
                : 'bg-gray-800/30 border-gray-600 text-gray-400 hover:border-gray-500'
            }`}
          >
            <Clipboard className="w-4 h-4 inline-block mr-2" />
            Clipboard ({stats.clipboard})
          </button>
        </div>

        {/* Events List */}
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl border border-gray-700/50 overflow-hidden">
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-white">Event Log</h2>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center p-12">
              <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center">
              <AlertTriangle className="w-16 h-16 text-gray-600 mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">No Events Found</h3>
              <p className="text-gray-400 mb-6">
                {kqlQuery
                  ? 'No events match your search query. Try adjusting your KQL filter.'
                  : 'No DLP events have been logged yet. Events will appear here when agents detect policy violations.'}
              </p>
              {kqlQuery && (
                <button
                  onClick={() => setKqlQuery('')}
                  className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all"
                >
                  Clear Search Filter
                </button>
              )}
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {filteredEvents.map((event: any) => (
                <div
                  key={event.event_id}
                  onClick={() => setSelectedEvent(event)}
                  className="p-6 hover:bg-gray-700/30 cursor-pointer transition-colors"
                >
                  <div className="flex items-start gap-4">
                    <div className={`p-3 rounded-xl border ${getSeverityColor(event.severity)}`}>
                      {getTypeIcon(event.event_type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-white font-semibold">{event.description}</h3>
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-medium uppercase ${getSeverityColor(event.severity)}`}>
                          {event.severity}
                        </span>
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-medium uppercase ${getActionColor(event.action)}`}>
                          {getActionIcon(event.action)}
                          {event.action}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-400">
                        <span>User: <span className="text-white font-medium">{event.user_email}</span></span>
                        <span>Agent: <span className="text-white font-medium">{event.agent_id}</span></span>
                        <span>{formatDateTimeIST(event.timestamp)}</span>
                      </div>
                      {Array.isArray(event.matched_policies) && event.matched_policies.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {event.matched_policies
                            .map((policy: any) => policy?.policy_name)
                            .filter(Boolean)
                            .map((name: string, idx: number) => (
                              <span
                                key={`${event.event_id}-policy-${idx}`}
                                className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-indigo-900/50 border border-indigo-500/40 text-indigo-200"
                              >
                                {name}
                              </span>
                            ))}
                        </div>
                      )}
                      {event.details && (
                        <p className="text-gray-400 text-sm mt-2">{event.details?.file_name || event.details}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Event Details Modal */}
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
    </DashboardLayout>
  )
}
