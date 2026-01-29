# CyberSentinel DLP Agent - Installation Script
# Requires Administrator privileges

#Requires -RunAsAdministrator

# Configuration
$GITHUB_REPO = "ansh-gadhia/DLP_Agent_VGIPL_CPP"
$INSTALL_DIR = "C:\Program Files\CyberSentinel"
$EXE_NAME = "cybersentinel_agent.exe"
$CONFIG_NAME = "agent_config.json"
$CERT_URL = "https://raw.githubusercontent.com/ansh-gadhia/DLP_Agent_VGIPL_CPP/main/ca.cer"
$CERT_NAME = "ca.cer"

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

function Install-SigningCertificate {
    param(
        [Parameter(Mandatory=$true)]
        [string]$CertUrl,
        [Parameter(Mandatory=$true)]
        [string]$CertName
    )
    
    Write-ColorOutput "Installing code signing certificate..." -Type "Info"
    
    $tempCertPath = Join-Path $env:TEMP $CertName
    $certInstalled = $false
    
    try {
        # Download certificate
        Write-ColorOutput "Downloading certificate from GitHub..." -Type "Info"
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($CertUrl, $tempCertPath)
        Write-ColorOutput "Certificate downloaded successfully" -Type "Success"
        
        # Verify certificate file exists
        if (-not (Test-Path $tempCertPath)) {
            Write-ColorOutput "Certificate file not found after download" -Type "Error"
            return $false
        }
        
        # Import and install certificate
        Write-ColorOutput "Installing certificate to Trusted Root..." -Type "Info"
        
        $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
        $cert.Import($tempCertPath)
        
        Write-ColorOutput "Certificate Details:" -Type "Info"
        Write-Host "  Subject: $($cert.Subject)" -ForegroundColor White
        Write-Host "  Issuer: $($cert.Issuer)" -ForegroundColor White
        Write-Host "  Thumbprint: $($cert.Thumbprint)" -ForegroundColor White
        Write-Host "  Valid From: $($cert.NotBefore)" -ForegroundColor White
        Write-Host "  Valid To: $($cert.NotAfter)" -ForegroundColor White
        Write-Host ""
        
        # Install to Trusted Root Certification Authorities
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "LocalMachine")
        $store.Open("ReadWrite")
        $store.Add($cert)
        $store.Close()
        
        Write-ColorOutput "Certificate installed successfully to Trusted Root Certification Authorities" -Type "Success"
        $certInstalled = $true
        
    } catch {
        Write-ColorOutput "Error installing certificate: $($_.Exception.Message)" -Type "Error"
        Write-ColorOutput "The agent may still work, but executable signature verification may fail" -Type "Warning"
        $certInstalled = $false
    } finally {
        # Always clean up the certificate file
        if (Test-Path $tempCertPath) {
            try {
                Remove-Item -Path $tempCertPath -Force -ErrorAction SilentlyContinue
                Write-ColorOutput "Certificate file cleaned up" -Type "Info"
            } catch {
                Write-ColorOutput "Warning: Could not delete temporary certificate file: $tempCertPath" -Type "Warning"
            }
        }
    }
    
    Write-Host ""
    return $certInstalled
}

function New-AgentId {
    return [guid]::NewGuid().ToString()
}

function Test-IPAddress {
    param([string]$IP)
    
    if ($IP -eq "localhost" -or $IP -eq "") {
        return $true
    }
    
    $isValid = $IP -match '^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return $isValid
}

function Test-PositiveInteger {
    param([string]$Value)
    
    $num = 0
    if ([int]::TryParse($Value, [ref]$num)) {
        return $num -gt 0
    }
    return $false
}

Clear-Host
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   CyberSentinel DLP Agent - Windows Installation Script   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 0: Install Certificate
Write-ColorOutput "Step 0: Installing Code Signing Certificate" -Type "Info"
Write-Host ""
$certInstalled = Install-SigningCertificate -CertUrl $CERT_URL -CertName $CERT_NAME

Write-ColorOutput "Step 1: Configuration Setup" -Type "Info"
Write-Host ""

do {
    $serverIP = Read-Host "Enter server IP address (default: localhost)"
    if ([string]::IsNullOrWhiteSpace($serverIP)) {
        $serverIP = "localhost"
    }
    
    if (-not (Test-IPAddress $serverIP)) {
        Write-ColorOutput "Invalid IP address format. Please try again." -Type "Error"
    }
} while (-not (Test-IPAddress $serverIP))

$serverURL = "http://${serverIP}:55000/api/v1"
Write-ColorOutput "Server URL: $serverURL" -Type "Success"
Write-Host ""

$defaultAgentId = New-AgentId
$agentID = Read-Host "Enter Agent ID (default: auto-generated)"
if ([string]::IsNullOrWhiteSpace($agentID)) {
    $agentID = $defaultAgentId
}
Write-ColorOutput "Agent ID: $agentID" -Type "Success"
Write-Host ""

$defaultAgentName = $env:COMPUTERNAME
$agentName = Read-Host "Enter Agent Name (default: $defaultAgentName)"
if ([string]::IsNullOrWhiteSpace($agentName)) {
    $agentName = $defaultAgentName
}
Write-ColorOutput "Agent Name: $agentName" -Type "Success"
Write-Host ""

do {
    $heartbeatInput = Read-Host "Enter heartbeat interval in seconds (default: 30)"
    if ([string]::IsNullOrWhiteSpace($heartbeatInput)) {
        $heartbeatInterval = 30
        break
    }
    
    if (-not (Test-PositiveInteger $heartbeatInput)) {
        Write-ColorOutput "Please enter a valid positive number." -Type "Error"
    } else {
        $heartbeatInterval = [int]$heartbeatInput
        break
    }
} while ($true)
Write-ColorOutput "Heartbeat Interval: $heartbeatInterval seconds" -Type "Success"
Write-Host ""

do {
    $policySyncInput = Read-Host "Enter policy sync interval in seconds (default: 60)"
    if ([string]::IsNullOrWhiteSpace($policySyncInput)) {
        $policySyncInterval = 60
        break
    }
    
    if (-not (Test-PositiveInteger $policySyncInput)) {
        Write-ColorOutput "Please enter a valid positive number." -Type "Error"
    } else {
        $policySyncInterval = [int]$policySyncInput
        break
    }
} while ($true)
Write-ColorOutput "Policy Sync Interval: $policySyncInterval seconds" -Type "Success"
Write-Host ""

Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "Configuration Summary:" -ForegroundColor Yellow
Write-Host "  Server URL: $serverURL"
Write-Host "  Agent ID: $agentID"
Write-Host "  Agent Name: $agentName"
Write-Host "  Heartbeat Interval: $heartbeatInterval seconds"
Write-Host "  Policy Sync Interval: $policySyncInterval seconds"
Write-Host "  Certificate Installed: $(if ($certInstalled) { 'Yes' } else { 'No (Warning)' })"
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Proceed with installation? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-ColorOutput "Installation cancelled by user." -Type "Warning"
    exit 0
}

Write-Host ""

Write-ColorOutput "Step 2: Downloading agent from GitHub..." -Type "Info"

try {
    $releaseUrl = "https://api.github.com/repos/$GITHUB_REPO/releases/latest"
    Write-ColorOutput "Fetching latest release information..." -Type "Info"
    
    $release = Invoke-RestMethod -Uri $releaseUrl -Headers @{
        "User-Agent" = "CyberSentinel-Installer"
    }
    
    $version = $release.tag_name
    Write-ColorOutput "Latest version: $version" -Type "Success"
    
    $asset = $release.assets | Where-Object { $_.name -eq $EXE_NAME }
    
    if (-not $asset) {
        Write-ColorOutput "Error: Could not find $EXE_NAME in release assets." -Type "Error"
        Write-ColorOutput "Available assets:" -Type "Info"
        $release.assets | ForEach-Object { Write-Host "  - $($_.name)" }
        exit 1
    }
    
    $downloadUrl = $asset.browser_download_url
    $tempFile = Join-Path $env:TEMP $EXE_NAME
    
    Write-ColorOutput "Downloading from: $downloadUrl" -Type "Info"
    
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $tempFile)
    
    Write-ColorOutput "Download completed successfully!" -Type "Success"
    
} catch {
    Write-ColorOutput "Error downloading from GitHub: $($_.Exception.Message)" -Type "Error"
    Write-ColorOutput "Please check:" -Type "Warning"
    Write-Host "  1. GitHub repository name is correct in the script"
    Write-Host "  2. A release exists with the agent executable"
    Write-Host "  3. Internet connection is available"
    exit 1
}

Write-Host ""

Write-ColorOutput "Step 3: Creating installation directory..." -Type "Info"

try {
    if (-not (Test-Path $INSTALL_DIR)) {
        New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
        Write-ColorOutput "Created: $INSTALL_DIR" -Type "Success"
    } else {
        Write-ColorOutput "Directory already exists: $INSTALL_DIR" -Type "Info"
    }
} catch {
    Write-ColorOutput "Error creating installation directory: $($_.Exception.Message)" -Type "Error"
    exit 1
}

Write-Host ""

Write-ColorOutput "Step 4: Installing agent executable..." -Type "Info"

try {
    $exePath = Join-Path $INSTALL_DIR $EXE_NAME
    Copy-Item -Path $tempFile -Destination $exePath -Force
    Write-ColorOutput "Installed: $exePath" -Type "Success"
    
    Remove-Item -Path $tempFile -Force
    
} catch {
    Write-ColorOutput "Error installing executable: $($_.Exception.Message)" -Type "Error"
    exit 1
}

Write-Host ""

Write-ColorOutput "Step 5: Creating configuration file..." -Type "Info"

try {
    $configPath = Join-Path $INSTALL_DIR $CONFIG_NAME
    
    $config = @{
        server_url = $serverURL
        agent_id = $agentID
        agent_name = $agentName
        heartbeat_interval = $heartbeatInterval
        policy_sync_interval = $policySyncInterval
    }
    
    $configJson = $config | ConvertTo-Json -Depth 10
    $configJson | Out-File -FilePath $configPath -Encoding UTF8 -Force
    
    Write-ColorOutput "Created: $configPath" -Type "Success"
    
} catch {
    Write-ColorOutput "Error creating configuration file: $($_.Exception.Message)" -Type "Error"
    exit 1
}

Write-Host ""

Write-ColorOutput "Step 6: Creating VBScript launcher for elevated startup..." -Type "Info"

try {
    # Create VBScript to launch the agent with administrator privileges
    $vbsPath = Join-Path $INSTALL_DIR "launch_agent.vbs"
    $vbsContent = @"
Set objShell = CreateObject("Shell.Application")
objShell.ShellExecute "$exePath", "--background", "$INSTALL_DIR", "runas", 0
"@
    
    $vbsContent | Out-File -FilePath $vbsPath -Encoding ASCII -Force
    Write-ColorOutput "Created launcher script: $vbsPath" -Type "Success"
    
} catch {
    Write-ColorOutput "Error creating VBScript launcher: $($_.Exception.Message)" -Type "Error"
    exit 1
}

Write-Host ""

Write-ColorOutput "Step 7: Configuring auto-start with administrator privileges..." -Type "Info"

try {
    # Create scheduled task to run at logon with highest privileges
    $taskName = "CyberSentinel DLP Agent"
    
    # Remove existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-ColorOutput "Removed existing scheduled task" -Type "Info"
    }
    
    # Create action to run the VBScript launcher
    $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbsPath`"" -WorkingDirectory $INSTALL_DIR
    
    # Create trigger for logon
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    
    # Create principal to run with highest privileges
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -DontStopOnIdleEnd
    
    # Register the task
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "CyberSentinel DLP Agent - Data Loss Prevention monitoring service running with administrator privileges" | Out-Null
    
    Write-ColorOutput "Scheduled task created successfully!" -Type "Success"
    Write-ColorOutput "Task Name: $taskName" -Type "Info"
    Write-ColorOutput "Agent will start automatically at logon with administrator privileges" -Type "Success"
    
} catch {
    Write-ColorOutput "Error creating scheduled task: $($_.Exception.Message)" -Type "Error"
    Write-ColorOutput "Falling back to startup folder method..." -Type "Warning"
    
    # Fallback: Create startup shortcut (won't have admin privileges)
    try {
        $startupFolder = [Environment]::GetFolderPath('Startup')
        $shortcutPath = Join-Path $startupFolder "CyberSentinel DLP Agent.lnk"
        
        if (Test-Path $shortcutPath) {
            Remove-Item -Path $shortcutPath -Force
        }
        
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = "wscript.exe"
        $Shortcut.Arguments = "`"$vbsPath`""
        $Shortcut.WorkingDirectory = $INSTALL_DIR
        $Shortcut.Description = "CyberSentinel DLP Agent - Data Loss Prevention monitoring service"
        $Shortcut.Save()
        
        Write-ColorOutput "Startup shortcut created as fallback" -Type "Success"
    } catch {
        Write-ColorOutput "Error creating startup shortcut: $($_.Exception.Message)" -Type "Error"
    }
}

Write-Host ""

Write-ColorOutput "Step 8: Starting the agent..." -Type "Info"

$startNow = Read-Host "Start the agent now? (Y/N)"
if ($startNow -eq "Y" -or $startNow -eq "y") {
    try {
        # Start the agent with --background flag and administrator privileges
        Start-Process -FilePath $exePath -ArgumentList "--background" -WorkingDirectory $INSTALL_DIR -Verb RunAs
        Start-Sleep -Seconds 3
        
        $process = Get-Process -Name "cybersentinel_agent" -ErrorAction SilentlyContinue
        if ($process) {
            Write-ColorOutput "Agent is running! (PID: $($process.Id))" -Type "Success"
            Write-ColorOutput "Running in background mode with administrator privileges" -Type "Success"
        } else {
            Write-ColorOutput "Agent started, but process not detected yet." -Type "Warning"
            Write-ColorOutput "It may take a few moments to initialize in background mode." -Type "Info"
        }
        
    } catch {
        Write-ColorOutput "Error starting agent: $($_.Exception.Message)" -Type "Error"
        Write-ColorOutput "You can manually start it from: $exePath --background" -Type "Info"
    }
} else {
    Write-ColorOutput "Agent will start automatically at next logon." -Type "Info"
}

Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host "           Installation Completed Successfully!            " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Installation Details:" -ForegroundColor Yellow
Write-Host "  Location: $INSTALL_DIR"
Write-Host "  Executable: $EXE_NAME"
Write-Host "  Configuration: $CONFIG_NAME"
Write-Host "  Launcher Script: launch_agent.vbs"
Write-Host "  Scheduled Task: CyberSentinel DLP Agent (runs at logon with admin privileges)"
Write-Host "  Code Signing Certificate: $(if ($certInstalled) { 'Installed' } else { 'Not Installed (Warning)' })"
Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Yellow
Write-Host "  Start Agent:   Start-Process '$exePath' -ArgumentList '--background' -Verb RunAs"
Write-Host "  Stop Agent:    Stop-Process -Name 'cybersentinel_agent' -Force"
Write-Host "  Check Status:  Get-Process -Name 'cybersentinel_agent'"
Write-Host "  View Logs:     Check $INSTALL_DIR\cybersentinel_agent.log"
Write-Host "  Disable Auto-start: Disable-ScheduledTask -TaskName 'CyberSentinel DLP Agent'"
Write-Host "  Enable Auto-start:  Enable-ScheduledTask -TaskName 'CyberSentinel DLP Agent'"
Write-Host ""
Write-Host "Note: The agent runs in background mode and requires administrator privileges" -ForegroundColor Cyan
Write-Host ""
Write-Host "To uninstall, run: Uninstall-CyberSentinelAgent.ps1" -ForegroundColor Yellow
Write-Host "To upgrade, run: Upgrade-CyberSentinelAgent.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green

Write-Host ""
Read-Host "Press Enter to exit"
