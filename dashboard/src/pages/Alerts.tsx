import { useQuery } from '@tanstack/react-query'
import { AlertCircle, CheckCircle, Clock } from 'lucide-react'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'
import { getAlerts } from '@/lib/api'
import { formatRelativeTime, getSeverityColor, cn } from '@/lib/utils'

export default function Alerts() {
  const { data: alertsData, isLoading, error, refetch } = useQuery({
    queryKey: ['alerts'],
    queryFn: getAlerts,
    refetchInterval: 10000,
  })

  if (isLoading) {
    return <LoadingSpinner size="lg" />
  }

  if (error) {
    return <ErrorMessage message="Failed to load alerts" retry={() => refetch()} />
  }

  // Handle both old format (array) and new format (object with alerts and counts)
  let alerts: any[] = []
  let counts: Record<string, number> = {}
  
  if (!alertsData) {
    // No data - use empty arrays
    alerts = []
  } else if (Array.isArray(alertsData)) {
    // Old format: direct array
    alerts = alertsData
  } else if (typeof alertsData === 'object' && alertsData !== null) {
    // New format: object with alerts and counts
    if ('alerts' in alertsData && Array.isArray(alertsData.alerts)) {
      alerts = alertsData.alerts
    }
    if ('counts' in alertsData && typeof alertsData.counts === 'object' && alertsData.counts !== null) {
      counts = alertsData.counts
    }
  }
  
  // Ensure alerts is always an array
  if (!Array.isArray(alerts)) {
    alerts = []
  }
  
  // Use API counts if available, otherwise fall back to calculating from array
  const newAlertsCount = typeof counts.new === 'number' ? counts.new : alerts.filter((a) => a && a.status === 'new').length
  const acknowledgedAlertsCount = typeof counts.acknowledged === 'number' ? counts.acknowledged : alerts.filter((a) => a && a.status === 'acknowledged').length
  const resolvedAlertsCount = typeof counts.resolved === 'number' ? counts.resolved : alerts.filter((a) => a && a.status === 'resolved').length

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
        <p className="mt-1 text-sm text-gray-600">
          Manage security alerts from DLP policies
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">New Alerts</p>
              <p className="text-2xl font-bold text-red-600">{newAlertsCount}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Clock className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Acknowledged</p>
              <p className="text-2xl font-bold text-yellow-600">
                {acknowledgedAlertsCount}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Resolved</p>
              <p className="text-2xl font-bold text-green-600">
                {resolvedAlertsCount}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="card p-0">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Recent Alerts</h3>
        </div>

        <div className="divide-y divide-gray-200">
          {!alerts || alerts.length === 0 ? (
            <div className="p-12 text-center">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 font-medium">No alerts</p>
              <p className="text-sm text-gray-500 mt-1">
                Alerts will appear here when policies trigger
              </p>
            </div>
          ) : (
            alerts?.map((alert) => (
              <div key={alert.id} className="p-4">
                <div className="flex items-start gap-4">
                  <div
                    className={cn(
                      'p-2 rounded-lg',
                      alert.severity === 'critical'
                        ? 'bg-red-100'
                        : alert.severity === 'high'
                        ? 'bg-orange-100'
                        : alert.severity === 'medium'
                        ? 'bg-yellow-100'
                        : 'bg-blue-100'
                    )}
                  >
                    <AlertCircle
                      className={cn(
                        'h-5 w-5',
                        alert.severity === 'critical'
                          ? 'text-red-600'
                          : alert.severity === 'high'
                          ? 'text-orange-600'
                          : alert.severity === 'medium'
                          ? 'text-yellow-600'
                          : 'text-blue-600'
                      )}
                    />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={cn('badge', getSeverityColor(alert.severity))}
                      >
                        {alert.severity}
                      </span>
                      {alert.status === 'new' && (
                        <span className="badge badge-danger">New</span>
                      )}
                      {alert.status === 'acknowledged' && (
                        <span className="badge badge-warning">Acknowledged</span>
                      )}
                      {alert.status === 'resolved' && (
                        <span className="badge badge-success">Resolved</span>
                      )}
                    </div>

                    <h4 className="font-medium text-gray-900">{alert.title}</h4>
                    <p className="mt-1 text-sm text-gray-600">
                      {alert.description}
                    </p>

                    <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                      <span>Agent: {alert.agent_id}</span>
                      <span>•</span>
                      <span>{formatRelativeTime(alert.created_at)}</span>
                      <span>•</span>
                      <code className="bg-gray-100 px-1 py-0.5 rounded">
                        {alert.event_id}
                      </code>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    {alert.status === 'new' && (
                      <button className="px-3 py-1 text-sm bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200">
                        Acknowledge
                      </button>
                    )}
                    {alert.status !== 'resolved' && (
                      <button className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded-lg hover:bg-green-200">
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
