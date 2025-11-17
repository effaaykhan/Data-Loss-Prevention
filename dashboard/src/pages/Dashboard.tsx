import { useQuery } from '@tanstack/react-query'
import { Server, AlertCircle, FileText, ShieldAlert } from 'lucide-react'
import StatsCard from '@/components/StatsCard'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

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

// Helper to format date/time in IST
const formatDateTimeIST = (date: Date) => {
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: IST_TIMEZONE,
    dateStyle: 'long',
    timeStyle: 'long'
  }).format(date)
}
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { getStats, getEventTimeSeries, getEventsByType, getEventsBySeverity } from '@/lib/api'

const SEVERITY_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#2563eb',
}

const TYPE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export default function Dashboard() {
  // Fetch stats
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    refetchInterval: 30000, // Refresh every 30s
  })

  // Fetch time series data
  const { data: timeSeries, isLoading: timeSeriesLoading } = useQuery({
    queryKey: ['eventTimeSeries'],
    queryFn: () => getEventTimeSeries({ interval: 'hour' }),
  })

  // Fetch events by type
  const { data: eventsByType, isLoading: typeLoading } = useQuery({
    queryKey: ['eventsByType'],
    queryFn: getEventsByType,
  })

  // Fetch events by severity
  const { data: eventsBySeverity, isLoading: severityLoading } = useQuery({
    queryKey: ['eventsBySeverity'],
    queryFn: getEventsBySeverity,
  })

  if (statsLoading) {
    return <LoadingSpinner size="lg" />
  }

  if (statsError) {
    return (
      <ErrorMessage
        message="Failed to load dashboard data. Please check if the backend is running."
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Overview of your DLP system activity
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Agents"
          value={stats?.total_agents || 0}
          icon={Server}
          color="blue"
        />
        <StatsCard
          title="Active Agents"
          value={stats?.active_agents || 0}
          icon={Server}
          color="green"
        />
        <StatsCard
          title="Total Events"
          value={stats?.total_events?.toLocaleString() || 0}
          icon={FileText}
          color="blue"
        />
        <StatsCard
          title="Critical Alerts"
          value={stats?.critical_alerts || 0}
          icon={AlertCircle}
          color="red"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Events Time Series */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Events Over Time
          </h3>
          {timeSeriesLoading ? (
            <LoadingSpinner />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timeSeries || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="timestamp"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => {
                    // Format in IST
                    return formatTimeIST(new Date(value))
                  }}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  labelFormatter={(value) => {
                    // Format in IST
                    return formatDateTimeIST(new Date(value))
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Events"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Events by Type */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Events by Type
          </h3>
          {typeLoading ? (
            <LoadingSpinner />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={eventsByType || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ type, percent }) =>
                    `${type}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {(eventsByType || []).map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={TYPE_COLORS[index % TYPE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Events by Severity */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Events by Severity
          </h3>
          {severityLoading ? (
            <LoadingSpinner />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={eventsBySeverity || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="severity" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" name="Events">
                  {(eventsBySeverity || []).map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        SEVERITY_COLORS[
                          entry.severity as keyof typeof SEVERITY_COLORS
                        ] || '#3b82f6'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Blocked Events */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            DLP Actions
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
              <div className="flex items-center gap-3">
                <ShieldAlert className="h-8 w-8 text-red-600" />
                <div>
                  <p className="font-medium text-gray-900">Blocked Events</p>
                  <p className="text-sm text-gray-600">
                    Events prevented by policies
                  </p>
                </div>
              </div>
              <span className="text-2xl font-bold text-red-600">
                {stats?.blocked_events || 0}
              </span>
            </div>

            <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-8 w-8 text-yellow-600" />
                <div>
                  <p className="font-medium text-gray-900">Active Alerts</p>
                  <p className="text-sm text-gray-600">
                    Alerts requiring attention
                  </p>
                </div>
              </div>
              <span className="text-2xl font-bold text-yellow-600">
                {stats?.critical_alerts || 0}
              </span>
            </div>

            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900">Total Events</p>
                  <p className="text-sm text-gray-600">All recorded events</p>
                </div>
              </div>
              <span className="text-2xl font-bold text-blue-600">
                {stats?.total_events?.toLocaleString() || 0}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
