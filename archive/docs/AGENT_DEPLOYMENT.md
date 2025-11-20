# Agent Deployment Guide - Windows & Linux

This guide provides step-by-step instructions for deploying CyberSentinel DLP agents on Windows and Linux endpoints and connecting them to your server.

## Prerequisites

Before deploying agents, ensure:

1. ✅ **Server is running** - Backend API accessible at `http://YOUR-SERVER-IP:8000`
2. ✅ **Network connectivity** - Agents can reach server on port 8000
3. ✅ **Firewall configured** - Port 8000 open on server
4. ✅ **Admin access** - Administrator/root privileges on endpoints

---

## Quick Reference

### Find Your Server IP

**On Linux Server:**
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
# Or
hostname -I
```

**On Windows Server:**
```powershell
ipconfig | findstr IPv4
```

### Test Server Connectivity

```bash
# From any endpoint, test if server is reachable
curl http://YOUR-SERVER-IP:8000/health

# Expected response:
# {"status":"healthy","service":"CyberSentinel DLP","version":"1.0.0"}
```

---

## Windows Agent Deployment

### 🚀 One-Click Installation (Recommended)

**The fastest way to install - just one command!**

1. **Right-click PowerShell** → **Run as Administrator**
2. **Copy and paste this single line:**

```powershell
iwr -useb https://raw.githubusercontent.com/effaaykhan/cybersentinel-windows-agent/main/install.ps1 | iex
```

3. **Follow the prompts** (enter server IP, agent name)
4. **Done!** Agent is installed and running

**What it does automatically:**
- ✅ Checks for Python (installs if missing)
- ✅ Downloads latest agent files from GitHub
- ✅ Installs all Python dependencies
- ✅ Prompts for server IP and agent details
- ✅ Creates configuration file
- ✅ Tests server connectivity
- ✅ Optionally installs as Windows Service
- ✅ Starts the agent

**Silent Installation (for automation):**
```powershell
iwr -useb https://raw.githubusercontent.com/effaaykhan/cybersentinel-windows-agent/main/install.ps1 | iex -ServerURL "http://192.168.1.100:8000/api/v1" -AgentID "WIN-SALES-01" -AgentName "Sales-Laptop" -AsService -Silent
```

---

### Method 1: Manual Installation (Development/Testing)

Perfect for testing or when you need more control.

#### Step 1: Clone Repository

```powershell
# Clone from GitHub
git clone https://github.com/effaaykhan/cybersentinel-windows-agent.git
cd cybersentinel-windows-agent

# Or download ZIP and extract
```

#### Step 2: Install Python Dependencies

```powershell
# Install requirements
pip install -r requirements.txt
```

#### Step 3: Configure Agent

Edit `agent_config.json` with your settings:

```json
{
  "server_url": "http://192.168.1.100:8000/api/v1",
  "agent_id": "WIN-DESKTOP-001",
  "agent_name": "JohnDoe-Laptop",
  "heartbeat_interval": 60,
  "monitoring": {
    "file_system": true,
    "clipboard": true,
    "usb_devices": true,
    "monitored_paths": [
      "C:\\Users\\Public\\Documents",
      "C:\\Users\\%USERNAME%\\Documents",
      "C:\\Users\\%USERNAME%\\Desktop",
      "C:\\Users\\%USERNAME%\\Downloads"
    ],
    "file_extensions": [
      ".pdf", ".docx", ".doc", ".xlsx", ".xls",
      ".csv", ".txt", ".json", ".xml", ".sql"
    ]
  },
  "classification": {
    "enabled": true,
    "max_file_size_mb": 10
  }
}
```

**Configuration Tips:**
- Replace `192.168.1.100` with your actual server IP
- Set unique `agent_id` for each machine (e.g., `WIN-SALES-DESK-01`)
- Set descriptive `agent_name` (e.g., username or hostname)
- `%USERNAME%` automatically expands to current user

#### Step 4: Run Agent

```powershell
# Run as Administrator (Right-click PowerShell -> Run as Administrator)
python agent.py
```

**Expected Output:**
```
2025-01-06 10:30:45 - INFO - Starting CyberSentinel DLP Agent
2025-01-06 10:30:45 - INFO - Connecting to server: http://192.168.1.100:8000/api/v1
2025-01-06 10:30:45 - INFO - Agent registered: WIN-DESKTOP-001
2025-01-06 10:30:45 - INFO - Starting file system monitoring...
2025-01-06 10:30:45 - INFO - Starting clipboard monitoring...
2025-01-06 10:30:45 - INFO - Starting USB monitoring...
2025-01-06 10:30:45 - INFO - Agent is running. Press Ctrl+C to stop.
```

---

### Method 2: Production Deployment (Windows Service)

Best for permanent installations across your organization.

#### Step 1: Build Standalone Executable

```powershell
# Install PyInstaller
pip install pyinstaller

# Build executable
build_agent.bat

# Or manually:
pyinstaller --onefile --noconsole --name CyberSentinelAgent agent.py
```

Output: `dist\CyberSentinelAgent.exe`

#### Step 2: Prepare for Deployment

```powershell
# Create deployment directory
New-Item -Path "C:\Program Files\CyberSentinel" -ItemType Directory -Force

# Copy executable
Copy-Item "dist\CyberSentinelAgent.exe" -Destination "C:\Program Files\CyberSentinel\"

# Copy configuration
Copy-Item "agent_config.json" -Destination "C:\Program Files\CyberSentinel\"

# Edit configuration for this machine
notepad "C:\Program Files\CyberSentinel\agent_config.json"
```

#### Step 3: Install as Windows Service

**Option A: Using NSSM (Recommended)**

```powershell
# Download NSSM from https://nssm.cc/download
# Extract to C:\nssm

# Install service
C:\nssm\nssm.exe install CyberSentinelDLP "C:\Program Files\CyberSentinel\CyberSentinelAgent.exe"

# Set working directory
C:\nssm\nssm.exe set CyberSentinelDLP AppDirectory "C:\Program Files\CyberSentinel"

# Set display name
C:\nssm\nssm.exe set CyberSentinelDLP DisplayName "CyberSentinel DLP Agent"

# Set description
C:\nssm\nssm.exe set CyberSentinelDLP Description "Data Loss Prevention endpoint protection agent"

# Set to start automatically
C:\nssm\nssm.exe set CyberSentinelDLP Start SERVICE_AUTO_START

# Set recovery options (restart on failure)
C:\nssm\nssm.exe set CyberSentinelDLP AppRestartDelay 30000

# Start service
C:\nssm\nssm.exe start CyberSentinelDLP

# Check status
C:\nssm\nssm.exe status CyberSentinelDLP
```

**Option B: Using PowerShell**

```powershell
# Create service
New-Service -Name "CyberSentinelDLP" `
    -BinaryPathName "C:\Program Files\CyberSentinel\CyberSentinelAgent.exe" `
    -DisplayName "CyberSentinel DLP Agent" `
    -Description "Data Loss Prevention endpoint protection agent" `
    -StartupType Automatic

# Start service
Start-Service -Name "CyberSentinelDLP"

# Verify service status
Get-Service -Name "CyberSentinelDLP" | Format-List
```

#### Step 4: Manage Windows Service

```powershell
# Check status
Get-Service -Name "CyberSentinelDLP"

# Start service
Start-Service -Name "CyberSentinelDLP"

# Stop service
Stop-Service -Name "CyberSentinelDLP"

# Restart service
Restart-Service -Name "CyberSentinelDLP"

# View service details
Get-Service -Name "CyberSentinelDLP" | Select-Object *
```

#### Step 5: View Logs

```powershell
# Logs are in the installation directory
Get-Content "C:\Program Files\CyberSentinel\cybersentinel_agent.log" -Tail 50

# Watch logs in real-time
Get-Content "C:\Program Files\CyberSentinel\cybersentinel_agent.log" -Wait -Tail 20
```

---

### Mass Deployment (Windows)

For deploying to multiple Windows machines:

#### Option 1: Group Policy (Active Directory)

1. Create deployment package:
```powershell
# Create deployment folder
mkdir \\server\share\CyberSentinel-Deploy
copy dist\CyberSentinelAgent.exe \\server\share\CyberSentinel-Deploy\
copy agent_config.json \\server\share\CyberSentinel-Deploy\
copy install.ps1 \\server\share\CyberSentinel-Deploy\
```

2. Create `install.ps1`:
```powershell
# install.ps1
$installPath = "C:\Program Files\CyberSentinel"
New-Item -Path $installPath -ItemType Directory -Force
Copy-Item "\\server\share\CyberSentinel-Deploy\*" -Destination $installPath -Force

# Install service with NSSM
& "C:\nssm\nssm.exe" install CyberSentinelDLP "$installPath\CyberSentinelAgent.exe"
& "C:\nssm\nssm.exe" start CyberSentinelDLP
```

3. Deploy via GPO startup script

#### Option 2: PowerShell Remoting

```powershell
# Deploy to multiple machines
$computers = @("PC001", "PC002", "PC003")

foreach ($computer in $computers) {
    Invoke-Command -ComputerName $computer -ScriptBlock {
        # Installation commands here
    }
}
```

---

## Linux Agent Deployment

### Quick Installation (Recommended)

Perfect for most Linux deployments.

#### Step 1: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/effaaykhan/cybersentinel-linux-agent.git
cd cybersentinel-linux-agent

# Or download tarball
wget https://github.com/effaaykhan/cybersentinel-linux-agent/archive/main.tar.gz
tar -xzf main.tar.gz
cd cybersentinel-linux-agent-main
```

#### Step 2: Configure Agent

Edit `agent_config.json`:

```bash
nano agent_config.json
```

```json
{
  "server_url": "http://192.168.1.100:8000/api/v1",
  "agent_id": "LINUX-WEB-01",
  "agent_name": "Production-WebServer-01",
  "heartbeat_interval": 60,
  "monitoring": {
    "file_system": true,
    "monitored_paths": [
      "/home",
      "/var/www",
      "/opt/data",
      "/etc"
    ],
    "exclude_paths": [
      "/home/*/.cache",
      "/home/*/.local/share",
      "/home/*/snap",
      "/home/*/.npm"
    ],
    "file_extensions": [
      ".pdf", ".docx", ".xlsx", ".txt", ".csv",
      ".json", ".xml", ".sql", ".conf", ".key",
      ".pem", ".crt", ".env", ".yaml", ".yml"
    ]
  },
  "classification": {
    "enabled": true,
    "max_file_size_mb": 10
  }
}
```

**Configuration Tips:**
- Replace `192.168.1.100` with your actual server IP
- Set unique `agent_id` for each Linux machine
- Add critical directories to `monitored_paths`
- Exclude cache/temp directories in `exclude_paths`
- Monitor config files (`.conf`, `.env`) for secrets

#### Step 3: Run Automated Installer

```bash
# Make installer executable
chmod +x install.sh

# Run as root
sudo ./install.sh
```

**Installation Process:**
```
=== CyberSentinel DLP Agent Installer ===
Installing Python dependencies...
Creating directories...
Copying agent files...
Installing systemd service...
Starting agent...
=== Installation Complete! ===

Agent Status:
● cybersentinel-agent.service - CyberSentinel DLP Agent
   Loaded: loaded (/etc/systemd/system/cybersentinel-agent.service)
   Active: active (running)
```

#### Step 4: Verify Installation

```bash
# Check service status
sudo systemctl status cybersentinel-agent

# View logs
sudo journalctl -u cybersentinel-agent -f

# Check log file
sudo tail -f /var/log/cybersentinel_agent.log
```

**Expected Log Output:**
```
2025-01-06 10:30:45 - INFO - Starting CyberSentinel DLP Agent
2025-01-06 10:30:45 - INFO - Loaded configuration from /etc/cybersentinel/agent_config.json
2025-01-06 10:30:45 - INFO - Connecting to: http://192.168.1.100:8000/api/v1
2025-01-06 10:30:45 - INFO - Agent registered successfully: LINUX-WEB-01
2025-01-06 10:30:45 - INFO - Monitoring paths: ['/home', '/var/www']
2025-01-06 10:30:45 - INFO - Agent running...
```

---

### Manual Installation (Linux)

If you need more control over the installation:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv -y

# Install Python packages
pip3 install -r requirements.txt

# Create directories
sudo mkdir -p /opt/cybersentinel
sudo mkdir -p /etc/cybersentinel
sudo mkdir -p /var/log

# Copy files
sudo cp agent.py /opt/cybersentinel/
sudo cp agent_config.json /etc/cybersentinel/
sudo cp cybersentinel-agent.service /etc/systemd/system/

# Set permissions
sudo chmod +x /opt/cybersentinel/agent.py
sudo chown -R root:root /opt/cybersentinel
sudo chmod 600 /etc/cybersentinel/agent_config.json

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable cybersentinel-agent
sudo systemctl start cybersentinel-agent

# Check status
sudo systemctl status cybersentinel-agent
```

---

### Manage Linux Agent

```bash
# Start agent
sudo systemctl start cybersentinel-agent

# Stop agent
sudo systemctl stop cybersentinel-agent

# Restart agent
sudo systemctl restart cybersentinel-agent

# Check status
sudo systemctl status cybersentinel-agent

# Enable auto-start on boot
sudo systemctl enable cybersentinel-agent

# Disable auto-start
sudo systemctl disable cybersentinel-agent

# View logs (real-time)
sudo journalctl -u cybersentinel-agent -f

# View last 100 lines
sudo journalctl -u cybersentinel-agent -n 100

# View logs for today
sudo journalctl -u cybersentinel-agent --since today

# View log file
sudo tail -f /var/log/cybersentinel_agent.log
```

---

### Mass Deployment (Linux)

For deploying to multiple Linux servers:

#### Option 1: Ansible Playbook

Create `deploy-agent.yml`:

```yaml
---
- name: Deploy CyberSentinel DLP Agent
  hosts: all
  become: yes

  vars:
    server_url: "http://192.168.1.100:8000/api/v1"

  tasks:
    - name: Install dependencies
      apt:
        name:
          - python3
          - python3-pip
        state: present

    - name: Copy agent files
      copy:
        src: "{{ item.src }}"
        dest: "{{ item.dest }}"
      loop:
        - { src: agent.py, dest: /opt/cybersentinel/agent.py }
        - { src: agent_config.json, dest: /etc/cybersentinel/agent_config.json }
        - { src: cybersentinel-agent.service, dest: /etc/systemd/system/ }

    - name: Update agent config with hostname
      lineinfile:
        path: /etc/cybersentinel/agent_config.json
        regexp: '"agent_id"'
        line: '  "agent_id": "{{ inventory_hostname }}",'

    - name: Enable and start service
      systemd:
        name: cybersentinel-agent
        state: started
        enabled: yes
        daemon_reload: yes
```

Run deployment:
```bash
ansible-playbook -i inventory.ini deploy-agent.yml
```

#### Option 2: SSH Loop

```bash
#!/bin/bash
SERVERS="server1 server2 server3"
SERVER_IP="192.168.1.100"

for server in $SERVERS; do
    echo "Deploying to $server..."

    # Copy files
    scp -r cybersentinel-linux-agent/ root@$server:/tmp/

    # Run installation
    ssh root@$server "cd /tmp/cybersentinel-linux-agent && \
        sed -i 's/CHANGE_THIS_TO_UNIQUE_ID/$server/' agent_config.json && \
        sed -i 's/YOUR-SERVER-IP/$SERVER_IP/' agent_config.json && \
        ./install.sh"
done
```

---

## Verification

### Check Agent Connection

#### On Dashboard

1. Open browser: `http://YOUR-SERVER-IP:3000`
2. Login with admin credentials
3. Navigate to **Agents** page
4. Verify agent appears with "Online" status

#### Via API

```bash
# List all agents
curl http://YOUR-SERVER-IP:8000/api/v1/agents

# Expected response:
[
  {
    "id": "uuid-here",
    "agent_id": "WIN-DESKTOP-001",
    "name": "JohnDoe-Laptop",
    "os": "Windows 10 Pro",
    "ip_address": "192.168.1.50",
    "status": "online",
    "last_heartbeat": "2025-01-06T10:35:00Z",
    "capabilities": {
      "file_monitoring": true,
      "clipboard_monitoring": true,
      "usb_monitoring": true
    }
  },
  {
    "id": "uuid-here",
    "agent_id": "LINUX-WEB-01",
    "name": "Production-WebServer-01",
    "os": "Ubuntu 22.04",
    "ip_address": "192.168.1.100",
    "status": "online",
    "last_heartbeat": "2025-01-06T10:35:05Z",
    "capabilities": {
      "file_monitoring": true
    }
  }
]
```

### Test Detection

#### Windows Test

```powershell
# Create test file with sensitive data
echo "Credit Card: 4532-1234-5678-9010" > "C:\Users\Public\Documents\test-sensitive.txt"

# Wait a few seconds, then check dashboard for event
```

#### Linux Test

```bash
# Create test file with SSN
echo "SSN: 123-45-6789" > /home/testuser/sensitive.txt

# Check events via API
curl http://YOUR-SERVER-IP:8000/api/v1/events?limit=10
```

---

## Troubleshooting

### Common Issues

#### 1. Agent Can't Connect to Server

**Error:** "Connection refused" or "timeout"

**Solutions:**

```bash
# Test server connectivity
curl http://YOUR-SERVER-IP:8000/health

# Check firewall (on server)
sudo ufw status
sudo ufw allow 8000/tcp

# Check server is running
docker compose ps  # If using Docker
sudo systemctl status cybersentinel-backend  # If manual install

# Test from agent machine
ping YOUR-SERVER-IP
telnet YOUR-SERVER-IP 8000
```

#### 2. Agent Shows Offline

**Solutions:**

- Check agent logs for errors
- Verify `heartbeat_interval` isn't too high
- Ensure `agent_id` is unique
- Check system time is synchronized (NTP)
- Verify network connectivity

#### 3. No Events Being Captured

**Solutions:**

- Verify monitored paths exist
- Check file extensions match
- Ensure agent has read permissions
- Test with known sensitive pattern
- Check `max_file_size_mb` limit

#### 4. Permission Denied Errors

**Windows:**
- Run agent as Administrator
- Check antivirus isn't blocking

**Linux:**
- Run service as root
- Check SELinux/AppArmor policies
```bash
sudo aa-status  # AppArmor
getenforce      # SELinux
```

#### 5. High CPU/Memory Usage

**Solutions:**

- Reduce number of monitored paths
- Add more exclude_paths
- Increase heartbeat_interval
- Reduce max_file_size_mb
- Limit file_extensions list

---

## Configuration Reference

### Agent Config Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `server_url` | string | - | Server API endpoint |
| `agent_id` | string | - | Unique agent identifier |
| `agent_name` | string | - | Display name |
| `heartbeat_interval` | int | 60 | Seconds between heartbeats |
| `monitoring.file_system` | bool | true | Enable file monitoring |
| `monitoring.clipboard` | bool | true | Enable clipboard (Windows only) |
| `monitoring.usb_devices` | bool | true | Enable USB detection (Windows only) |
| `monitoring.monitored_paths` | array | - | Directories to monitor |
| `monitoring.exclude_paths` | array | - | Directories to exclude (Linux) |
| `monitoring.file_extensions` | array | - | File types to scan |
| `classification.enabled` | bool | true | Enable content classification |
| `classification.max_file_size_mb` | int | 10 | Max file size to scan |

---

## Next Steps

After deploying agents:

1. ✅ **Test Detection** - Create test files with sensitive data
2. ✅ **Configure Policies** - Enable/customize DLP policies
3. ✅ **Set Up Alerts** - Configure email/Slack notifications
4. ✅ **Deploy More Agents** - Roll out to additional endpoints
5. ✅ **Monitor Dashboard** - Check events and agent status regularly

---

## Support

**Documentation:**
- Main README: [README.md](README.md)
- Deployment Guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Master Docs: [MASTER_DOCUMENTATION.md](MASTER_DOCUMENTATION.md)

**Repositories:**
- Windows Agent: https://github.com/effaaykhan/cybersentinel-windows-agent
- Linux Agent: https://github.com/effaaykhan/cybersentinel-linux-agent

**Logs:**
- Windows: `C:\Program Files\CyberSentinel\cybersentinel_agent.log`
- Linux: `/var/log/cybersentinel_agent.log` or `journalctl -u cybersentinel-agent`
