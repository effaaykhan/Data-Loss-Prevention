'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { AlertTriangle, Usb, Clipboard, Cloud, Ban, Bell, Eye, Filter, Download, Search, Loader2, X } from 'lucide-react'
import { getEvents as fetchEvents, getEventStats } from '@/lib/api'
import { formatDateTimeIST } from '@/lib/utils'
import toast from 'react-hot-toast'

export default function EventsPage() {
  const [selectedType, setSelectedType] = useState('all')
  const [selectedEvent, setSelectedEvent] = useState<any>(null)
  const [kqlQuery, setKqlQuery] = useState('')
  const [startTime, setStartTime] = useState<string>('')
  const [endTime, setEndTime] = useState<string>('')

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
              onClick={() => {
                refetch()
                refetchStats()
              }}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-600 text-gray-200 hover:border-indigo-500 hover:text-white transition-colors"
            >
              <Loader2 className="w-4 h-4 animate-spin-slow" />
              Refresh
            </button>
            <button
              onClick={exportEvents}
              className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all"
              disabled={filteredEvents.length === 0}
            >
              <Download className="w-5 h-5" />
              Export Events
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
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedEvent(null)}>
            <div className="bg-gray-800 rounded-2xl max-w-2xl w-full border border-gray-700" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between p-6 border-b border-gray-700">
                <h3 className="text-2xl font-bold text-white">Event Details</h3>
                <button onClick={() => setSelectedEvent(null)} className="text-gray-400 hover:text-white transition-colors">
                  <X className="w-6 h-6" />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="text-sm text-gray-400">Description</label>
                  <p className="text-white font-medium">{selectedEvent.description}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-400">Event Type</label>
                    <p className="text-white font-medium capitalize">{selectedEvent.event_type}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Severity</label>
                    <p className="text-white font-medium capitalize">{selectedEvent.severity}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Action Taken</label>
                    <p className="text-white font-medium capitalize">{selectedEvent.action}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Timestamp</label>
                    <p className="text-white font-medium">{formatDateTimeIST(selectedEvent.timestamp)}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">User</label>
                    <p className="text-white font-medium">{selectedEvent.user_email}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Agent</label>
                    <p className="text-white font-medium">{selectedEvent.agent_id}</p>
                  </div>
                </div>
                {selectedEvent.details && (
                  <div>
                    <label className="text-sm text-gray-400">Additional Details</label>
                    <p className="text-white font-mono text-sm bg-gray-900/50 p-4 rounded-lg">
                      {JSON.stringify(selectedEvent.details, null, 2)}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
