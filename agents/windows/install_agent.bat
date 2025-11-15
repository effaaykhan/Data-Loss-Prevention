@echo off
:: CyberSentinel DLP Agent - Windows Installation Wrapper
:: This script runs the PowerShell installer with Administrator privileges

echo ========================================
echo CyberSentinel DLP Agent Installer
echo ========================================
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: Run PowerShell installer
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "install.ps1" -ManagerUrl "http://192.168.60.135:55000"

echo.
echo Installation complete! Press any key to exit...
pause >nul
