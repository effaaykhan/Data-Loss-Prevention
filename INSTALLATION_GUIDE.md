# CyberSentinel DLP - Installation Guide

**Updated:** November 15, 2025  
**Version:** 2.0.0

Complete installation guide for CyberSentinel DLP Dashboard, Linux Agents, and Windows Agents based on the latest codebase updates. Includes comprehensive browser testing procedures.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Dashboard Installation](#dashboard-installation)
3. [Linux Agent Installation](#linux-agent-installation)
4. [Windows Agent Installation](#windows-agent-installation)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+), macOS, or Windows with WSL2
- **Docker**: Version 24.0 or higher
- **Docker Compose**: Version 2.20 or higher
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: At least 50GB free
- **Network**: Ports 3000, 55000, 5432, 27017, 6379, 9200 available

### Required Ports

| Port | Service | Access |
|------|---------|--------|
| 3000 | Dashboard | Public |
| 55000 | API Server | Public |
| 5432 | PostgreSQL | Internal |
| 27017 | MongoDB | Internal |
| 6379 | Redis | Internal |
| 9200 | OpenSearch | Internal |

---

## Dashboard Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/effaaykhan/Data-Loss-Prevention.git
cd Data-Loss-Prevention
```

### Step 2: Configure Environment

#### Get Your Server IP Address

**Linux/macOS:**
```bash
hostname -I | awk '{print $1}'
# Or for WSL2:
ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
```

**Windows (WSL2):**
```bash
# In WSL2 terminal
hostname -I | awk '{print $1}'
```

**Note:** For WSL2, the IP address may change on restart. Use the IP shown by the command above.

#### Update Docker Compose Configuration

Edit `docker-compose.yml` and ensure the following environment variables are set:

```yaml
manager:
  environment:
    - CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://YOUR_IP:3000"]
    - ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_IP
    - PORT=55000
    - OPENSEARCH_USE_SSL=false

dashboard:
  build:
    args:
      - VITE_API_URL=http://YOUR_IP:55000/api/v1
      - VITE_WS_URL=ws://YOUR_IP:55000/ws
      - VITE_APP_NAME=CyberSentinel DLP
      - VITE_APP_VERSION=2.0.0
```

**Replace `YOUR_IP` with your actual server IP address.**

### Step 3: Initialize Database

```bash
# Start database services only
docker-compose up -d postgres mongodb redis opensearch

# Wait for services to be healthy (about 30 seconds)
docker-compose ps

# Initialize database
docker-compose run --rm manager python init_db.py
```

**Expected output:**
```
✓ Users table created
✓ Policies table created
✓ Default admin user created
Database initialization complete!
```

### Step 4: Build and Start Services

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

All services should show "Up" or "Healthy" status.

### Step 5: Verify Dashboard

1. **Check logs:**
```bash
docker-compose logs dashboard | tail -20
docker-compose logs manager | tail -20
```

2. **Access dashboard:**
   - Open browser: `http://YOUR_IP:3000`
   - Default credentials:
     - **Email:** `admin`
     - **Password:** `admin`

3. **Test API:**
```bash
curl http://YOUR_IP:55000/health
# Expected: {"status":"healthy","service":"CyberSentinel DLP","version":"2.0.0"}
```

---

## Linux Agent Installation

### Step 1: Prerequisites

Ensure Python 3.9+ is installed:

```bash
python3 --version
# Should show Python 3.9 or higher

# If not installed (Ubuntu/Debian):
sudo apt update
sudo apt install python3 python3-pip -y
```

### Step 2: Install Dependencies

```bash
cd agents/endpoint/linux

# Install required Python packages
pip3 install -r requirements.txt

# Or if using virtual environment (recommended):
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Agent

#### Option A: Edit Configuration File

Edit `agent_config.json`:

```json
{
  "server_url": "http://YOUR_SERVER_IP:55000/api/v1",
  "agent_id": "",
  "agent_name": "your-hostname",
  "monitor_paths": ["/home", "/tmp"],
  "scan_interval": 60,
  "log_level": "INFO"
}
```

**Important:**
- Replace `YOUR_SERVER_IP` with your server's IP address
- Leave `agent_id` empty to auto-generate
- Set `agent_name` to your hostname or a descriptive name
- Adjust `monitor_paths` as needed

#### Option B: Use Default Configuration

The agent will create a default config at `~/cybersentinel_agent_config.json` if `/etc/cybersentinel` is not writable.

### Step 4: Test Server Connectivity

```bash
# Test if server is reachable
curl http://YOUR_SERVER_IP:55000/health

# Test API endpoint
curl http://YOUR_SERVER_IP:55000/api/v1/health
```

Both should return JSON responses.

### Step 5: Run Agent

#### Manual Run (Testing)

```bash
cd agents/endpoint/linux
python3 agent.py
```

**Expected output:**
```
[INFO] Starting CyberSentinel DLP Agent
[INFO] Agent ID: <generated-uuid>
[INFO] Server URL: http://YOUR_SERVER_IP:55000/api/v1
[INFO] Registering agent...
[INFO] Agent registered successfully
[INFO] Starting file monitoring...
[INFO] Monitoring paths: ['/home', '/tmp']
```

#### Run as Systemd Service (Production)

1. **Create service file:**

```bash
sudo nano /etc/systemd/system/cybersentinel-agent.service
```

2. **Add service configuration:**

```ini
[Unit]
Description=CyberSentinel DLP Agent
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/Data-Loss-Prevention/agents/endpoint/linux
ExecStart=/usr/bin/python3 /path/to/Data-Loss-Prevention/agents/endpoint/linux/agent.py
Restart=always
RestartSec=10
StandardOutput=append:/home/YOUR_USERNAME/cybersentinel_agent.log
StandardError=append:/home/YOUR_USERNAME/cybersentinel_agent.log

[Install]
WantedBy=multi-user.target
```

**Replace:**
- `YOUR_USERNAME` with your Linux username
- `/path/to/Data-Loss-Prevention` with actual path

3. **Enable and start service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable cybersentinel-agent

# Start service
sudo systemctl start cybersentinel-agent

# Check status
sudo systemctl status cybersentinel-agent
```

4. **View logs:**

```bash
# Service logs
sudo journalctl -u cybersentinel-agent -f

# Or application logs
tail -f ~/cybersentinel_agent.log
```

### Step 6: Verify Agent Functionality

**6.1 Check Agent Registration:**
1. Open dashboard: `http://YOUR_SERVER_IP:3000` in your browser
2. Login with `admin` / `admin`
3. Navigate to **Agents** page
4. Verify Linux agent appears in list with:
   - Agent ID: Your configured agent ID
   - Name: Your hostname or configured name
   - OS: `linux`
   - Status: `online`
   - IP Address: Your machine IP
   - Last Seen: Recent timestamp

**6.2 Test File Monitoring:**
```bash
# Create test file with sensitive data
echo "Credit Card: 4532-1234-5678-9010" > ~/test_credit_card.txt

# Check agent logs
tail -f ~/cybersentinel_agent.log
```

**Expected in logs:**
```
INFO - File event detected: file_created - test_credit_card.txt
INFO - Sending file event: file_created - test_credit_card.txt - Severity: critical
```

**Verify in Dashboard:**
1. Navigate to **Events** page
2. Look for the new file event
3. Verify it shows:
   - Severity: `critical` (due to credit card detection)
   - Event type: `file`
   - File path: `/home/username/test_credit_card.txt`
   - Agent ID: Your Linux agent ID

**6.3 Verify Dashboard Overview:**
1. Navigate to **Dashboard** page (main overview)
2. Verify stats cards show:
   - **Total Agents:** Should include your Linux agent
   - **Active Agents:** Should show Linux agent as active
   - **Total Events:** Should include events from Linux agent
   - **Critical Alerts:** Should include critical events from Linux agent
3. Verify charts display data:
   - **Events Over Time:** Should show timeline with events
   - **Events by Type:** Should show file events
   - **Events by Severity:** Should show critical events from Linux agent

**6.4 API Verification (Optional):**
```bash
# Get auth token first
TOKEN=$(curl -X POST http://YOUR_SERVER_IP:55000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

# List agents
curl http://YOUR_SERVER_IP:55000/api/v1/agents \
  -H "Authorization: Bearer $TOKEN"

# Get events
curl http://YOUR_SERVER_IP:55000/api/v1/events?limit=10 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Windows Agent Installation

### Prerequisites

- **Windows 10/11** or **Windows Server 2016+**
- **Python 3.8+** installed on Windows
- **Administrator privileges** (for some features like USB monitoring)
- **WSL2** (if deploying from WSL) or direct Windows access

### Step 1: Copy Agent Files to Windows

If deploying from WSL2, copy files to Windows drive:

```bash
# From WSL terminal
mkdir -p /mnt/d/CyberSentinelAgent
cp -r agents/endpoint/windows/* /mnt/d/CyberSentinelAgent/
```

Or clone directly on Windows:

```powershell
# From Windows PowerShell
git clone https://github.com/effaaykhan/Data-Loss-Prevention.git
cd Data-Loss-Prevention\agents\endpoint\windows
```

### Step 2: Install Python Dependencies

```powershell
# Navigate to agent directory
cd D:\CyberSentinelAgent

# Install dependencies
pip install -r requirements.txt
```

**Required packages:**
- `requests` - HTTP client
- `watchdog` - File system monitoring
- `pywin32` - Windows API access
- `WMI` - Windows Management Instrumentation
- `python-dateutil` - Date utilities

**Note:** If `pywin32` installation fails, you may need to install Visual C++ Redistributables.

### Step 3: Configure Agent

Edit `agent_config.json`:

```json
{
  "server_url": "http://localhost:55000/api/v1",
  "agent_id": "windows-agent-001",
  "agent_name": "Windows-Endpoint-01",
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

**Configuration Notes:**
- `server_url`: Use `http://localhost:55000/api/v1` if server is on same machine (WSL2), or use WSL IP
- `agent_id`: Set unique ID for each Windows machine
- `agent_name`: Descriptive name for the endpoint
- `%USERNAME%`: Automatically expanded to current Windows username
- `monitored_paths`: Paths to monitor for file operations
- `file_extensions`: File types to monitor (empty array = monitor all)

### Step 4: Test Server Connectivity

```powershell
# Test server health endpoint
Invoke-WebRequest -Uri "http://localhost:55000/health" -UseBasicParsing

# Should return: {"status":"healthy","service":"CyberSentinel DLP","version":"2.0.0"}
```

### Step 5: Run Agent

#### Manual Run (Testing)

```powershell
# Navigate to agent directory
cd D:\CyberSentinelAgent

# Run agent
python agent.py
```

**Expected output:**
```
2025-11-15 12:19:33 - INFO - Agent initialized: windows-agent-001
2025-11-15 12:19:33 - INFO - Starting CyberSentinel DLP Agent...
2025-11-15 12:19:33 - INFO - Agent registered with server
2025-11-15 12:19:33 - INFO - Monitoring path: C:\Users\Public\Documents
2025-11-15 12:19:33 - INFO - Monitoring path: C:\Users\YourUsername\Documents
2025-11-15 12:19:33 - INFO - Clipboard monitoring started
2025-11-15 12:19:33 - INFO - USB monitoring started
2025-11-15 12:19:33 - INFO - Agent started successfully
```

#### Run as Windows Service (Production)

**Option A: Using NSSM (Recommended)**

1. Download NSSM from https://nssm.cc/download
2. Extract and run as Administrator:

```powershell
# Install service
nssm install CyberSentinelDLP "C:\Python311\python.exe"
nssm set CyberSentinelDLP AppDirectory "D:\CyberSentinelAgent"
nssm set CyberSentinelDLP AppParameters "agent.py"
nssm set CyberSentinelDLP DisplayName "CyberSentinel DLP Agent"
nssm set CyberSentinelDLP Description "Data Loss Prevention endpoint agent"

# Start service
nssm start CyberSentinelDLP

# Check status
nssm status CyberSentinelDLP
```

**Option B: Using PowerShell**

```powershell
# Create service
New-Service -Name "CyberSentinelDLP" `
    -BinaryPathName "C:\Python311\python.exe D:\CyberSentinelAgent\agent.py" `
    -DisplayName "CyberSentinel DLP Agent" `
    -Description "Data Loss Prevention endpoint agent" `
    -StartupType Automatic

# Start service
Start-Service -Name "CyberSentinelDLP"

# Check status
Get-Service -Name "CyberSentinelDLP"
```

### Step 6: Verify Agent Functionality

1. **Check Agent Registration:**
   - Open dashboard: `http://YOUR_SERVER_IP:3000`
   - Navigate to Agents page
   - Verify Windows agent appears in list

2. **Test File Monitoring:**
   ```powershell
   # Create test file in monitored directory
   New-Item -Path "C:\Users\Public\Documents\test.txt" -ItemType File -Value "Test content"
   
   # Check agent logs
   Get-Content D:\CyberSentinelAgent\cybersentinel_agent.log -Tail 20
   ```

3. **Test Clipboard Monitoring:**
   ```powershell
   # Copy sensitive data to clipboard
   Set-Clipboard -Value "SSN: 123-45-6789"
   
   # Check logs for clipboard event
   Get-Content D:\CyberSentinelAgent\cybersentinel_agent.log -Tail 10
   ```

4. **Test USB Monitoring:**
   - Connect USB device
   - Check logs for USB connection event

5. **Verify Events in Dashboard:**
   - Navigate to Events page
   - Verify file, clipboard, and USB events appear

### Windows-Specific Features

- **Clipboard Monitoring**: Detects sensitive data copied to clipboard
- **USB Device Detection**: Alerts when USB devices are connected
- **Environment Variable Expansion**: Supports `%USERNAME%` and other Windows env vars in paths
- **Windows Path Support**: Handles Windows-style paths (`C:\Users\...`)

### Troubleshooting Windows Agent

**Issue: Agent cannot connect to server**
- Verify server is running: `Invoke-WebRequest http://localhost:55000/health`
- Check firewall settings
- If using WSL2, ensure `localhost` resolves correctly

**Issue: File monitoring not working**
- Verify monitored paths exist
- Check file permissions
- Ensure agent has read access to monitored directories

**Issue: Clipboard monitoring errors**
- Run agent as Administrator
- Check Windows clipboard service is running

**Issue: USB monitoring not working**
- Run agent as Administrator
- Verify Windows Management Instrumentation service is running

**Issue: Environment variables not expanding**
- Ensure using latest agent code (includes `os.path.expandvars()`)
- Check paths use Windows format: `C:\Users\%USERNAME%\Documents`

---

## Configuration

### Dashboard Configuration

#### Environment Variables (Build Time)

Set in `docker-compose.yml` under `dashboard.build.args`:

- `VITE_API_URL`: API server URL (e.g., `http://172.23.19.78:55000/api/v1`)
- `VITE_WS_URL`: WebSocket URL (e.g., `ws://172.23.19.78:55000/ws`)
- `VITE_APP_NAME`: Application name
- `VITE_APP_VERSION`: Application version

#### CORS Configuration

Set in `docker-compose.yml` under `manager.environment`:

```yaml
- CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://YOUR_IP:3000"]
- ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_IP
```

### Agent Configuration

#### Configuration File Location

1. **System-wide:** `/etc/cybersentinel/agent_config.json` (requires root)
2. **User-specific:** `~/cybersentinel_agent_config.json` (fallback)

#### Configuration Options

```json
{
  "server_url": "http://YOUR_SERVER_IP:55000/api/v1",
  "agent_id": "auto-generated-if-empty",
  "agent_name": "hostname-or-custom-name",
  "monitor_paths": ["/home", "/tmp", "/opt"],
  "scan_interval": 60,
  "log_level": "INFO",
  "exclude_patterns": [".git", "node_modules", "__pycache__"]
}
```

#### Log File Location

- Default: `~/cybersentinel_agent.log`
- Configurable via environment variable: `CYBERSENTINEL_LOG_FILE`

---

## Verification

### Dashboard Verification

#### Step 1: Health Check
```bash
curl http://YOUR_IP:55000/health
```

Expected response:
```json
{"status":"healthy","service":"CyberSentinel DLP","version":"2.0.0"}
```

#### Step 2: Browser Testing - Complete Dashboard Verification

**2.1 Login Test:**
1. Open `http://YOUR_IP:3000` in your browser
2. You should see the login page with CyberSentinel branding
3. Login with credentials:
   - **Username:** `admin`
   - **Password:** `admin`
4. After successful login, you should be redirected to the dashboard

**2.2 Dashboard Overview Verification:**
1. **Check Stats Cards:**
   - **Total Agents:** Should show the number of registered agents (e.g., "3")
   - **Active Agents:** Should show agents with "online" status
   - **Total Events:** Should show total event count (e.g., "362")
   - **Critical Alerts:** Should show count of critical severity events

2. **Check Charts:**
   - **Events Over Time:** Should display a line chart with event counts over time
   - **Events by Type:** Should show a pie chart with event type distribution (file, clipboard, usb, etc.)
   - **Events by Severity:** Should show a bar chart with severity distribution (critical, high, medium, low)
   - **DLP Actions:** Should show blocked events, active alerts, and total events

**2.3 Agents Page Verification:**
1. Click on **"Agents"** in the sidebar navigation
2. Verify the following:
   - Agent list displays all registered agents
   - Each agent shows:
     - Agent ID
     - Name
     - OS (windows/linux)
     - IP Address
     - Status (online/offline)
     - Last Seen timestamp
     - Registered timestamp
   - Windows agent should appear with:
     - Agent ID: `windows-agent-001` (or your configured ID)
     - OS: `windows`
     - Status: `online`
   - Linux agents should appear with their respective details

**2.4 Events Page Verification:**
1. Click on **"Events"** in the sidebar navigation
2. Verify the following:
   - Events list displays recent events
   - Each event shows:
     - Severity badge (critical, high, medium, low)
     - Event type (file, clipboard, usb)
     - Agent ID or "Unknown Agent"
     - Timestamp
     - Event ID
     - File path (for file events)
   - Search functionality works (try searching for `agent_id:windows-agent-001`)
   - Filter options are available
   - Test file events should appear:
     - Look for files created during testing (e.g., `browser_test_file.txt`, `sensitive_data.txt`)
     - Critical severity events should be highlighted

**2.5 Alerts Page Verification:**
1. Click on **"Alerts"** in the sidebar navigation
2. Verify the following:
   - **Stats Cards:**
     - **New Alerts:** Should show count of critical/high severity events (e.g., "33")
     - **Acknowledged:** Should show count of acknowledged alerts (initially "0")
     - **Resolved:** Should show count of resolved alerts (initially "0")
   - **Alerts List:**
     - Displays alerts generated from critical/high severity events
     - Each alert shows:
       - Severity badge (critical, high)
       - Status badge (New, Acknowledged, Resolved)
       - Alert title (e.g., "Sensitive Data Detected in File", "Sensitive Data Copied to Clipboard")
       - Alert description with file path (for file events)
       - Agent ID
       - Timestamp (relative time, e.g., "about 6 hours ago")
       - Event ID
     - **Acknowledge** and **Resolve** buttons are available for each alert
   - **Alert Types:**
     - File alerts: Show file path in description
     - Clipboard alerts: Show "Sensitive data detected in clipboard content"
     - USB alerts: Show USB device connection information
   - **Data Consistency:**
     - New Alerts count should match or be close to Dashboard's "Critical Alerts" count
     - Alerts correspond to critical/high severity events from Events page

**2.6 Windows Agent Event Verification:**
1. **Create Test File:**
   ```powershell
   # On Windows machine
   New-Item -Path "C:\Users\Public\Documents\test_verification.txt" -ItemType File -Force -Value "SSN: 123-45-6789"
   ```

2. **Check Dashboard:**
   - Navigate to Events page
   - Look for the new file event
   - Verify it shows:
     - Severity: `critical` (due to SSN detection)
     - Event type: `file`
     - File path: `C:\Users\Public\Documents\test_verification.txt`
     - Agent ID: `windows-agent-001`

3. **Test Clipboard Monitoring:**
   ```powershell
   # On Windows machine
   Set-Clipboard -Value "API Key: sk-1234567890abcdef"
   ```
   - Wait a few seconds
   - Check Events page for clipboard event
   - Should show severity: `high` or `critical` (due to API key detection)

**2.7 Linux Agent Event Verification:**
1. **Create Test File:**
   ```bash
   # On Linux machine
   echo "Credit Card: 4532-1234-5678-9010" > ~/test_verification.txt
   ```

2. **Check Dashboard:**
   - Navigate to Events page
   - Look for the new file event
   - Verify it shows:
     - Severity: `critical` (due to credit card detection)
     - Event type: `file`
     - File path: `/home/username/test_verification.txt`
     - Agent ID: Your Linux agent ID

**2.8 Dashboard Data Consistency:**
- Verify that dashboard stats match the data shown in:
  - Agents page (agent counts)
  - Events page (event counts)
  - Alerts page (alert counts should match critical/high severity events)
  - All numbers should be consistent across pages

3. **API Test:**
```bash
# Get token
TOKEN=$(curl -X POST http://YOUR_IP:55000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

# Test events endpoint
curl http://YOUR_IP:55000/api/v1/events?limit=10 \
  -H "Authorization: Bearer $TOKEN"
```

### Agent Verification

1. **Agent Status:**
```bash
# Check if agent is running
ps aux | grep agent.py

# Check logs
tail -f ~/cybersentinel_agent.log
```

2. **Server Connectivity:**
   - Agent should appear in dashboard "Agents" page
   - Status should show "online" or "active"
   - Last seen timestamp should be recent

3. **Event Generation:**
```bash
# Create a test file with sensitive data
echo "SSN: 123-45-6789" > /tmp/test_ssn.txt

# Check agent logs for detection
tail -f ~/cybersentinel_agent.log | grep -i "ssn\|detected"

# Check events in dashboard
# Navigate to Events page - should show new event
```

---

## Troubleshooting

### Dashboard Issues

#### Dashboard Not Loading

**Symptoms:** Blank page or connection refused

**Solutions:**
1. Check if dashboard container is running:
```bash
docker-compose ps dashboard
```

2. Check dashboard logs:
```bash
docker-compose logs dashboard
```

3. Verify CORS configuration includes your IP
4. Check browser console for errors

#### Authentication Not Working

**Symptoms:** Login fails or redirects loop

**Solutions:**
1. Verify API server is running:
```bash
curl http://YOUR_IP:55000/health
```

2. Check API logs:
```bash
docker-compose logs manager | grep -i "auth\|login"
```

3. Verify default admin user exists:
```bash
docker-compose exec postgres psql -U cybersentinel_dlp -d cybersentinel_dlp -c "SELECT email, role FROM users;"
```

#### Events Not Displaying

**Symptoms:** Events page shows "0 events found"

**Solutions:**
1. Check API response:
```bash
curl http://YOUR_IP:55000/api/v1/events?limit=10 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. Check MongoDB for events:
```bash
docker-compose exec mongodb mongosh -u cybersentinel_dlp -p YOUR_PASSWORD --eval "db.dlp_events.countDocuments()"
```

3. Verify API response format matches frontend expectations

### Agent Issues

#### Agent Not Connecting

**Symptoms:** Agent doesn't appear in dashboard

**Solutions:**
1. Check server URL in config:
```bash
cat ~/cybersentinel_agent_config.json | grep server_url
```

2. Test server connectivity:
```bash
curl http://YOUR_SERVER_IP:55000/health
```

3. Check agent logs:
```bash
tail -f ~/cybersentinel_agent.log
```

4. Verify firewall allows outbound connections

#### Permission Errors

**Symptoms:** "Permission denied" errors in logs

**Solutions:**
1. Agent uses user-writable locations:
   - Config: `~/cybersentinel_agent_config.json`
   - Logs: `~/cybersentinel_agent.log`

2. If running as service, ensure user has permissions:
```bash
sudo chown YOUR_USER:YOUR_USER ~/cybersentinel_agent.log
```

#### File Monitoring Not Working

**Symptoms:** No events detected

**Solutions:**
1. Verify monitor paths are correct:
```bash
cat ~/cybersentinel_agent_config.json | grep monitor_paths
```

2. Test with a file containing sensitive data:
```bash
echo "Credit Card: 4532-1234-5678-9010" > /tmp/test_cc.txt
```

3. Check agent logs for file system events:
```bash
tail -f ~/cybersentinel_agent.log | grep -i "file\|event"
```

### Common Issues

#### Port Already in Use

**Error:** `Bind for 0.0.0.0:55000 failed: port is already allocated`

**Solution:**
```bash
# Find process using port
sudo lsof -i :55000

# Kill process or change port in docker-compose.yml
```

#### Database Connection Errors

**Error:** `connection refused` or `database does not exist`

**Solution:**
1. Wait for database to be ready:
```bash
docker-compose ps postgres mongodb
```

2. Reinitialize database:
```bash
docker-compose run --rm manager python init_db.py
```

#### CORS Errors

**Error:** `No 'Access-Control-Allow-Origin' header`

**Solution:**
1. Add your IP to `CORS_ORIGINS` in `docker-compose.yml`
2. Restart manager service:
```bash
docker-compose restart manager
```

---

## Additional Resources

- **Changelog:** See `CHANGELOG.md` for detailed list of changes
- **Architecture:** See `ARCHITECTURE.md` for system design
- **API Documentation:** Access at `http://YOUR_IP:55000/docs` when server is running
- **Deployment Guide:** See `DEPLOYMENT_GUIDE.md` for production deployment

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review troubleshooting section above
3. Check GitHub issues: https://github.com/effaaykhan/Data-Loss-Prevention/issues

---

**End of Installation Guide**


