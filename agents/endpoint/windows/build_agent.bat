@echo off
REM CyberSentinel DLP - Windows Agent Build Script

echo ============================================
echo Building CyberSentinel DLP Windows Agent
echo ============================================
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Build executable with PyInstaller
echo Building executable...
pyinstaller --onefile ^
    --name "CyberSentinelAgent" ^
    --icon=icon.ico ^
    --add-data "agent_config.json;." ^
    --hidden-import=win32timezone ^
    --hidden-import=wmi ^
    agent.py

echo.
echo ============================================
echo Build complete!
echo Executable location: dist\CyberSentinelAgent.exe
echo ============================================
echo.
pause
