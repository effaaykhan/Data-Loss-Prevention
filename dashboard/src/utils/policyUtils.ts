/**
 * Policy Utility Functions
 * Helper functions for policy operations and formatting
 */

import { 
  Policy, 
  PolicyType,
  PolicySeverity,
  ClipboardConfig, 
  FileSystemConfig, 
  USBDeviceConfig, 
  USBTransferConfig 
} from '@/types/policy'
import { Clipboard, FileText, Usb, HardDrive } from 'lucide-react'

/**
 * Get icon component for policy type
 */
export const getPolicyTypeIcon = (type: PolicyType) => {
  switch (type) {
    case 'clipboard_monitoring':
      return Clipboard
    case 'file_system_monitoring':
      return FileText
    case 'usb_device_monitoring':
      return Usb
    case 'usb_file_transfer_monitoring':
      return HardDrive
    default:
      return FileText
  }
}

/**
 * Get human-readable label for policy type
 */
export const getPolicyTypeLabel = (type: PolicyType): string => {
  switch (type) {
    case 'clipboard_monitoring':
      return 'Clipboard Monitoring'
    case 'file_system_monitoring':
      return 'File System Monitoring'
    case 'usb_device_monitoring':
      return 'USB Device Monitoring'
    case 'usb_file_transfer_monitoring':
      return 'USB File Transfer Monitoring'
    default:
      return 'Unknown'
  }
}

/**
 * Format policy configuration for display
 */
export const formatPolicyConfig = (policy: Policy): string => {
  const { type, config } = policy
  
  switch (type) {
    case 'clipboard_monitoring': {
      const c = config as ClipboardConfig
      const predefined = c.patterns.predefined.map(p => {
        const labels: Record<string, string> = {
          'ssn': 'SSN',
          'credit_card': 'Credit Card',
          'email': 'Email',
          'phone': 'Phone',
          'api_key': 'API Key',
          'private_key': 'Private Key'
        }
        return labels[p] || p
      }).join(', ')
      const custom = c.patterns.custom.length > 0 
        ? `, ${c.patterns.custom.length} custom pattern(s)`
        : ''
      return `Patterns: ${predefined}${custom} | Action: ${c.action}`
    }
    
    case 'file_system_monitoring': {
      const c = config as FileSystemConfig
      const events = Object.entries(c.events)
        .filter(([_, enabled]) => enabled)
        .map(([event]) => event.charAt(0).toUpperCase() + event.slice(1))
        .join(', ')
      const paths = c.monitoredPaths.length > 0 
        ? `${c.monitoredPaths.length} path(s)`
        : 'No paths'
      return `Paths: ${paths} | Events: ${events} | Action: ${c.action}`
    }
    
    case 'usb_device_monitoring': {
      const c = config as USBDeviceConfig
      const events = Object.entries(c.events)
        .filter(([_, enabled]) => enabled)
        .map(([event]) => event.charAt(0).toUpperCase() + event.slice(1))
        .join(', ')
      return `Events: ${events} | Action: ${c.action}`
    }
    
    case 'usb_file_transfer_monitoring': {
      const c = config as USBTransferConfig
      const paths = c.monitoredPaths.length > 0 
        ? `${c.monitoredPaths.length} path(s)`
        : 'No paths'
      return `Paths: ${paths} | Action: ${c.action}`
    }
    
    default:
      return 'Unknown configuration'
  }
}

/**
 * Validate regex pattern
 */
export const validateRegex = (regex: string): { valid: boolean; error?: string } => {
  if (!regex.trim()) {
    return { valid: false, error: 'Regex pattern cannot be empty' }
  }
  
  try {
    new RegExp(regex)
    return { valid: true }
  } catch (e) {
    return { valid: false, error: 'Invalid regex pattern' }
  }
}

/**
 * Test regex against sample text
 */
export const testRegex = (regex: string, sampleText: string): boolean => {
  try {
    const pattern = new RegExp(regex)
    return pattern.test(sampleText)
  } catch {
    return false
  }
}

/**
 * Validate policy before save
 */
export const validatePolicy = (policy: Partial<Policy>): { valid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  if (!policy.name || !policy.name.trim()) {
    errors.push('Policy name is required')
  }
  
  if (!policy.type) {
    errors.push('Policy type is required')
  }
  
  if (!policy.config) {
    errors.push('Policy configuration is required')
  } else {
    // Type-specific validation
    switch (policy.type) {
      case 'clipboard_monitoring': {
        const c = policy.config as ClipboardConfig
        if (c.patterns.predefined.length === 0 && c.patterns.custom.length === 0) {
          errors.push('At least one pattern must be selected')
        }
        // Validate custom regex patterns
        c.patterns.custom.forEach((custom, index) => {
          const validation = validateRegex(custom.regex)
          if (!validation.valid) {
            errors.push(`Custom pattern ${index + 1}: ${validation.error}`)
          }
        })
        break
      }
      
      case 'file_system_monitoring': {
        const c = policy.config as FileSystemConfig
        if (c.monitoredPaths.length === 0) {
          errors.push('At least one monitored path is required')
        }
        if (!Object.values(c.events).some(v => v)) {
          errors.push('At least one event type must be selected')
        }
        break
      }
      
      case 'usb_device_monitoring': {
        const c = policy.config as USBDeviceConfig
        if (!Object.values(c.events).some(v => v)) {
          errors.push('At least one event type must be selected')
        }
        break
      }
      
      case 'usb_file_transfer_monitoring': {
        const c = policy.config as USBTransferConfig
        if (c.monitoredPaths.length === 0) {
          errors.push('At least one monitored path is required')
        }
        break
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors
  }
}

/**
 * Get severity color classes (dark theme)
 */
export const getSeverityColor = (severity: string): string => {
  switch (severity) {
    case 'critical':
      return 'text-red-400 bg-red-900/30 border-red-500/50'
    case 'high':
      return 'text-orange-400 bg-orange-900/30 border-orange-500/50'
    case 'medium':
      return 'text-yellow-400 bg-yellow-900/30 border-yellow-500/50'
    case 'low':
      return 'text-green-400 bg-green-900/30 border-green-500/50'
    default:
      return 'text-gray-400 bg-gray-900/30 border-gray-500/50'
  }
}

/**
 * Get severity color classes (light theme - Dashboard style)
 */
export const getSeverityColorLight = (severity: string): {
  bg: string
  icon: string
  badge: string
} => {
  switch (severity) {
    case 'critical':
      return {
        bg: 'bg-red-100',
        icon: 'text-red-600',
        badge: 'badge-danger'
      }
    case 'high':
      return {
        bg: 'bg-orange-100',
        icon: 'text-orange-600',
        badge: 'badge-warning'
      }
    case 'medium':
      return {
        bg: 'bg-yellow-100',
        icon: 'text-yellow-600',
        badge: 'badge-warning'
      }
    case 'low':
      return {
        bg: 'bg-green-100',
        icon: 'text-green-600',
        badge: 'badge-success'
      }
    default:
      return {
        bg: 'bg-gray-100',
        icon: 'text-gray-600',
        badge: 'badge-info'
      }
  }
}

/**
 * Transform API policy response to frontend Policy format
 */
export const transformApiPolicyToFrontend = (apiPolicy: any): Policy => {
  return {
    id: apiPolicy.id || '',
    name: apiPolicy.name || '',
    description: apiPolicy.description || '',
    type: apiPolicy.type as PolicyType,
    enabled: apiPolicy.enabled ?? true,
    severity: (apiPolicy.severity || 'medium') as PolicySeverity,
    priority: apiPolicy.priority || 100,
    createdAt: apiPolicy.created_at || new Date().toISOString(),
    updatedAt: apiPolicy.updated_at || new Date().toISOString(),
    createdBy: apiPolicy.created_by || undefined,
    violations: 0, // TODO: Get from stats endpoint
    lastViolation: undefined, // TODO: Get from stats endpoint
    config: apiPolicy.config || getDefaultConfig(apiPolicy.type as PolicyType),
  }
}

/**
 * Transform frontend Policy format to API request format
 */
export const transformFrontendPolicyToApi = (policy: Partial<Policy>): any => {
  return {
    name: policy.name || '',
    description: policy.description || '',
    type: policy.type,
    severity: policy.severity || 'medium',
    priority: policy.priority || 100,
    enabled: policy.enabled ?? true,
    config: policy.config,
    // Backend format (empty for now, will be transformed from config later)
    conditions: [],
    actions: [],
    compliance_tags: [],
  }
}

/**
 * Get default config for policy type (helper for transformation)
 */
const getDefaultConfig = (type: PolicyType): any => {
  switch (type) {
    case 'clipboard_monitoring':
      return { patterns: { predefined: [], custom: [] }, action: 'alert' }
    case 'file_system_monitoring':
      return { monitoredPaths: [], events: { create: false, modify: false, delete: false, move: false, copy: false }, action: 'alert' }
    case 'usb_device_monitoring':
      return { events: { connect: false, disconnect: false, fileTransfer: false }, action: 'alert' }
    case 'usb_file_transfer_monitoring':
      return { monitoredPaths: [], action: 'block' }
    default:
      return {}
  }
}

/**
 * Predefined pattern definitions
 */
export const predefinedPatterns = [
  { 
    id: 'ssn', 
    name: 'Social Security Number (SSN)', 
    example: '123-45-6789',
    regex: '\\b\\d{3}-\\d{2}-\\d{4}\\b'
  },
  { 
    id: 'credit_card', 
    name: 'Credit Card Number', 
    example: '4111-1111-1111-1111',
    regex: '\\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b'
  },
  { 
    id: 'email', 
    name: 'Email Address', 
    example: 'user@example.com',
    regex: '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
  },
  { 
    id: 'phone', 
    name: 'Phone Number', 
    example: '+1-555-123-4567',
    regex: '\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b'
  },
  { 
    id: 'api_key', 
    name: 'API Key', 
    example: 'sk_live_...',
    regex: '\\b[A-Za-z0-9_-]{32,}\\b'
  },
  { 
    id: 'private_key', 
    name: 'Private Key', 
    example: '-----BEGIN PRIVATE KEY-----',
    regex: '-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----'
  }
]

