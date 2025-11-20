# CyberSentinel DLP Agent Installation Guide

## Quick Installation

### Windows Agent (This PC)

**Option 1: Auto-Elevating Script (Recommended)**
1. Right-click on `INSTALL_WINDOWS_AGENT.ps1`
2. Select **"Run with PowerShell"**
3. Click **"Yes"** when prompted for Administrator privileges
4. Wait for installation to complete

**Option 2: Manual Administrator PowerShell**
1. Right-click **Start Menu** → Select **"Windows PowerShell (Admin)"**
2. Run these commands:
```powershell
cd "C:\Users\Red Ghost\Desktop\cybersentinel-dlp\agents\windows"
.\install.ps1 -ManagerUrl "http://192.168.60.135:55000"
```

### Linux Agent (WSL Ubuntu)

**Run in WSL Ubuntu terminal:**
```bash
cd "/mnt/c/Users/Red Ghost/Desktop/cybersentinel-dlp/agents/linux"
sudo bash install.sh --manager-url "http://192.168.60.135:55000"
```

---

## Verification

After installation, verify agents are running:

### Windows
```powershell
Get-ScheduledTask -TaskName "CyberSentinelAgent"
```

### Linux (WSL)
```bash
sudo systemctl status cybersentinel-agent
```

### Dashboard
Open browser: `http://192.168.60.135:3000/agents`
- Login: admin / admin
- You should see both agents listed

---

## Troubleshooting

### Windows Agent Issues

**Check if agent is running:**
```powershell
Get-ScheduledTask -TaskName "CyberSentinelAgent" | Select-Object State, LastRunTime, LastTaskResult
```

**View agent logs:**
```powershell
Get-Content "C:\ProgramData\CyberSentinel\agent.log" -Tail 50
```

**Restart agent:**
```powershell
Stop-ScheduledTask -TaskName "CyberSentinelAgent"
Start-ScheduledTask -TaskName "CyberSentinelAgent"
```

**Manual test run:**
```powershell
cd "C:\Program Files\CyberSentinel"
python service.py
```

### Linux Agent Issues

**Check status:**
```bash
sudo systemctl status cybersentinel-agent
```

**View logs:**
```bash
sudo journalctl -u cybersentinel-agent -f
```

**Restart agent:**
```bash
sudo systemctl restart cybersentinel-agent
```

**Manual test run:**
```bash
sudo python3 /opt/cybersentinel/linux/agent.py
```

### Connection Issues

**Test manager connectivity:**

Windows:
```powershell
Invoke-WebRequest -Uri "http://192.168.60.135:55000/health" -UseBasicParsing
```

Linux:
```bash
curl -v http://192.168.60.135:55000/health
```

Expected response: `{"status":"healthy",...}`

---

## What the Agent Does

The CyberSentinel DLP Agent monitors:

1. **File System** - Tracks file operations in monitored directories
   - Windows: Desktop, Documents, Downloads
   - Linux: ~/Desktop, ~/Documents, ~/Downloads

2. **Clipboard** - Monitors clipboard for sensitive data
   - Credit card numbers
   - Social security numbers
   - Email addresses

3. **USB Devices** - Detects when USB devices are connected
   - Logs device information
   - Monitors file transfers

4. **Heartbeat** - Sends status updates every 60 seconds

All events are sent to the manager at `http://192.168.60.135:55000`

---

## Uninstallation

### Windows
```powershell
Stop-Process -Name CyberSentinelAgent -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Program Files\CyberSentinel" -Recurse -Force
Remove-Item "C:\ProgramData\CyberSentinel\agent_config.json" -Force -ErrorAction SilentlyContinue
```

### Linux
```bash
sudo systemctl stop cybersentinel-agent
sudo systemctl disable cybersentinel-agent
sudo rm /etc/systemd/system/cybersentinel-agent.service
sudo rm -rf /opt/cybersentinel
sudo rm -f /etc/cybersentinel/agent_config.json
sudo systemctl daemon-reload
```

---

## Configuration

### Windows
Edit: `C:\ProgramData\CyberSentinel\agent_config.json`

### Linux
Edit: `/etc/cybersentinel/agent_config.json`

After editing, restart the agent.

---

## Next Steps

1. **Install agents** using commands above
2. **Verify** agents appear in dashboard
3. **Test** by creating a file with test data (e.g., fake credit card number)
4. **View events** in dashboard: `http://192.168.60.135:3000/events`

---

## Support

- View agent logs for detailed debugging
- Check dashboard for agent status
- Ensure manager is running: `docker-compose ps`
- Firewall: Allow port 55000 for agent communication
