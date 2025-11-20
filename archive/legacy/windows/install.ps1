# CyberSentinel DLP Agent - Windows Installation Script
# One-liner: iwr -useb https://raw.githubusercontent.com/YOUR_ORG/cybersentinel-dlp/main/agents/windows/install.ps1 | iex

param(
    [string]$ManagerUrl = "https://localhost:55000",
    [string]$InstallDir = "C:\Program Files\CyberSentinel",
    [string]$ConfigDir = "C:\ProgramData\CyberSentinel",
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CyberSentinel DLP Agent Installer v2.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[ERROR] This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Uninstall mode
if ($Uninstall) {
    Write-Host "[*] Uninstalling CyberSentinel DLP Agent..." -ForegroundColor Yellow

    # Stop service
    try {
        Stop-Service -Name "CyberSentinelAgent" -ErrorAction SilentlyContinue
        Write-Host "[+] Service stopped" -ForegroundColor Green
    } catch {
        Write-Host "[-] Service not running" -ForegroundColor Gray
    }

    # Remove service
    try {
        sc.exe delete "CyberSentinelAgent"
        Write-Host "[+] Service removed" -ForegroundColor Green
    } catch {
        Write-Host "[-] Service not found" -ForegroundColor Gray
    }

    # Remove files
    if (Test-Path $InstallDir) {
        Remove-Item -Path $InstallDir -Recurse -Force
        Write-Host "[+] Installation directory removed" -ForegroundColor Green
    }

    if (Test-Path $ConfigDir) {
        $response = Read-Host "Remove configuration directory? (y/N)"
        if ($response -eq "y" -or $response -eq "Y") {
            Remove-Item -Path $ConfigDir -Recurse -Force
            Write-Host "[+] Configuration directory removed" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "[+] Uninstallation complete!" -ForegroundColor Green
    exit 0
}

# Installation mode
Write-Host "[*] Installing CyberSentinel DLP Agent..." -ForegroundColor Yellow
Write-Host "    Manager URL: $ManagerUrl" -ForegroundColor Gray
Write-Host "    Install Dir: $InstallDir" -ForegroundColor Gray
Write-Host "    Config Dir:  $ConfigDir" -ForegroundColor Gray
Write-Host ""

# Check Python
Write-Host "[1/8] Checking Python installation..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
$majorVersion = [int]$Matches[1]
$minorVersion = [int]$Matches[2]

if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 8)) {
    Write-Host "[ERROR] Python 3.8+ is required (found: $pythonVersion)" -ForegroundColor Red
    exit 1
}

Write-Host "[+] Python version: $pythonVersion" -ForegroundColor Green

# Create directories
Write-Host "[2/8] Creating directories..." -ForegroundColor Cyan
New-Item -Path $InstallDir -ItemType Directory -Force | Out-Null
New-Item -Path $ConfigDir -ItemType Directory -Force | Out-Null
Write-Host "[+] Directories created" -ForegroundColor Green

# Download agent code
Write-Host "[3/8] Downloading agent files..." -ForegroundColor Cyan

# Create directory structure
$dirs = @(
    "$InstallDir\common",
    "$InstallDir\common\monitors",
    "$InstallDir\windows"
)

foreach ($dir in $dirs) {
    New-Item -Path $dir -ItemType Directory -Force | Out-Null
}

# Base URL for agent files
$baseUrl = "https://raw.githubusercontent.com/YOUR_ORG/cybersentinel-dlp/main/agents"

# Download files
$files = @{
    "common/__init__.py" = "$InstallDir\common\__init__.py"
    "common/base_agent.py" = "$InstallDir\common\base_agent.py"
    "common/monitors/__init__.py" = "$InstallDir\common\monitors\__init__.py"
    "common/monitors/file_monitor.py" = "$InstallDir\common\monitors\file_monitor.py"
    "common/monitors/clipboard_monitor.py" = "$InstallDir\common\monitors\clipboard_monitor.py"
    "common/monitors/usb_monitor.py" = "$InstallDir\common\monitors\usb_monitor.py"
    "windows/__init__.py" = "$InstallDir\windows\__init__.py"
    "windows/agent.py" = "$InstallDir\windows\agent.py"
    "windows/clipboard_monitor_windows.py" = "$InstallDir\windows\clipboard_monitor_windows.py"
    "windows/usb_monitor_windows.py" = "$InstallDir\windows\usb_monitor_windows.py"
    "requirements.txt" = "$InstallDir\requirements.txt"
}

# For local testing, use local files instead
Write-Host "[*] Using local installation (update baseUrl for remote installation)" -ForegroundColor Yellow
$localAgentPath = Split-Path -Parent $PSScriptRoot

foreach ($file in $files.Keys) {
    $sourcePath = Join-Path $localAgentPath $file
    $destPath = $files[$file]

    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $destPath -Force
    } else {
        Write-Host "[-] Warning: $sourcePath not found" -ForegroundColor Yellow
    }
}

Write-Host "[+] Agent files downloaded" -ForegroundColor Green

# Install Python dependencies
Write-Host "[4/8] Installing Python dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet
python -m pip install -r "$InstallDir\requirements.txt" --quiet
Write-Host "[+] Dependencies installed" -ForegroundColor Green

# Create configuration file
Write-Host "[5/8] Creating configuration file..." -ForegroundColor Cyan

$username = $env:USERNAME
$configContent = @"
# CyberSentinel DLP Agent Configuration
# Auto-generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

agent:
  id: ""  # Auto-assigned by manager
  name: "$env:COMPUTERNAME"
  manager_url: "$ManagerUrl"
  registration_key: ""  # Auto-generated after registration
  heartbeat_interval: 60  # seconds

monitoring:
  file_system:
    enabled: true
    paths:
      - "C:/Users/$username/Desktop"
      - "C:/Users/$username/Documents"
      - "C:/Users/$username/Downloads"
    extensions:
      - .pdf
      - .docx
      - .xlsx
      - .txt
      - .csv
      - .pptx
    exclude_patterns:
      - "*/node_modules/*"
      - "*/.git/*"
      - "*/venv/*"

  clipboard:
    enabled: true
    poll_interval: 2  # seconds

  usb:
    enabled: true
    poll_interval: 5  # seconds

  network:
    enabled: false

classification:
  local:
    enabled: true
    patterns:
      - credit_card
      - ssn
      - email

performance:
  max_events_per_minute: 100
  max_event_size: 1048576  # 1MB
  batch_size: 10
  queue_size: 1000

logging:
  level: INFO
  file: "$ConfigDir/agent.log"
  max_size: 10485760  # 10MB
  max_files: 5
"@

$configPath = "$ConfigDir\agent.yml"
Set-Content -Path $configPath -Value $configContent
Write-Host "[+] Configuration file created: $configPath" -ForegroundColor Green

# Create Windows service
Write-Host "[6/8] Creating Windows service..." -ForegroundColor Cyan

# Create service wrapper script
$serviceScript = @"
import sys
import os

# Add agent directory to path
sys.path.insert(0, r'$InstallDir')

# Set config path
os.environ['CYBERSENTINEL_CONFIG'] = r'$configPath'

# Import and run agent
from windows.agent import main
import asyncio

if __name__ == '__main__':
    asyncio.run(main())
"@

$serviceScriptPath = "$InstallDir\service.py"
Set-Content -Path $serviceScriptPath -Value $serviceScript

# Install NSSM (Non-Sucking Service Manager) for service management
# For production, use proper Windows service or scheduled task

Write-Host "[+] Service script created" -ForegroundColor Green

# Register agent with manager
Write-Host "[7/8] Registering agent with manager..." -ForegroundColor Cyan
Write-Host "    Manager URL: $ManagerUrl" -ForegroundColor Gray

# Test connection
try {
    $response = Invoke-WebRequest -Uri "$ManagerUrl/health" -Method GET -UseBasicParsing -TimeoutSec 5
    Write-Host "[+] Manager is reachable" -ForegroundColor Green
} catch {
    Write-Host "[-] Warning: Cannot reach manager at $ManagerUrl" -ForegroundColor Yellow
    Write-Host "    Agent will attempt registration on first start" -ForegroundColor Gray
}

# Start agent
Write-Host "[8/8] Starting agent..." -ForegroundColor Cyan

# For now, create a scheduled task to run on startup
$taskName = "CyberSentinelAgent"
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "`"$serviceScriptPath`"" -WorkingDirectory $InstallDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    Write-Host "[+] Agent started as scheduled task" -ForegroundColor Green
} catch {
    Write-Host "[-] Could not create scheduled task: $_" -ForegroundColor Yellow
    Write-Host "[*] You can start the agent manually:" -ForegroundColor Gray
    Write-Host "    cd `"$InstallDir`"" -ForegroundColor Gray
    Write-Host "    python service.py" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Agent Details:" -ForegroundColor Cyan
Write-Host "  - Install Directory: $InstallDir" -ForegroundColor Gray
Write-Host "  - Config File: $configPath" -ForegroundColor Gray
Write-Host "  - Manager URL: $ManagerUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "The agent will automatically:" -ForegroundColor Cyan
Write-Host "  1. Register with the manager" -ForegroundColor Gray
Write-Host "  2. Start monitoring file system, clipboard, and USB" -ForegroundColor Gray
Write-Host "  3. Send events to the manager" -ForegroundColor Gray
Write-Host ""
Write-Host "To check agent status:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask -TaskName CyberSentinelAgent" -ForegroundColor Gray
Write-Host ""
Write-Host "To uninstall:" -ForegroundColor Cyan
Write-Host "  iwr -useb https://URL/install.ps1 | iex -Uninstall" -ForegroundColor Gray
Write-Host ""
Write-Host "View logs at: $ConfigDir\agent.log" -ForegroundColor Gray
Write-Host ""
