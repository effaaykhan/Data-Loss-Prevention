# CyberSentinel Windows Agent - Quick Deploy
# Runs in user space (no admin required)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CyberSentinel Windows Agent Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Install to user's local appdata
$installDir = "$env:LOCALAPPDATA\CyberSentinel"
$configDir = "$env:LOCALAPPDATA\CyberSentinel\config"
$managerUrl = "http://192.168.60.135:55000"

Write-Host "[1/6] Creating directories..." -ForegroundColor Cyan
New-Item -Path "$installDir\common\monitors" -ItemType Directory -Force | Out-Null
New-Item -Path "$installDir\windows" -ItemType Directory -Force | Out-Null
New-Item -Path "$configDir\logs" -ItemType Directory -Force | Out-Null
Write-Host "[+] Directories created" -ForegroundColor Green

Write-Host "[2/6] Copying agent files..." -ForegroundColor Cyan
$sourceDir = "C:\Users\Red Ghost\Desktop\cybersentinel-dlp\agents"
Copy-Item -Path "$sourceDir\common\*" -Destination "$installDir\common\" -Recurse -Force
Copy-Item -Path "$sourceDir\windows\*" -Destination "$installDir\windows\" -Recurse -Force
Copy-Item -Path "$sourceDir\requirements.txt" -Destination "$installDir\" -Force
Write-Host "[+] Agent files copied" -ForegroundColor Green

Write-Host "[3/6] Installing Python dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet
python -m pip install -r "$installDir\requirements.txt" --quiet
Write-Host "[+] Dependencies installed" -ForegroundColor Green

Write-Host "[4/6] Creating configuration..." -ForegroundColor Cyan
$configContent = @"
agent:
  id: ""
  name: "$env:COMPUTERNAME"
  manager_url: "$managerUrl"
  registration_key: ""
  heartbeat_interval: 60

monitoring:
  file_system:
    enabled: true
    paths:
      - "C:/Users/$env:USERNAME/Desktop"
      - "C:/Users/$env:USERNAME/Documents"
      - "C:/Users/$env:USERNAME/Downloads"
    extensions:
      - .pdf
      - .docx
      - .xlsx
      - .txt
      - .csv
    exclude_patterns:
      - "*/node_modules/*"
      - "*/.git/*"

  clipboard:
    enabled: true
    poll_interval: 2

  usb:
    enabled: true
    poll_interval: 5

classification:
  local:
    enabled: true
    patterns:
      - credit_card
      - ssn
      - email

performance:
  max_events_per_minute: 100
  max_event_size: 1048576
  batch_size: 10
  queue_size: 1000

logging:
  level: INFO
  file: "$configDir/logs/agent.log"
  max_size: 10485760
  max_files: 5
"@

Set-Content -Path "$configDir\agent.yml" -Value $configContent
Write-Host "[+] Configuration created" -ForegroundColor Green

Write-Host "[5/6] Creating service script..." -ForegroundColor Cyan
$serviceScript = @"
import sys
import os

# Add agent directory to path
sys.path.insert(0, r'$installDir')

# Set config path
os.environ['CYBERSENTINEL_CONFIG'] = r'$configDir\agent.yml'

# Import and run agent
from windows.agent import main
import asyncio

if __name__ == '__main__':
    asyncio.run(main())
"@

Set-Content -Path "$installDir\run_agent.py" -Value $serviceScript
Write-Host "[+] Service script created" -ForegroundColor Green

Write-Host "[6/6] Testing agent startup..." -ForegroundColor Cyan
Write-Host "[*] Agent installed to: $installDir" -ForegroundColor Gray
Write-Host "[*] Config file: $configDir\agent.yml" -ForegroundColor Gray
Write-Host "[*] Manager URL: $managerUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "[+] Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the agent manually:" -ForegroundColor Cyan
Write-Host "  cd `"$installDir`"" -ForegroundColor Gray
Write-Host "  python run_agent.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Starting agent now..." -ForegroundColor Yellow

# Start agent in background
Start-Process python -ArgumentList "$installDir\run_agent.py" -WorkingDirectory $installDir -WindowStyle Hidden

Write-Host "[+] Agent started in background!" -ForegroundColor Green
Write-Host ""
Write-Host "Check logs at: $configDir\logs\agent.log" -ForegroundColor Gray
Write-Host ""
