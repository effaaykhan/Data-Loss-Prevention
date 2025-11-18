import { useState } from 'react'
import { Plus, Shield, CheckCircle, XCircle } from 'lucide-react'
import PolicyCreatorModal from '@/components/policies/PolicyCreatorModal'
import PolicyTable from '@/components/policies/PolicyTable'
import PolicyDetailsModal from '@/components/policies/PolicyDetailsModal'
import { Policy } from '@/mocks/mockPolicies'
import { mockPolicies } from '@/mocks/mockPolicies'
import toast from 'react-hot-toast'

export default function PoliciesPage() {
  const [showModal, setShowModal] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null)
  const [policies, setPolicies] = useState<Policy[]>(mockPolicies)
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null)
  const [showDetailsModal, setShowDetailsModal] = useState(false)

  const handleCreatePolicy = () => {
    setEditingPolicy(null)
    setShowModal(true)
  }

  const handleSavePolicy = (policyData: Partial<Policy>) => {
    if (editingPolicy) {
      // Update existing policy
      const updatedPolicies = policies.map(p => 
        p.id === editingPolicy.id 
          ? { ...p, ...policyData, updatedAt: new Date().toISOString() } as Policy
          : p
      )
      setPolicies(updatedPolicies)
      toast.success('Policy updated successfully!')
    } else {
      // Create new policy
      const newPolicy: Policy = {
        ...policyData,
        id: `policy-${Date.now()}`,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        violations: 0
      } as Policy
      setPolicies([...policies, newPolicy])
      toast.success('Policy created successfully!')
    }
    setShowModal(false)
    setEditingPolicy(null)
  }

  const handleViewDetails = (policy: Policy) => {
    setSelectedPolicy(policy)
    setShowDetailsModal(true)
  }

  const handleEdit = (policy: Policy) => {
    setEditingPolicy(policy)
    setShowModal(true)
  }

  const handleDuplicate = (policy: Policy) => {
    const duplicatedPolicy: Policy = {
      ...policy,
      id: `policy-${Date.now()}`,
      name: `${policy.name} (Copy)`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      violations: 0,
      enabled: false, // Start as inactive
    }
    setEditingPolicy(duplicatedPolicy)
    setShowModal(true)
  }

  const handleToggleStatus = (policy: Policy) => {
    const updatedPolicies = policies.map(p =>
      p.id === policy.id
        ? { ...p, enabled: !p.enabled, updatedAt: new Date().toISOString() } as Policy
        : p
    )
    setPolicies(updatedPolicies)
    toast.success(`Policy ${!policy.enabled ? 'activated' : 'deactivated'} successfully!`)
  }

  const handleDelete = (policy: Policy) => {
    if (!confirm(`Are you sure you want to delete "${policy.name}"? This action cannot be undone.`)) {
      return
    }
    const updatedPolicies = policies.filter(p => p.id !== policy.id)
    setPolicies(updatedPolicies)
    toast.success('Policy deleted successfully!')
  }

  const activePolicies = policies.filter(p => p.enabled)
  const inactivePolicies = policies.filter(p => !p.enabled)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">DLP Policies</h1>
        <p className="mt-1 text-sm text-gray-600">
          Create and manage data loss prevention policies
        </p>
      </div>

      {/* Header Actions */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex-1" />
        <div className="flex items-center gap-3">
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
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Policies</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">{policies.length}</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-100 text-blue-600">
              <Shield className="h-6 w-6" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Policies</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">{activePolicies.length}</p>
            </div>
            <div className="p-3 rounded-lg bg-green-100 text-green-600">
              <CheckCircle className="h-6 w-6" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Inactive Policies</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">{inactivePolicies.length}</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-100 text-gray-600">
              <XCircle className="h-6 w-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Active Policies Table */}
      <PolicyTable
        title="Active Policies"
        policies={activePolicies}
        emptyMessage="No active policies"
        onViewDetails={handleViewDetails}
        onEdit={handleEdit}
        onDuplicate={handleDuplicate}
        onToggleStatus={handleToggleStatus}
        onDelete={handleDelete}
      />

      {/* Inactive Policies Table */}
      <PolicyTable
        title="Inactive Policies"
        policies={inactivePolicies}
        emptyMessage="No inactive policies"
        onViewDetails={handleViewDetails}
        onEdit={handleEdit}
        onDuplicate={handleDuplicate}
        onToggleStatus={handleToggleStatus}
        onDelete={handleDelete}
      />

      {/* Policy Creator Modal */}
      <PolicyCreatorModal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false)
          setEditingPolicy(null)
        }}
        onSave={handleSavePolicy}
        editingPolicy={editingPolicy}
      />

      {/* Policy Details Modal */}
      <PolicyDetailsModal
        isOpen={showDetailsModal}
        policy={selectedPolicy}
        onClose={() => {
          setShowDetailsModal(false)
          setSelectedPolicy(null)
        }}
      />
    </div>
  )
}
