# CyberSentinel DLP - Quick Installation

## One-Line Agent Installation

### Windows Agent

**Open PowerShell as Administrator** and run:

```powershell
cd "C:\Path\To\cybersentinel-dlp\agents\windows"; .\install.ps1 -ManagerUrl "http://YOUR_SERVER_IP:55000"
```

**Example:**
```powershell
cd "C:\Users\YourName\Desktop\cybersentinel-dlp\agents\windows"; .\install.ps1 -ManagerUrl "http://192.168.60.135:55000"
```

---

### Linux Agent

**On your Linux/Ubuntu machine**, run:

```bash
cd /path/to/cybersentinel-dlp/agents/linux && sudo bash install.sh --manager-url "http://YOUR_SERVER_IP:55000"
```

**Example:**
```bash
cd ~/cybersentinel-dlp/agents/linux && sudo bash install.sh --manager-url "http://192.168.60.135:55000"
```

---

## Verification

After installation, verify agents are running:

**Windows:**
```powershell
Get-ScheduledTask -TaskName "CyberSentinelAgent"
```

**Linux:**
```bash
sudo systemctl status cybersentinel-agent
```

**Dashboard:**
Open http://YOUR_SERVER_IP:3000 and check Agents page.

---

## Prerequisites

- **Python 3.8+** installed
- **Administrator/sudo access**
- **Network access** to manager server
- **Server running** at specified IP

---

## Troubleshooting

**Windows - "Cannot bind argument to parameter 'Path'":**
- Make sure you're in the `agents/windows` directory before running
- Use full path: `cd "C:\Full\Path\To\agents\windows"`

**Linux - "ModuleNotFoundError: No module named 'structlog'":**
```bash
sudo apt-get install python3-pip
sudo pip3 install -r requirements.txt
```

**Agent not appearing in dashboard:**
- Test connectivity: `curl http://YOUR_SERVER_IP:55000/health`
- Check logs:
  - Windows: `Get-Content "C:\ProgramData\CyberSentinel\agent.log" -Tail 50`
  - Linux: `sudo journalctl -u cybersentinel-agent -n 50`

---

## Default Locations

**Windows:**
- Install: `C:\Program Files\CyberSentinel`
- Config: `C:\ProgramData\CyberSentinel\agent.yml`
- Logs: `C:\ProgramData\CyberSentinel\agent.log`

**Linux:**
- Install: `/opt/cybersentinel`
- Config: `/etc/cybersentinel/agent.yml`
- Logs: `/etc/cybersentinel/logs/agent.log`

---

## Quick Links

- **Dashboard:** http://YOUR_SERVER_IP:3000
- **API:** http://YOUR_SERVER_IP:55000/api/v1
- **Default Login:** admin / admin

**⚠️ Change default password after first login!**
