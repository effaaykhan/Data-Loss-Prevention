@echo off
:: Run as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell.exe -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0agents\windows"
powershell.exe -ExecutionPolicy Bypass -File "install.ps1" -ManagerUrl "http://192.168.60.135:55000"
pause
