/**
 * Mock Policy Data
 * Sample policies for development and testing
 */

export type PolicyType = 
  | 'clipboard_monitoring'
  | 'file_system_monitoring'
  | 'usb_device_monitoring'
  | 'usb_file_transfer_monitoring'

export type PolicySeverity = 'low' | 'medium' | 'high' | 'critical'
export type ClipboardAction = 'alert' | 'log'
export type FileSystemAction = 'alert' | 'quarantine' | 'block' | 'log'
export type USBDeviceAction = 'alert' | 'log' | 'block'
export type USBTransferAction = 'block' | 'quarantine' | 'alert'

export interface ClipboardConfig {
  patterns: {
    predefined: string[]  // ['ssn', 'credit_card', 'api_key']
    custom: Array<{ regex: string, description?: string }>
  }
  action: ClipboardAction
}

export interface FileSystemConfig {
  monitoredPaths: string[]
  fileExtensions?: string[]
  events: {
    create: boolean
    modify: boolean
    delete: boolean
    move: boolean
  }
  action: FileSystemAction
  quarantinePath?: string
}

export interface USBDeviceConfig {
  events: {
    connect: boolean
    disconnect: boolean
    fileTransfer: boolean
  }
  action: USBDeviceAction
}

export interface USBTransferConfig {
  monitoredPaths: string[]
  action: USBTransferAction
  quarantinePath?: string
}

export interface Policy {
  id: string
  name: string
  description?: string
  type: PolicyType
  enabled: boolean
  severity: PolicySeverity
  priority: number
  createdAt: string
  updatedAt: string
  createdBy?: string
  violations?: number
  lastViolation?: string
  
  // Type-specific configuration
  config: ClipboardConfig | FileSystemConfig | USBDeviceConfig | USBTransferConfig
}

// Mock policies data
export const mockPolicies: Policy[] = [
  // Active Policies
  {
    id: 'policy-001',
    name: 'Block Sensitive Data on USB',
    description: 'Prevents transfer of files containing sensitive data to USB drives',
    type: 'usb_file_transfer_monitoring',
    enabled: true,
    severity: 'critical',
    priority: 100,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-20T14:30:00Z',
    createdBy: 'admin',
    violations: 15,
    lastViolation: '2024-01-25T09:15:00Z',
    config: {
      monitoredPaths: [
        'C:\\Users\\%USERNAME%\\Documents',
        'C:\\Users\\%USERNAME%\\Desktop'
      ],
      action: 'block',
    } as USBTransferConfig
  },
  {
    id: 'policy-002',
    name: 'Monitor Clipboard for PII',
    description: 'Detects and alerts when sensitive PII is copied to clipboard',
    type: 'clipboard_monitoring',
    enabled: true,
    severity: 'high',
    priority: 90,
    createdAt: '2024-01-10T08:00:00Z',
    updatedAt: '2024-01-18T11:20:00Z',
    createdBy: 'admin',
    violations: 42,
    lastViolation: '2024-01-25T10:45:00Z',
    config: {
      patterns: {
        predefined: ['ssn', 'credit_card', 'email'],
        custom: []
      },
      action: 'alert'
    } as ClipboardConfig
  },
  {
    id: 'policy-003',
    name: 'Protect Financial Documents',
    description: 'Monitors financial document directories and quarantines suspicious files',
    type: 'file_system_monitoring',
    enabled: true,
    severity: 'high',
    priority: 85,
    createdAt: '2024-01-12T09:00:00Z',
    updatedAt: '2024-01-22T16:00:00Z',
    createdBy: 'analyst',
    violations: 8,
    lastViolation: '2024-01-24T13:30:00Z',
    config: {
      monitoredPaths: [
        'C:\\Finance',
        'C:\\Accounting'
      ],
      fileExtensions: ['.xlsx', '.xls', '.pdf', '.csv'],
      events: {
        create: true,
        modify: true,
        delete: true,
        move: true
      },
      action: 'quarantine',
      quarantinePath: 'C:\\Quarantine'
    } as FileSystemConfig
  },
  {
    id: 'policy-004',
    name: 'USB Device Connection Alerts',
    description: 'Alerts when USB devices are connected or disconnected',
    type: 'usb_device_monitoring',
    enabled: true,
    severity: 'medium',
    priority: 70,
    createdAt: '2024-01-08T07:00:00Z',
    updatedAt: '2024-01-15T12:00:00Z',
    createdBy: 'analyst',
    violations: 127,
    lastViolation: '2024-01-25T11:00:00Z',
    config: {
      events: {
        connect: true,
        disconnect: true,
        fileTransfer: false
      },
      action: 'alert'
    } as USBDeviceConfig
  },
  {
    id: 'policy-005',
    name: 'API Key Detection',
    description: 'Detects API keys in clipboard content',
    type: 'clipboard_monitoring',
    enabled: true,
    severity: 'critical',
    priority: 95,
    createdAt: '2024-01-14T10:30:00Z',
    updatedAt: '2024-01-21T15:45:00Z',
    createdBy: 'admin',
    violations: 23,
    lastViolation: '2024-01-25T08:20:00Z',
    config: {
      patterns: {
        predefined: ['api_key', 'private_key'],
        custom: [
          { regex: 'sk_live_[A-Za-z0-9]{32}', description: 'Stripe Live API Key' }
        ]
      },
      action: 'alert'
    } as ClipboardConfig
  },
  
  // Inactive Policies
  {
    id: 'policy-006',
    name: 'Legacy File Monitoring',
    description: 'Old file monitoring policy - disabled for review',
    type: 'file_system_monitoring',
    enabled: false,
    severity: 'low',
    priority: 50,
    createdAt: '2023-12-01T10:00:00Z',
    updatedAt: '2024-01-10T09:00:00Z',
    createdBy: 'admin',
    violations: 0,
    config: {
      monitoredPaths: ['C:\\OldDocuments'],
      fileExtensions: ['.txt'],
      events: {
        create: true,
        modify: false,
        delete: false,
        move: false
      },
      action: 'log'
    } as FileSystemConfig
  },
  {
    id: 'policy-007',
    name: 'Test USB Transfer Policy',
    description: 'Testing policy for USB transfers',
    type: 'usb_file_transfer_monitoring',
    enabled: false,
    severity: 'medium',
    priority: 60,
    createdAt: '2024-01-20T14:00:00Z',
    updatedAt: '2024-01-20T14:00:00Z',
    createdBy: 'analyst',
    violations: 0,
    config: {
      monitoredPaths: ['C:\\Test'],
      action: 'quarantine',
      quarantinePath: 'C:\\Quarantine\\Test'
    } as USBTransferConfig
  },
  {
    id: 'policy-008',
    name: 'Email Address Detection',
    description: 'Monitors clipboard for email addresses',
    type: 'clipboard_monitoring',
    enabled: true,
    severity: 'low',
    priority: 40,
    createdAt: '2024-01-16T11:00:00Z',
    updatedAt: '2024-01-23T09:30:00Z',
    createdBy: 'analyst',
    violations: 156,
    lastViolation: '2024-01-25T12:15:00Z',
    config: {
      patterns: {
        predefined: ['email'],
        custom: []
      },
      action: 'log'
    } as ClipboardConfig
  },
  {
    id: 'policy-009',
    name: 'Secure Folder Protection',
    description: 'Monitors secure folder for unauthorized access',
    type: 'file_system_monitoring',
    enabled: true,
    severity: 'high',
    priority: 88,
    createdAt: '2024-01-11T13:00:00Z',
    updatedAt: '2024-01-19T10:20:00Z',
    createdBy: 'admin',
    violations: 3,
    lastViolation: '2024-01-24T15:45:00Z',
    config: {
      monitoredPaths: ['C:\\Secure', 'C:\\Confidential'],
      fileExtensions: ['.docx', '.pdf', '.xlsx'],
      events: {
        create: true,
        modify: true,
        delete: true,
        move: true
      },
      action: 'alert',
    } as FileSystemConfig
  },
  {
    id: 'policy-010',
    name: 'USB File Transfer Blocking',
    description: 'Blocks all file transfers to USB devices',
    type: 'usb_file_transfer_monitoring',
    enabled: true,
    severity: 'critical',
    priority: 99,
    createdAt: '2024-01-13T08:00:00Z',
    updatedAt: '2024-01-21T14:00:00Z',
    createdBy: 'admin',
    violations: 89,
    lastViolation: '2024-01-25T13:20:00Z',
    config: {
      monitoredPaths: [
        'C:\\Users\\%USERNAME%\\Documents',
        'C:\\Users\\%USERNAME%\\Desktop',
        'C:\\Users\\%USERNAME%\\Downloads'
      ],
      action: 'block',
    } as USBTransferConfig
  },
  {
    id: 'policy-011',
    name: 'Credit Card Number Detection',
    description: 'Detects credit card numbers in clipboard',
    type: 'clipboard_monitoring',
    enabled: true,
    severity: 'high',
    priority: 92,
    createdAt: '2024-01-09T09:00:00Z',
    updatedAt: '2024-01-17T11:00:00Z',
    createdBy: 'admin',
    violations: 67,
    lastViolation: '2024-01-25T09:30:00Z',
    config: {
      patterns: {
        predefined: ['credit_card'],
        custom: []
      },
      action: 'alert'
    } as ClipboardConfig
  },
  {
    id: 'policy-012',
    name: 'Archived USB Monitoring',
    description: 'Old USB monitoring policy - archived',
    type: 'usb_device_monitoring',
    enabled: false,
    severity: 'low',
    priority: 30,
    createdAt: '2023-11-15T10:00:00Z',
    updatedAt: '2024-01-05T08:00:00Z',
    createdBy: 'admin',
    violations: 0,
    config: {
      events: {
        connect: true,
        disconnect: false,
        fileTransfer: false
      },
      action: 'log'
    } as USBDeviceConfig
  }
]

// Helper functions
export const getActivePolicies = (): Policy[] => {
  return mockPolicies.filter(p => p.enabled)
}

export const getInactivePolicies = (): Policy[] => {
  return mockPolicies.filter(p => !p.enabled)
}

export const getPolicyById = (id: string): Policy | undefined => {
  return mockPolicies.find(p => p.id === id)
}
