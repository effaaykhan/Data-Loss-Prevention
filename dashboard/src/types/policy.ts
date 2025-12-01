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
  | 'google_drive_cloud_monitoring'

export type PolicySeverity = 'low' | 'medium' | 'high' | 'critical'
export type ClipboardAction = 'alert' | 'log'
// NOTE: Quarantine is not yet fully implemented (no physical move), so it is hidden from UI actions for now.
export type FileSystemAction = 'alert' | 'block' | 'log'
export type USBDeviceAction = 'alert' | 'log' | 'block'
// Same as FileSystemAction: quarantine is disabled until fully implemented.
export type USBTransferAction = 'block' | 'alert'

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

export interface GoogleDriveLocalConfig {
  basePath: string  // Default: "G:\\My Drive\\"
  monitoredFolders: string[]  // Subfolders within basePath
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

export interface GoogleDriveCloudConfig {
  connectionId: string
  protectedFolders: Array<{
    id: string
    name: string
    path?: string
  }>
  pollingInterval: number // minutes
  action: 'log'
}

export type PolicyConfig = 
  | ClipboardConfig 
  | FileSystemConfig 
  | USBDeviceConfig 
  | USBTransferConfig 
  | GoogleDriveLocalConfig
  | GoogleDriveCloudConfig

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


