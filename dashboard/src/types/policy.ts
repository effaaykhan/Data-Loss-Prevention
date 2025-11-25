/**
 * Policy Type Definitions
 * Shared types for policy management
 */

export type PolicyType = 
  | 'clipboard_monitoring'
  | 'file_system_monitoring'
  | 'usb_device_monitoring'
  | 'usb_file_transfer_monitoring'
  | 'google_drive_local_monitoring'

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
    copy: boolean
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

export interface GoogleDriveLocalConfig {
  basePath: string  // Default: "G:\\My Drive\\"
  monitoredFolders: string[]  // Subfolders within basePath
  fileExtensions?: string[]
  events: {
    create: boolean
    modify: boolean
    delete: boolean
    move: boolean
    copy: boolean
  }
  action: FileSystemAction
  quarantinePath?: string
}

export type PolicyConfig = ClipboardConfig | FileSystemConfig | USBDeviceConfig | USBTransferConfig | GoogleDriveLocalConfig

export interface Policy {
  id: string
  name: string
  description: string
  type: PolicyType
  severity: PolicySeverity
  priority: number
  enabled: boolean
  config: PolicyConfig
  createdAt: string
  updatedAt: string
  createdBy?: string
  violations?: number
  lastViolation?: string
}



