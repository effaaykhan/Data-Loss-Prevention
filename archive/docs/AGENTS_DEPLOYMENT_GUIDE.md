# CyberSentinel DLP - Agent Deployment Guide

## Summary

The Windows and Linux agents are ready for deployment but require manual installation due to elevated privileges.

---

## ✅ Current Status

### Windows Agent
- **Status:** Ready for installation (requires Admin privileges)
- **Location:** `C:\Users\Red Ghost\Desktop\cybersentinel-dlp\agents\windows\`
- **Installer:** `INSTALL_WINDOWS_AGENT.ps1`

### Linux Agent (WSL Ubuntu)
- **Status:** Dependencies installed, requires service configuration
- **Location:** `/opt/cybersentinel` (in WSL)
- **Config Path:** `/etc/cybersentinel` (in WSL)

---

## 📋 Installation Instructions

### 1. Windows Agent Installation

**Step 1: Open PowerShell as Administrator**
- Right-click **Start Menu**
- Select **"Windows PowerShell (Admin)"** or **"Terminal (Admin)"**

**Step 2: Run the installer**
```powershell
cd "C:\Users\Red Ghost\Desktop\cybersentinel-dlp"
.\INSTALL_WINDOWS_AGENT.ps1
```

**Step 3: Verify installation**
```powershell
# Check if agent is running
Get-ScheduledTask -TaskName "CyberSentinelAgent"

# View agent logs
Get-Content "C:\ProgramData\CyberSentinel\agent.log" -Tail 20
```

---

### 2. Linux Agent Installation (WSL Ubuntu)

**Step 1: Open WSL Ubuntu terminal**

**Step 2: Create configuration file**
```bash
sudo tee /etc/cybersentinel/agent_config.json > /dev/null << 'EOF'
{
  "server_url": "http://192.168.60.135:55000/api/v1",
  "agent_id": "",
  "agent_name": "$(hostname)",
  "heartbeat_interval": 30,
  "monitoring": {
    "file_system": true,
    "monitored_paths": [
      "/home/$(whoami)/Documents",
      "/home/$(whoami)/Desktop",
      "/home/$(whoami)/Downloads"
    ],
    "file_extensions": [
      ".pdf",
      ".docx",
      ".xlsx",
      ".txt",
      ".csv"
    ],
    "exclude_paths": [
      "*/node_modules/*",
      "*/.git/*"
    ]
  },
  "monitoring_options": {
    "clipboard": true,
    "usb_devices": true
  },
  "classification": {
    "enabled": true,
    "max_file_size_mb": 10,
    "patterns": [
      "credit_card",
      "ssn",
      "email"
    ]
  },
  "performance": {
    "max_events_per_minute": 100,
    "max_event_size": 1048576,
    "batch_size": 10,
    "queue_size": 1000
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/cybersentinel_agent.log",
    "max_size": 10485760,
    "max_files": 5
  }
}
EOF
```

**Step 3: Create systemd service**
```bash
sudo tee /etc/systemd/system/cybersentinel-agent.service > /dev/null << 'EOF'
[Unit]
Description=CyberSentinel DLP Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cybersentinel
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 /opt/cybersentinel/agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

**Step 4: Start the agent service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable cybersentinel-agent
sudo systemctl start cybersentinel-agent
```

**Step 5: Verify installation**
```bash
# Check service status
sudo systemctl status cybersentinel-agent

# View agent logs
sudo journalctl -u cybersentinel-agent -f

# Or view log file
sudo tail -f /etc/cybersentinel/logs/agent.log
```

---

## 🔍 Verification

### Check Agents in Dashboard

1. **Open Dashboard:**
   ```
   http://192.168.60.135:3000
   ```

2. **Login:**
   - Username: `admin`
   - Password: `admin`

3. **Navigate to Agents:**
   - Click **"Agents"** in the sidebar
   - You should see both agents listed:
     - Windows agent (hostname: your PC name)
     - Linux agent (hostname: your WSL hostname)

### Check Agent Communication

**Test from Manager:**
```bash
ssh ubuntu@192.168.60.135
docker logs cybersentinel-manager --tail 50 | grep -i agent
```

You should see registration and heartbeat messages from both agents.

---

## 🐛 Troubleshooting

### Windows Agent Issues

**Agent not starting:**
```powershell
# Manual start for testing
cd "C:\Program Files\CyberSentinel"
python service.py
```

**Check Python is in PATH:**
```powershell
python --version
```

**Restart scheduled task:**
```powershell
Stop-ScheduledTask -TaskName "CyberSentinelAgent"
Start-ScheduledTask -TaskName "CyberSentinelAgent"
```

### Linux Agent Issues

**Service won't start:**
```bash
# Check for errors
sudo journalctl -u cybersentinel-agent -n 50

# Test manual run
sudo python3 /opt/cybersentinel/agent.py
```

**Dependencies missing:**
```bash
# Reinstall dependencies
cd /opt/cybersentinel
sudo python3 -m pip install --break-system-packages -r requirements.txt
```

**Config file issues:**
```bash
# Verify config syntax
sudo cat /etc/cybersentinel/agent_config.json
```

### Connection Issues

**Test manager reachability:**

Windows:
```powershell
Invoke-WebRequest -Uri "http://192.168.60.135:55000/health"
```

Linux:
```bash
curl -v http://192.168.60.135:55000/health
```

Expected response: `{"status":"healthy",...}`

**Check firewall:**
- Ensure port 55000 is open on the manager server
- Windows Firewall: Allow Python or the specific port
- Linux: `sudo ufw allow from any to any port 55000`

---

## 📊 What the Agents Monitor

### File System Monitoring
- **Windows:** Desktop, Documents, Downloads folders
- **Linux:** ~/Desktop, ~/Documents, ~/Downloads
- **File types:** .pdf, .docx, .xlsx, .txt, .csv, .pptx
- **Events:** File creation, modification, copying, deletion

### Clipboard Monitoring
- Scans clipboard every 2 seconds
- Detects sensitive patterns:
  - Credit card numbers
  - Social Security Numbers (SSN)
  - Email addresses
- Creates event if sensitive data detected

### USB Monitoring
- Detects USB device connections
- Logs device information:
  - Vendor ID
  - Product ID
  - Device name
  - Mount point (Linux) / Drive letter (Windows)

### Heartbeat
- Sends status update every 60 seconds
- Includes:
  - Agent status
  - System resource usage
  - Last activity timestamp

---

## 🧪 Testing

### Test File Monitoring

**Windows:**
```powershell
# Create test file with fake credit card
"4532-1234-5678-9010" | Out-File "$env:USERPROFILE\Desktop\test-cc.txt"
```

**Linux:**
```bash
# Create test file with fake credit card
echo "4532-1234-5678-9010" > ~/Desktop/test-cc.txt
```

### Test Clipboard Monitoring

1. Copy this fake credit card number: `4532-1234-5678-9010`
2. Wait 2-5 seconds
3. Check dashboard for clipboard event

### Verify in Dashboard

1. Go to: `http://192.168.60.135:3000/events`
2. Filter by:
   - Event Type: `file_created` or `clipboard_copy`
   - Severity: `high` or `critical`
3. You should see the test events

---

## 🔧 Advanced Configuration

### Change Monitored Paths

**Windows:** Edit `C:\ProgramData\CyberSentinel\agent_config.json`
**Linux:** Edit `/etc/cybersentinel/agent_config.json`

```json
{
  "monitoring": {
    "monitored_paths": [
      "C:/Custom/Path",
      "/custom/path"
    ]
  }
}
```

After editing, restart the agent.

### Adjust Sensitivity

```json
{
  "performance": {
    "max_events_per_minute": 200,
    "batch_size": 20
  }
}
```

### Enable Network Monitoring (Advanced)

```json
{
  "monitoring": {
    "network": {
      "enabled": true,
      "interfaces": [
        "eth0",
        "Ethernet"
      ]
    }
  }
}
```

---

## 📦 Uninstallation

### Windows
```powershell
cd "C:\Users\Red Ghost\Desktop\cybersentinel-dlp\agents\windows"
.\install.ps1 -Uninstall
```

### Linux
```bash
sudo systemctl stop cybersentinel-agent
sudo systemctl disable cybersentinel-agent
sudo rm /etc/systemd/system/cybersentinel-agent.service
sudo rm -rf /opt/cybersentinel
sudo rm -rf /etc/cybersentinel  # Removes config and logs
sudo systemctl daemon-reload
```

---

## 📝 Quick Reference

### Manager Info
- **URL:** `http://192.168.60.135:55000`
- **Dashboard:** `http://192.168.60.135:3000`
- **Credentials:** admin / admin

### Agent Locations
- **Windows Install:** `C:\Program Files\CyberSentinel`
- **Windows Config:** `C:\ProgramData\CyberSentinel\agent_config.json`
- **Windows Logs:** `C:\ProgramData\CyberSentinel\agent.log`
- **Linux Install:** `/opt/cybersentinel`
- **Linux Config:** `/etc/cybersentinel/agent_config.json`
- **Linux Logs:** `/var/log/cybersentinel_agent.log`

### Service Management

**Windows:**
```powershell
Get-ScheduledTask -TaskName "CyberSentinelAgent"
Stop-ScheduledTask -TaskName "CyberSentinelAgent"
Start-ScheduledTask -TaskName "CyberSentinelAgent"
```

**Linux:**
```bash
sudo systemctl status cybersentinel-agent
sudo systemctl stop cybersentinel-agent
sudo systemctl start cybersentinel-agent
sudo systemctl restart cybersentinel-agent
```

---

## ✅ Next Steps

1. ✅ **Install Windows Agent** (Follow section 1 above)
2. ✅ **Install Linux Agent** (Follow section 2 above)
3. ✅ **Verify in Dashboard** - Check both agents are showing as "online"
4. ✅ **Test Detection** - Create test files with sensitive data
5. ✅ **Review Events** - Check dashboard for captured events
6. ✅ **Configure Policies** - Set up data loss prevention policies
7. ✅ **Monitor Alerts** - Review and acknowledge alerts

---

## 🎯 Success Criteria

### Windows Agent
- [ ] Scheduled task "CyberSentinelAgent" exists and is running
- [ ] Agent appears in dashboard with status "online"
- [ ] Heartbeat timestamp updates every ~60 seconds
- [ ] Test file creation generates an event

### Linux Agent
- [ ] Systemd service "cybersentinel-agent" is active
- [ ] Agent appears in dashboard with status "online"
- [ ] Heartbeat timestamp updates every ~60 seconds
- [ ] Test file creation generates an event

### System Integration
- [ ] Both agents visible in dashboard
- [ ] Events from both agents appear in event log
- [ ] Clipboard monitoring works on both platforms
- [ ] USB detection works (when USB device connected)

---

**Installation Support:**
- Review agent logs for detailed error messages
- Check manager logs: `docker logs cybersentinel-manager --tail 100`
- Verify network connectivity between agent and manager
- Ensure Python 3.8+ is installed on both Windows and Linux

Good luck with your deployment! 🚀
