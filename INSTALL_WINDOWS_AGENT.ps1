# CyberSentinel DLP Agent - Auto-Elevating Installer
# This script will automatically request Administrator privileges

param(
    [string]$ManagerUrl = "http://192.168.60.135:55000"
)

# Self-elevate if not running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow

    $arguments = "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -ManagerUrl `"$ManagerUrl`""
    Start-Process powershell.exe -ArgumentList $arguments -Verb RunAs -Wait
    exit
}

# Now running as Administrator
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CyberSentinel DLP Agent Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[*] Running with Administrator privileges" -ForegroundColor Green
Write-Host "[*] Manager URL: $ManagerUrl" -ForegroundColor Gray
Write-Host ""

# Change to agents directory
$agentsDir = Join-Path (Split-Path -Parent $PSScriptRoot) "agents\windows"
Set-Location $agentsDir

# Run the actual installer
& ".\install.ps1" -ManagerUrl $ManagerUrl

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
