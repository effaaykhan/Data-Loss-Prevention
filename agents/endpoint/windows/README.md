# CyberSentinel DLP - Windows Agent

Enterprise endpoint DLP agent for Windows operating systems.

## Features

- ✅ **File System Monitoring** - Real-time monitoring of file operations
- ✅ **Clipboard Monitoring** - Detects sensitive data in clipboard
- ✅ **USB Device Detection** - Alerts on USB device connections
- ✅ **Automatic Classification** - Pattern-based sensitive data detection
- ✅ **Real-time Reporting** - Sends events to central server
- ✅ **Configurable Monitoring** - Customize paths and file types

## Requirements

- Windows 10/11 or Windows Server 2016+
- Python 3.8+ (for development)
- Administrator privileges (for installation)

## Quick Start

### Option 1: Run from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Configure agent
# Edit agent_config.json with your server URL

# Run agent
python agent.py
```

### Option 2: Build Executable

```bash
# Build standalone executable
build_agent.bat

# Run executable
dist\CyberSentinelAgent.exe
```

## Configuration

Edit `agent_config.json`:

```json
{
  "server_url": "http://YOUR-SERVER-IP:8000/api/v1",
  "agent_name": "YOUR-AGENT-NAME",
  "monitoring": {
    "file_system": true,
    "clipboard": true,
    "usb_devices": true,
    "monitored_paths": [
      "C:\\Users\\Public\\Documents",
      "C:\\Users\\%USERNAME%\\Desktop"
    ]
  }
}
```

## Installation as Windows Service

### Using NSSM (Recommended)

```powershell
# Download NSSM
# https://nssm.cc/download

# Install service
nssm install CyberSentinelDLP "C:\Path\To\CyberSentinelAgent.exe"

# Start service
nssm start CyberSentinelDLP

# Check status
nssm status CyberSentinelDLP
```

### Using PowerShell

```powershell
# Create service
New-Service -Name "CyberSentinelDLP" `
    -BinaryPathName "C:\Path\To\CyberSentinelAgent.exe" `
    -DisplayName "CyberSentinel DLP Agent" `
    -Description "Data Loss Prevention endpoint agent" `
    -StartupType Automatic

# Start service
Start-Service -Name "CyberSentinelDLP"

# Check status
Get-Service -Name "CyberSentinelDLP"
```

## Monitored Events

| Event Type | Description |
|------------|-------------|
| **File Created** | New file created in monitored directories |
| **File Modified** | File content changed |
| **File Moved** | File moved or renamed |
| **Clipboard Copy** | Sensitive data copied to clipboard |
| **USB Connected** | USB device plugged in |

## Sensitive Data Detection

The agent detects:
- Credit Card Numbers (PAN)
- Social Security Numbers (SSN)
- Email Addresses
- API Keys and Secrets
- Custom patterns (configurable)

## Logs

Agent logs are saved to: `cybersentinel_agent.log`

## Troubleshooting

### Agent won't start
- Check if server URL is correct
- Verify network connectivity: `ping YOUR-SERVER-IP`
- Check logs in `cybersentinel_agent.log`

### No events showing on server
- Verify agent is running: Check Task Manager
- Check firewall rules: Port 8000 should be open
- Verify server API is accessible

### Permission errors
- Run as Administrator
- Check monitored path permissions

## Uninstallation

```powershell
# Stop service
Stop-Service -Name "CyberSentinelDLP"

# Remove service
Remove-Service -Name "CyberSentinelDLP"

# Or using NSSM
nssm stop CyberSentinelDLP
nssm remove CyberSentinelDLP confirm
```

## Support

For issues or questions:
- Check logs: `cybersentinel_agent.log`
- Review server logs
- Contact: support@cybersentinel.local

## Version

**Version**: 1.0.0
**Platform**: Windows 10/11, Windows Server 2016+
**Last Updated**: January 2025
