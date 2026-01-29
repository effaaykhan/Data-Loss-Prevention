# CyberSentinel DLP Agent - Uninstallation Script
# Requires Administrator privileges

#Requires -RunAsAdministrator

# Configuration
$INSTALL_DIR = "C:\Program Files\CyberSentinel"
$EXE_NAME = "cybersentinel_agent.exe"
$VBS_NAME = "launch_agent.vbs"
$TASK_NAME = "CyberSentinel DLP Agent"
$PROCESS_NAME = "cybersentinel_agent"

# Colors for output
function Write-ColorOutput {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        [ValidateSet("Info", "Success", "Warning", "Error")]
        [string]$Type = "Info"
    )
    
    switch ($Type) {
        "Info"    { Write-Host $Message -ForegroundColor Cyan }
        "Success" { Write-Host $Message -ForegroundColor Green }
        "Warning" { Write-Host $Message -ForegroundColor Yellow }
        "Error"   { Write-Host $Message -ForegroundColor Red }
    }
}

# Banner
Clear-Host
Write-Host "============================================================" -ForegroundColor Red
Write-Host "  CyberSentinel DLP Agent - Uninstallation Script          " -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""

# Check if agent is installed
if (-not (Test-Path $INSTALL_DIR)) {
    Write-ColorOutput "CyberSentinel Agent is not installed." -Type "Warning"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}

# Display installation info
Write-ColorOutput "Found CyberSentinel Agent installation:" -Type "Info"
Write-Host "  Location: $INSTALL_DIR"

$exePath = Join-Path $INSTALL_DIR $EXE_NAME
if (Test-Path $exePath) {
    $fileInfo = Get-Item $exePath
    Write-Host "  Executable: $EXE_NAME (Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB)"
    Write-Host "  Created: $($fileInfo.CreationTime)"
}

$configPath = Join-Path $INSTALL_DIR "agent_config.json"
if (Test-Path $configPath) {
    Write-Host "  Configuration: agent_config.json"
}

$vbsPath = Join-Path $INSTALL_DIR $VBS_NAME
if (Test-Path $vbsPath) {
    Write-Host "  Launcher: $VBS_NAME"
}

Write-Host ""

# Confirmation
Write-ColorOutput "WARNING: This will completely remove the CyberSentinel Agent from your system." -Type "Warning"
Write-Host ""
$confirm = Read-Host "Are you sure you want to uninstall? (Y/N)"

if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-ColorOutput "Uninstallation cancelled by user." -Type "Info"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}

Write-Host ""
Write-ColorOutput "Starting uninstallation process..." -Type "Info"
Write-Host ""

# Step 1: Stop Running Process
Write-ColorOutput "Step 1: Stopping agent process..." -Type "Info"

try {
    $process = Get-Process -Name $PROCESS_NAME -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-ColorOutput "Found running process (PID: $($process.Id))" -Type "Info"
        Stop-Process -Name $PROCESS_NAME -Force -ErrorAction Stop
        Start-Sleep -Seconds 2
        
        # Verify process stopped
        $stillRunning = Get-Process -Name $PROCESS_NAME -ErrorAction SilentlyContinue
        if ($stillRunning) {
            Write-ColorOutput "Warning: Process may still be running. Waiting..." -Type "Warning"
            Start-Sleep -Seconds 3
            Stop-Process -Name $PROCESS_NAME -Force -ErrorAction SilentlyContinue
        }
        
        Write-ColorOutput "Agent process stopped successfully" -Type "Success"
    } else {
        Write-ColorOutput "Agent process is not running" -Type "Info"
    }
} catch {
    Write-ColorOutput "Error stopping process: $($_.Exception.Message)" -Type "Warning"
    Write-ColorOutput "Continuing with uninstallation..." -Type "Info"
}

Write-Host ""

# Step 2: Remove Scheduled Task
Write-ColorOutput "Step 2: Removing scheduled task..." -Type "Info"

try {
    $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
    
    if ($task) {
        Unregister-ScheduledTask -TaskName $TASK_NAME -Confirm:$false -ErrorAction Stop
        Write-ColorOutput "Scheduled task removed successfully" -Type "Success"
    } else {
        Write-ColorOutput "Scheduled task not found (may have been removed already)" -Type "Info"
    }
} catch {
    Write-ColorOutput "Error removing scheduled task: $($_.Exception.Message)" -Type "Warning"
    Write-ColorOutput "You may need to remove it manually from Task Scheduler" -Type "Warning"
}

Write-Host ""

# Step 3: Remove Startup Folder Shortcut (if exists as fallback)
Write-ColorOutput "Step 3: Removing startup folder shortcut..." -Type "Info"

try {
    $startupFolder = [Environment]::GetFolderPath('Startup')
    $shortcutPath = Join-Path $startupFolder "CyberSentinel DLP Agent.lnk"
    
    if (Test-Path $shortcutPath) {
        Remove-Item -Path $shortcutPath -Force -ErrorAction Stop
        Write-ColorOutput "Startup shortcut removed successfully" -Type "Success"
    } else {
        Write-ColorOutput "Startup shortcut not found (may not have been created)" -Type "Info"
    }
} catch {
    Write-ColorOutput "Error removing startup shortcut: $($_.Exception.Message)" -Type "Warning"
}

Write-Host ""

# Step 4: Backup Configuration (Optional)
Write-ColorOutput "Step 4: Configuration backup..." -Type "Info"

$backupConfig = Read-Host "Do you want to backup the configuration file? (Y/N)"

if ($backupConfig -eq "Y" -or $backupConfig -eq "y") {
    try {
        if (Test-Path $configPath) {
            $backupDir = Join-Path $env:USERPROFILE "CyberSentinel_Backup"
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupFile = Join-Path $backupDir "agent_config_$timestamp.json"
            
            if (-not (Test-Path $backupDir)) {
                New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
            }
            
            Copy-Item -Path $configPath -Destination $backupFile -Force
            Write-ColorOutput "Configuration backed up to: $backupFile" -Type "Success"
        } else {
            Write-ColorOutput "Configuration file not found, skipping backup" -Type "Info"
        }
    } catch {
        Write-ColorOutput "Error backing up configuration: $($_.Exception.Message)" -Type "Warning"
    }
}

Write-Host ""

# Step 5: Remove Installation Directory
Write-ColorOutput "Step 5: Removing installation directory..." -Type "Info"

try {
    # Wait a moment to ensure all file handles are released
    Start-Sleep -Seconds 2
    
    if (Test-Path $INSTALL_DIR) {
        Remove-Item -Path $INSTALL_DIR -Recurse -Force -ErrorAction Stop
        Write-ColorOutput "Installation directory removed successfully" -Type "Success"
    } else {
        Write-ColorOutput "Installation directory not found" -Type "Info"
    }
} catch {
    Write-ColorOutput "Error removing installation directory: $($_.Exception.Message)" -Type "Error"
    Write-ColorOutput "You may need to manually delete: $INSTALL_DIR" -Type "Warning"
    Write-Host ""
    Write-Host "Common reasons for this error:"
    Write-Host "  - Files are still in use (restart may be required)"
    Write-Host "  - Insufficient permissions"
    Write-Host "  - Antivirus software blocking deletion"
}

Write-Host ""

# Step 6: Clean up any remaining processes
Write-ColorOutput "Step 6: Final cleanup..." -Type "Info"

try {
    # Double-check process is stopped
    $remainingProcess = Get-Process -Name $PROCESS_NAME -ErrorAction SilentlyContinue
    if ($remainingProcess) {
        Stop-Process -Name $PROCESS_NAME -Force -ErrorAction SilentlyContinue
        Write-ColorOutput "Cleaned up remaining process" -Type "Info"
    }
    
    Write-ColorOutput "Cleanup completed" -Type "Success"
} catch {
    Write-ColorOutput "Minor cleanup issues encountered (can be ignored)" -Type "Info"
}

Write-Host ""

# Verify Uninstallation
Write-ColorOutput "Verifying uninstallation..." -Type "Info"

$uninstallSuccess = $true

if (Test-Path $INSTALL_DIR) {
    Write-ColorOutput "WARNING: Installation directory still exists" -Type "Warning"
    $uninstallSuccess = $false
}

$taskCheck = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
if ($taskCheck) {
    Write-ColorOutput "WARNING: Scheduled task still exists" -Type "Warning"
    $uninstallSuccess = $false
}

$processCheck = Get-Process -Name $PROCESS_NAME -ErrorAction SilentlyContinue
if ($processCheck) {
    Write-ColorOutput "WARNING: Process is still running" -Type "Warning"
    $uninstallSuccess = $false
}

Write-Host ""

# Final Status
if ($uninstallSuccess) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "        Uninstallation Completed Successfully!             " -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "CyberSentinel DLP Agent has been completely removed from your system." -ForegroundColor Green
    Write-Host ""
    Write-Host "Removed components:" -ForegroundColor Cyan
    Write-Host "  - Agent executable and configuration"
    Write-Host "  - VBScript launcher"
    Write-Host "  - Scheduled task for auto-start"
    Write-Host "  - Startup folder shortcut (if present)"
    Write-Host ""
    Write-Host "Thank you for using CyberSentinel DLP Agent!" -ForegroundColor Cyan
} else {
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "          Uninstallation Completed with Warnings           " -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Some components may require manual removal:" -ForegroundColor Yellow
    Write-Host "  1. Delete directory: $INSTALL_DIR"
    Write-Host "  2. Remove scheduled task from Task Scheduler: $TASK_NAME"
    Write-Host "  3. Delete startup shortcut: $([Environment]::GetFolderPath('Startup'))\CyberSentinel DLP Agent.lnk"
    Write-Host "  4. Restart your computer if files are locked"
    Write-Host ""
    Write-Host "A system restart may resolve these issues." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

# Pause before exit
Write-Host ""
Read-Host "Press Enter to exit"