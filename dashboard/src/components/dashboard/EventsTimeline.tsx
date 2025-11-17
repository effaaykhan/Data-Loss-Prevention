'use client'

import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { api } from '@/lib/api'

// IST timezone
const IST_TIMEZONE = 'Asia/Kolkata'

// Helper to format time in IST
const formatTimeIST = (date: Date) => {
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: IST_TIMEZONE,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(date)
}

export default function EventsTimeline() {
  const { data, isLoading } = useQuery({
    queryKey: ['event-timeline'],
    queryFn: () => api.getEventTimeline(24),
    refetchInterval: 60000, // Refresh every minute
  })

  if (isLoading) {
    return (
      <div className="h-80 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const chartData = data?.timeline || []

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="timestamp"
          stroke="#6b7280"
          tickFormatter={(value) => {
            return formatTimeIST(new Date(value))
          }}
        />
        <YAxis stroke="#6b7280" />
        <Tooltip
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="total_events"
          stroke="#3b82f6"
          strokeWidth={2}
          name="Total Events"
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="blocked_events"
          stroke="#ef4444"
          strokeWidth={2}
          name="Blocked"
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="critical_events"
          stroke="#f59e0b"
          strokeWidth={2}
          name="Critical"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
