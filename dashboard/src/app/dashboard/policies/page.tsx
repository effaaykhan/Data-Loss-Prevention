'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPolicies, getPolicyStats, createPolicy, updatePolicy, deletePolicy } from '@/lib/api'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { FileText, Shield, CheckCircle, Clock, Plus, Edit, Trash2, Copy, X, AlertTriangle, Ban, Bell, Archive, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

interface Rule {
  id: string
  type: 'pattern' | 'file_type' | 'destination' | 'size'
  condition: string
  value: string
}

interface Policy {
  id: number
  policy_id?: string
  name: string
  description: string
  status: 'active' | 'inactive'
  severity: 'low' | 'medium' | 'high' | 'critical'
  action: 'block' | 'alert' | 'quarantine' | 'log'
  rules: Rule[]
  destinations: string[]
  fileTypes: string[]
  patterns: string[]
  violations: number
  createdAt: string
  updatedAt: string
  created_at?: string
  updated_at?: string
}

export default function PoliciesPage() {
  const queryClient = useQueryClient()

  // Fetch policies from API
  const { data: policies = [], isLoading, refetch } = useQuery({
    queryKey: ['policies'],
    queryFn: () => getPolicies(),
    refetchInterval: 30000,
  })

  // Fetch policy stats
  const { data: policyStats, refetch: refetchStats } = useQuery({
    queryKey: ['policy-stats'],
    queryFn: () => getPolicyStats(),
    refetchInterval: 30000,
  })

  const [showModal, setShowModal] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null)

  // Form state
  const [policyForm, setPolicyForm] = useState({
    name: '',
    description: '',
    severity: 'medium' as Policy['severity'],
    action: 'alert' as Policy['action'],
    destinations: [] as string[],
    fileTypes: [] as string[],
    patterns: [] as string[],
  })

  const stats = {
    total: policyStats?.total_policies || policies.length || 0,
    active: policyStats?.active_policies || policies.filter((p: any) => p.status === 'active').length || 0,
    violations: policyStats?.total_violations || policies.reduce((sum: number, p: any) => sum + (p.violations || 0), 0) || 0,
  }

  const resetForm = () => {
    setPolicyForm({
      name: '',
      description: '',
      severity: 'medium',
      action: 'alert',
      destinations: [],
      fileTypes: [],
      patterns: [],
    })
    setEditingPolicy(null)
  }

  const handleCreatePolicy = () => {
    setShowModal(true)
    resetForm()
  }

  const handleEditPolicy = (policy: any) => {
    setEditingPolicy(policy)
    setPolicyForm({
      name: policy.name,
      description: policy.description,
      severity: policy.severity,
      action: policy.action,
      destinations: policy.destinations || [],
      fileTypes: policy.fileTypes || policy.file_types || [],
      patterns: policy.patterns || [],
    })
    setShowModal(true)
  }

  const handleSavePolicy = async () => {
    if (!policyForm.name.trim()) {
      toast.error('Policy name is required')
      return
    }

    try {
      if (editingPolicy) {
        // Update existing policy via API
        await updatePolicy(editingPolicy.policy_id || String(editingPolicy.id), policyForm)
        toast.success('Policy updated successfully!')
      } else {
        // Create new policy via API
        await createPolicy(policyForm)
        toast.success('Policy created successfully!')
      }

      // Refresh policies list
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      queryClient.invalidateQueries({ queryKey: ['policy-stats'] })

      setShowModal(false)
      resetForm()
    } catch (error) {
      toast.error('Failed to save policy')
      console.error(error)
    }
  }

  const handleDeletePolicy = async (policy: any) => {
    if (confirm('Are you sure you want to delete this policy?')) {
      try {
        await deletePolicy(policy.policy_id || String(policy.id))
        toast.success('Policy deleted successfully!')
        queryClient.invalidateQueries({ queryKey: ['policies'] })
        queryClient.invalidateQueries({ queryKey: ['policy-stats'] })
      } catch (error) {
        toast.error('Failed to delete policy')
        console.error(error)
      }
    }
  }

  const handleToggleStatus = async (policy: any) => {
    try {
      const newStatus = policy.status === 'active' ? 'inactive' : 'active'
      await api.updatePolicy(policy.policy_id || String(policy.id), {
        ...policy,
        status: newStatus
      })
      toast.success('Policy status updated!')
      queryClient.invalidateQueries({ queryKey: ['policies'] })
    } catch (error) {
      toast.error('Failed to update policy status')
      console.error(error)
    }
  }

  const handleDuplicatePolicy = async (policy: any) => {
    try {
      const duplicatedPolicy = {
        name: `${policy.name} (Copy)`,
        description: policy.description,
        severity: policy.severity,
        action: policy.action,
        destinations: policy.destinations || [],
        fileTypes: policy.fileTypes || policy.file_types || [],
        patterns: policy.patterns || [],
      }
      await api.createPolicy(duplicatedPolicy)
      toast.success('Policy duplicated successfully!')
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      queryClient.invalidateQueries({ queryKey: ['policy-stats'] })
    } catch (error) {
      toast.error('Failed to duplicate policy')
      console.error(error)
    }
  }

  const toggleArrayItem = (array: string[], item: string) => {
    return array.includes(item)
      ? array.filter(i => i !== item)
      : [...array, item]
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
      case 'block': return <Ban className="w-4 h-4" />
      case 'alert': return <Bell className="w-4 h-4" />
      case 'quarantine': return <Archive className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const destinationOptions = [
    { id: 'usb', name: 'USB Drives', description: 'External USB storage devices' },
    { id: 'external_drive', name: 'External Drives', description: 'Any external storage' },
    { id: 'google_drive', name: 'Google Drive', description: 'Google cloud storage' },
    { id: 'onedrive', name: 'OneDrive', description: 'Microsoft cloud storage' },
    { id: 'dropbox', name: 'Dropbox', description: 'Dropbox cloud storage' },
    { id: 's3', name: 'Amazon S3', description: 'AWS S3 buckets' },
    { id: 'clipboard', name: 'Clipboard', description: 'System clipboard' },
    { id: 'email', name: 'Email', description: 'Email attachments' },
    { id: 'network_share', name: 'Network Share', description: 'Network file shares' },
  ]

  const fileTypeOptions = [
    '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv', '.pptx', '.ppt',
    '.txt', '.zip', '.rar', '.7z', '.json', '.xml', '.sql', '.db'
  ]

  const patternOptions = [
    { id: 'ssn', name: 'Social Security Number (SSN)', example: '123-45-6789' },
    { id: 'credit_card', name: 'Credit Card Number', example: '4111-1111-1111-1111' },
    { id: 'email', name: 'Email Address', example: 'user@example.com' },
    { id: 'phone', name: 'Phone Number', example: '+1-555-123-4567' },
    { id: 'api_key', name: 'API Key', example: 'sk_live_...' },
    { id: 'password', name: 'Password Pattern', example: 'password=...' },
    { id: 'private_key', name: 'Private Key', example: '-----BEGIN PRIVATE KEY-----' },
    { id: 'internal', name: 'Internal Classification', example: 'INTERNAL' },
    { id: 'confidential', name: 'Confidential Classification', example: 'CONFIDENTIAL' },
    { id: 'restricted', name: 'Restricted Classification', example: 'RESTRICTED' },
  ]

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold text-white">DLP Policies</h1>
            <p className="text-gray-400 mt-2">Create and manage custom data loss prevention policies</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                refetch()
                refetchStats()
              }}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-600 text-gray-200 hover:border-indigo-500 hover:text-white transition-colors"
            >
              <Clock className="w-4 h-4" />
              Refresh
            </button>
            <button
              onClick={handleCreatePolicy}
              className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all"
            >
              <Plus className="w-5 h-5" />
              Create Policy
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Policies</p>
                <p className="text-3xl font-bold text-white mt-2">{stats.total}</p>
              </div>
              <FileText className="w-12 h-12 text-indigo-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Active Policies</p>
                <p className="text-3xl font-bold text-green-400 mt-2">{stats.active}</p>
              </div>
              <CheckCircle className="w-12 h-12 text-green-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-6 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Violations</p>
                <p className="text-3xl font-bold text-red-400 mt-2">{stats.violations}</p>
              </div>
              <Shield className="w-12 h-12 text-red-400" />
            </div>
          </div>
        </div>

        {/* Policies List */}
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl border border-gray-700/50 overflow-hidden">
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-white">Policy List</h2>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center p-12">
              <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
            </div>
          ) : policies.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12">
              <Shield className="w-16 h-16 text-gray-600 mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">No Policies Found</h3>
              <p className="text-gray-400 text-center max-w-md mb-6">
                Create your first DLP policy to start protecting sensitive data across your organization.
              </p>
              <button
                onClick={handleCreatePolicy}
                className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all"
              >
                <Plus className="w-5 h-5" />
                Create First Policy
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {policies.map((policy: any) => (
                <div key={policy.policy_id || policy.id} className="p-6 hover:bg-gray-700/30 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="p-3 bg-indigo-900/30 border border-indigo-500/50 rounded-lg">
                        <FileText className="w-6 h-6 text-indigo-400" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-white font-semibold text-lg">{policy.name}</h3>
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-medium uppercase ${getSeverityColor(policy.severity)}`}>
                            {policy.severity}
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-medium uppercase text-purple-400 bg-purple-900/30 border-purple-500/50">
                            {getActionIcon(policy.action)}
                            {policy.action}
                          </span>
                        </div>
                        <p className="text-gray-400 mt-1">{policy.description}</p>
                        <div className="flex items-center gap-4 mt-3 text-sm">
                          <span className="text-gray-500">Destinations: <span className="text-white font-medium">{policy.destinations?.length || 0}</span></span>
                          <span className="text-gray-500">File Types: <span className="text-white font-medium">{(policy.fileTypes || policy.file_types || []).length}</span></span>
                          <span className="text-gray-500">Patterns: <span className="text-white font-medium">{policy.patterns?.length || 0}</span></span>
                          <span className="text-gray-500">Violations: <span className="text-red-400 font-medium">{policy.violations || 0}</span></span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleStatus(policy)}
                        className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border text-sm font-medium ${
                          policy.status === 'active'
                            ? 'text-green-400 bg-green-900/30 border-green-500/50'
                            : 'text-gray-400 bg-gray-900/30 border-gray-500/50'
                        }`}
                      >
                        {policy.status === 'active' ? <CheckCircle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                        {policy.status === 'active' ? 'Active' : 'Inactive'}
                      </button>
                      <button
                        onClick={() => handleEditPolicy(policy)}
                        className="p-2 text-gray-400 hover:text-indigo-400 hover:bg-indigo-900/30 rounded-lg transition-colors"
                        title="Edit Policy"
                      >
                        <Edit className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDuplicatePolicy(policy)}
                        className="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-900/30 rounded-lg transition-colors"
                        title="Duplicate Policy"
                      >
                        <Copy className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDeletePolicy(policy)}
                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-900/30 rounded-lg transition-colors"
                        title="Delete Policy"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Create/Edit Policy Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
            <div className="bg-gray-800 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-gray-700" onClick={(e) => e.stopPropagation()}>
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
                <div>
                  <h3 className="text-2xl font-bold text-white">
                    {editingPolicy ? 'Edit Policy' : 'Create New Policy'}
                  </h3>
                  <p className="text-gray-400 mt-1">Configure your custom DLP policy</p>
                </div>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white transition-colors">
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {/* Step 1: Basic Information */}
                <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
                  <h4 className="text-lg font-semibold text-white mb-4">1. Basic Information</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-200 mb-2">Policy Name *</label>
                      <input
                        type="text"
                        value={policyForm.name}
                        onChange={(e) => setPolicyForm({ ...policyForm, name: e.target.value })}
                        className="w-full px-4 py-3 bg-gray-900/50 border-2 border-gray-600 rounded-xl text-white placeholder-gray-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/20 transition-all"
                        placeholder="e.g., Block Sensitive Data Transfer"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-200 mb-2">Description</label>
                      <textarea
                        value={policyForm.description}
                        onChange={(e) => setPolicyForm({ ...policyForm, description: e.target.value })}
                        rows={3}
                        className="w-full px-4 py-3 bg-gray-900/50 border-2 border-gray-600 rounded-xl text-white placeholder-gray-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/20 transition-all resize-none"
                        placeholder="Describe what this policy does..."
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-200 mb-2">Severity Level</label>
                        <select
                          value={policyForm.severity}
                          onChange={(e) => setPolicyForm({ ...policyForm, severity: e.target.value as Policy['severity'] })}
                          className="w-full px-4 py-3 bg-gray-900/50 border-2 border-gray-600 rounded-xl text-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/20 transition-all"
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                          <option value="critical">Critical</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-200 mb-2">Action</label>
                        <select
                          value={policyForm.action}
                          onChange={(e) => setPolicyForm({ ...policyForm, action: e.target.value as Policy['action'] })}
                          className="w-full px-4 py-3 bg-gray-900/50 border-2 border-gray-600 rounded-xl text-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/20 transition-all"
                        >
                          <option value="log">Log Only</option>
                          <option value="alert">Alert</option>
                          <option value="quarantine">Quarantine</option>
                          <option value="block">Block</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Step 2: Destinations */}
                <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
                  <h4 className="text-lg font-semibold text-white mb-4">2. Monitor Destinations</h4>
                  <p className="text-sm text-gray-400 mb-4">Select where this policy should apply</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {destinationOptions.map((dest) => (
                      <button
                        key={dest.id}
                        onClick={() => setPolicyForm({
                          ...policyForm,
                          destinations: toggleArrayItem(policyForm.destinations, dest.id)
                        })}
                        className={`p-4 rounded-lg border-2 text-left transition-all ${
                          policyForm.destinations.includes(dest.id)
                            ? 'border-indigo-500 bg-indigo-900/30 text-white'
                            : 'border-gray-600 bg-gray-900/30 text-gray-400 hover:border-gray-500'
                        }`}
                      >
                        <div className="font-medium">{dest.name}</div>
                        <div className="text-xs mt-1 opacity-70">{dest.description}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Step 3: File Types */}
                <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
                  <h4 className="text-lg font-semibold text-white mb-4">3. File Types</h4>
                  <p className="text-sm text-gray-400 mb-4">Select file extensions to monitor (leave empty for all types)</p>
                  <div className="flex flex-wrap gap-2">
                    {fileTypeOptions.map((ext) => (
                      <button
                        key={ext}
                        onClick={() => setPolicyForm({
                          ...policyForm,
                          fileTypes: toggleArrayItem(policyForm.fileTypes, ext)
                        })}
                        className={`px-4 py-2 rounded-lg border-2 transition-all font-mono text-sm ${
                          policyForm.fileTypes.includes(ext)
                            ? 'border-indigo-500 bg-indigo-900/30 text-white'
                            : 'border-gray-600 bg-gray-900/30 text-gray-400 hover:border-gray-500'
                        }`}
                      >
                        {ext}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Step 4: Sensitive Patterns */}
                <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
                  <h4 className="text-lg font-semibold text-white mb-4">4. Sensitive Data Patterns</h4>
                  <p className="text-sm text-gray-400 mb-4">Select patterns to detect in files and data</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {patternOptions.map((pattern) => (
                      <button
                        key={pattern.id}
                        onClick={() => setPolicyForm({
                          ...policyForm,
                          patterns: toggleArrayItem(policyForm.patterns, pattern.id)
                        })}
                        className={`p-4 rounded-lg border-2 text-left transition-all ${
                          policyForm.patterns.includes(pattern.id)
                            ? 'border-purple-500 bg-purple-900/30 text-white'
                            : 'border-gray-600 bg-gray-900/30 text-gray-400 hover:border-gray-500'
                        }`}
                      >
                        <div className="font-medium">{pattern.name}</div>
                        <div className="text-xs mt-1 opacity-70 font-mono">{pattern.example}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-indigo-900/20 border border-indigo-500/50 rounded-xl p-6">
                  <h4 className="text-lg font-semibold text-indigo-300 mb-3">Policy Summary</h4>
                  <div className="space-y-2 text-sm">
                    <p className="text-gray-300">
                      <span className="font-medium">Name:</span> {policyForm.name || 'Not set'}
                    </p>
                    <p className="text-gray-300">
                      <span className="font-medium">Severity:</span> <span className="uppercase">{policyForm.severity}</span>
                    </p>
                    <p className="text-gray-300">
                      <span className="font-medium">Action:</span> <span className="uppercase">{policyForm.action}</span>
                    </p>
                    <p className="text-gray-300">
                      <span className="font-medium">Destinations:</span> {policyForm.destinations.length > 0 ? policyForm.destinations.join(', ') : 'None selected'}
                    </p>
                    <p className="text-gray-300">
                      <span className="font-medium">File Types:</span> {policyForm.fileTypes.length > 0 ? policyForm.fileTypes.join(', ') : 'All types'}
                    </p>
                    <p className="text-gray-300">
                      <span className="font-medium">Patterns:</span> {policyForm.patterns.length > 0 ? policyForm.patterns.length + ' pattern(s)' : 'None selected'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex gap-3 p-6 border-t border-gray-700 sticky bottom-0 bg-gray-800">
                <button
                  onClick={handleSavePolicy}
                  className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold py-3 rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all"
                >
                  {editingPolicy ? 'Update Policy' : 'Create Policy'}
                </button>
                <button
                  onClick={() => setShowModal(false)}
                  className="px-6 bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 rounded-xl transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
