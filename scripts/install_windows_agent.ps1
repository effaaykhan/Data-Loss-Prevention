<#
.SYNOPSIS
  CyberSentinel DLP Windows agent installer (clone -> venv -> deps -> config -> scheduled task).

.DESCRIPTION
  Downloads the Windows agent from git, creates a Python virtual environment, installs dependencies,
  templates agent_config.json, and registers a SYSTEM/AtStartup Scheduled Task with restart-on-failure.

.PARAMETER ManagerUrl
  Manager API base URL (default: http://localhost:55000/api/v1).

.PARAMETER InstallDir
  Path to install the agent code (default: %ProgramFiles%\CyberSentinel\agent).

.PARAMETER ConfigDir
  Path to store agent_config.json and logs (default: %ProgramData%\CyberSentinel).

.PARAMETER VenvDir
  Path for the virtual environment (default: <InstallDir>\venv).

.PARAMETER RepoUrl
  Git repository URL for the project (default: https://github.com/YOUR_ORG/Data-Loss-Prevention.git).

.PARAMETER Branch
  Git branch to checkout (default: main).

.PARAMETER Ref
  Optional commit/tag to checkout after branch.

.PARAMETER ServiceName
  Scheduled Task name (default: CyberSentinelAgent).

.PARAMETER LogPath
  Optional explicit log path (default: <ConfigDir>\cybersentinel_agent.log).

.PARAMETER NoStart
  Do not start the Scheduled Task after registration.

.PARAMETER Force
  Re-clone and overwrite existing config.
#>

[CmdletBinding()]
param(
    [string]$ManagerUrl = "http://localhost:55000/api/v1",
    [string]$InstallDir = "$env:ProgramFiles\CyberSentinel\agent",
    [string]$ConfigDir = "$env:ProgramData\CyberSentinel",
    [string]$VenvDir = "",
    [string]$RepoUrl = "https://github.com/YOUR_ORG/Data-Loss-Prevention.git",
    [string]$Branch = "main",
    [string]$Ref = "",
    [string]$ServiceName = "CyberSentinelAgent",
    [string]$LogPath = "",
    [switch]$NoStart,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Require-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    if (-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Err "Run PowerShell as Administrator."
        exit 1
    }
}

function Require-Command($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Err "Missing required command: $name"
        exit 1
    }
}

function Ensure-Dir($path) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}

try {
    Require-Admin
    Require-Command git
    Require-Command python

    if (-not $VenvDir) { $VenvDir = Join-Path $InstallDir "venv" }
    if (-not $LogPath) { $LogPath = Join-Path $ConfigDir "cybersentinel_agent.log" }

    Write-Info "ManagerUrl:   $ManagerUrl"
    Write-Info "InstallDir:   $InstallDir"
    Write-Info "ConfigDir:    $ConfigDir"
    Write-Info "VenvDir:      $VenvDir"
    Write-Info "RepoUrl:      $RepoUrl"
    Write-Info "Branch/Ref:   $Branch $Ref"
    Write-Info "ServiceName:  $ServiceName"
    Write-Host ""

    # TLS
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    # Prep paths
    Ensure-Dir $InstallDir
    Ensure-Dir $ConfigDir

    # Clone with sparse checkout
    $temp = Join-Path $env:TEMP ("cs-agent-" + [guid]::NewGuid().ToString("N"))
    try {
        Write-Info "Cloning repository..."
        git clone --depth 1 --branch $Branch $RepoUrl $temp | Out-Null
        if ($Ref) {
            Push-Location $temp
            git checkout $Ref | Out-Null
            Pop-Location
        }

        $agentSrc = Join-Path $temp "agents/endpoint/windows"
        if (-not (Test-Path $agentSrc)) {
            throw "Agent source not found at $agentSrc"
        }

        if ($Force -and (Test-Path $InstallDir)) {
            Write-Warn "Force requested: clearing install dir $InstallDir"
            Remove-Item -Recurse -Force -Path $InstallDir
            Ensure-Dir $InstallDir
        }

        Write-Info "Copying agent files..."
        robocopy $agentSrc $InstallDir /E /NFL /NDL /NJH /NJS /NC /NS | Out-Null
        Write-Ok "Agent files copied to $InstallDir"
    }
    finally {
        if (Test-Path $temp) { Remove-Item -Recurse -Force $temp }
    }

    # Python version check
    $pyCmd = "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    $pyVersion = & python -c $pyCmd
    if ($LASTEXITCODE -ne 0) { throw "Python check failed" }
    $parts = $pyVersion.Trim().Split(".")
    if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 10)) {
        throw "Python 3.10+ required (found $pyVersion)"
    }
    Write-Ok "Python $pyVersion detected"

    # Virtualenv
    if ($Force -and (Test-Path $VenvDir)) {
        Write-Warn "Force requested: removing venv $VenvDir"
        Remove-Item -Recurse -Force $VenvDir
    }
    if (-not (Test-Path $VenvDir)) {
        Write-Info "Creating virtual environment..."
        python -m venv "$VenvDir"
    }
    $venvPy = Join-Path $VenvDir "Scripts/python.exe"
    & $venvPy -m pip install --upgrade pip | Out-Null
    & $venvPy -m pip install -r (Join-Path $InstallDir "requirements.txt")
    Write-Ok "Dependencies installed"

    # Config
    $configPath = Join-Path $ConfigDir "agent_config.json"
    $defaultConfigPath = Join-Path $InstallDir "agent_config.json"
    $configObj = @{}
if ((Test-Path $configPath) -and (-not $Force)) {
        $configObj = Get-Content $configPath -Raw | ConvertFrom-Json
        Write-Info "Using existing config at $configPath"
    } elseif (Test-Path $defaultConfigPath) {
        $configObj = Get-Content $defaultConfigPath -Raw | ConvertFrom-Json
        Write-Info "Loaded template config from $defaultConfigPath"
    } else {
        $configObj = @{
            server_url = $ManagerUrl
            agent_name = $env:COMPUTERNAME
            monitoring = @{
                file_system = $true
                clipboard = $true
                usb_devices = $true
                monitored_paths = @(
                    "$env:USERPROFILE\Documents",
                    "$env:USERPROFILE\Desktop",
                    "$env:USERPROFILE\Downloads"
                )
                file_extensions = @(".pdf",".docx",".xlsx",".txt",".csv",".json",".xml")
                transfer_blocking = @{
                    enabled = $false
                    block_removable_drives = $true
                    poll_interval_seconds = 5
                }
            }
            quarantine = @{
                enabled = $true
                folder = "C:\Quarantine"
            }
            heartbeat_interval = 30
            policy_sync_interval = 60
        }
        Write-Warn "Template config not found; using defaults."
    }
    $configObj.server_url = $ManagerUrl
    if (-not $configObj.agent_name) { $configObj.agent_name = $env:COMPUTERNAME }
    if (-not $configObj.quarantine) { $configObj.quarantine = @{ enabled = $true; folder = "C:\Quarantine" } }
    if (-not $configObj.monitoring) { $configObj.monitoring = @{} }
    if (-not $configObj.monitoring.monitored_paths) {
        $configObj.monitoring.monitored_paths = @(
            "$env:USERPROFILE\Documents",
            "$env:USERPROFILE\Desktop",
            "$env:USERPROFILE\Downloads"
        )
    }
    $json = $configObj | ConvertTo-Json -Depth 8
    $json | Out-File -FilePath $configPath -Encoding UTF8
    Write-Ok "Config written to $configPath"

    # Scheduled Task
    $action = New-ScheduledTaskAction -Execute $venvPy -Argument "`"$InstallDir\agent.py`"" -WorkingDirectory $InstallDir
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    Register-ScheduledTask -TaskName $ServiceName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Write-Ok "Scheduled Task '$ServiceName' registered (AtStartup, SYSTEM)"

    if (-not $NoStart) {
        Write-Info "Starting Scheduled Task..."
        Start-ScheduledTask -TaskName $ServiceName
        Start-Sleep -Seconds 2
    }

    $task = Get-ScheduledTask -TaskName $ServiceName
    $last = Get-ScheduledTaskInfo -TaskName $ServiceName
    Write-Host ""
    Write-Ok "Task State: $($task.State); LastResult: $($last.LastTaskResult)"
    Write-Info "Logs (if configured) at: $LogPath"
    Write-Info "Config: $configPath"
    Write-Info "To check status: Get-ScheduledTask -TaskName $ServiceName"
    Write-Info "To view task history: Get-ScheduledTaskInfo -TaskName $ServiceName"
}
catch {
    Write-Err "Installer failed: $($_.Exception.Message)"
    if ($_.InvocationInfo) {
        Write-Host $_.InvocationInfo.PositionMessage
    }
    if ($_.ScriptStackTrace) {
        Write-Host $_.ScriptStackTrace
    }
    exit 1
}

