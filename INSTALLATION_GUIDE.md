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

> **Documentation scope:** This guide plus `TESTING_COMMANDS.md`, `README.md`, and `plan.md` are the active docs. Historical or deprecated references now live under `archive/` for posterity.

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

#### Update Environment for Containers (avoid host-IP drift)

Use `.env` to drive both manager and dashboard. For local/WSL installs you can keep the dashboard hitting the API via `localhost` (inside the docker network). For remote browsers, set these to your host/IP before building:

```
# .env
CORS_ORIGINS=["http://<HOST>:3000","http://127.0.0.1:3000"]
VITE_API_URL=http://<HOST>:55000/api/v1
VITE_WS_URL=ws://<HOST>:55000/ws
```

After changing these, rebuild the dashboard:

```bash
docker compose build --no-cache dashboard
docker compose up -d dashboard
```

#### Agent deployment (remote host)
- Windows: run `scripts/install_windows_agent.ps1 -ManagerUrl "http://<HOST>:55000/api/v1"` (or set `CYBERSENTINEL_SERVER_URL` before running).
- Linux: run `scripts/install_linux_agent.sh --manager-url http://<HOST>:55000/api/v1` (or set `CYBERSENTINEL_SERVER_URL`); service autostarts on boot.

### Step 3: Initialize Database

```bash
# Start database services only
docker-compose up -d postgres mongodb redis opensearch

# Wait for services to be healthy (about 30 seconds)
docker-compose ps

# Wait until all show "healthy" or "Up"
# You can also check logs:
docker-compose logs postgres | tail -10
docker-compose logs mongodb | tail -10

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

### POSSIBLE BUGS
### Bug 1: ENUM mismatch
- ERROR
  ```
  invalid input value for enum userrole: "admin"
  ```
- FIX
  ```
  docker exec -it cybersentinel-postgres psql -U dlp_user -d cybersentinel_dlp -c "
  ALTER TYPE user_role RENAME VALUE 'admin' TO 'ADMIN';
  ALTER TYPE user_role RENAME VALUE 'analyst' TO 'ANALYST';
  ALTER TYPE user_role RENAME VALUE 'viewer' TO 'VIEWER';
  ALTER TYPE user_role RENAME VALUE 'agent' TO 'AGENT';
  "
  ```

### Bug 2: bcrypt broken
- Error:
```
(trapped) error reading bcrypt version
module 'bcrypt' has no attribute '__about__'
```
- Fix
```
docker exec -it cybersentinel-manager bash -c "pip install bcrypt==4.0.1"
```

### ✔ AFTER FIXES — Create admin again
- Once ENUM and bcrypt are fixed, run this again:
```
docker exec -it cybersentinel-manager bash
```
THEN
```
python - << 'EOF'
import asyncio
from app.core.database import init_databases
from app.core.database import get_db_session
from app.services.user_service import UserService

async def main():
    await init_databases()
    
    gen = get_db_session()
    db = next(gen)

    try:
        service = UserService(db)
        user = await service.create_user(
            email="admin@local",
            password="Admin123!",
            role="ADMIN",
            full_name="Administrator"
        )
        print("Admin created:", user.email)
    finally:
        try: next(gen)
        except StopIteration: pass

asyncio.run(main())
EOF
```

✔ After running, verify:
```
docker exec -it cybersentinel-postgres psql -U dlp_user -d cybersentinel_dlp -c "SELECT email, role FROM users;"
```

You should see:

```
admin@local | admin
```
✔ LOGIN TO DASHBOARD
```
admin@local
Admin123!
```


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


## SIMPLE WINDOWS AGENT INSTALLATION as a Service
- Create an installer file in any directory:
  ```
  notepad windows-agent_installer.py
  ```
- Paste the [content](https://github.com/effaaykhan/Data-Loss-Prevention/blob/main/windows-agent_installer.py) in this file:
- Add the details prompted on the screen.

### Step 1: Copy Agent Files to Windows

If deploying from WSL2, copy files to Windows drive:

```bash
# From WSL terminal (if deploying to Windows via WSL)
# Choose a location on your Windows machine (e.g., D:\CyberSentinelAgent)
mkdir -p /mnt/d/CyberSentinelAgent
cp -r agents/endpoint/windows/* /mnt/d/CyberSentinelAgent/

# Or deploy directly on Windows:
# Choose a location like C:\Program Files\CyberSentinel or D:\CyberSentinelAgent
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

**Note:** If you see a USB monitoring threading error (`wmi.x_wmi_uninitialised_thread`), ensure you're using the latest `agent.py` file which includes the COM initialization fix. The error should not appear with the updated code.

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
- **USB Monitoring Threading Error:** If you see `wmi.x_wmi_uninitialised_thread` error:
  - Ensure you're using the latest `agent.py` file (includes COM initialization fix)
  - The fix uses `CoInitializeEx` with `COINIT_MULTITHREADED` flag for proper thread initialization
  - If error persists, verify `pywin32` package is properly installed: `pip install --upgrade pywin32`

**Issue: Environment variables not expanding**
- Ensure using latest agent code (includes `os.path.expandvars()`)
- Check paths use Windows format: `C:\Users\%USERNAME%\Documents`

**Issue: File transfer blocking not working**
- Ensure `transfer_blocking.enabled` is set to `true` in agent config
- Verify monitored paths are correctly configured
- Check that files exist in monitored directories before copying to USB
- Agent requires Administrator privileges for file deletion
- Check agent logs for "Permission denied" errors (Windows Explorer may lock files temporarily)
- The agent automatically retries file operations if locked (up to 5 attempts)

---

## Google Drive Integration Setup

### Prerequisites

- Google Cloud Platform (GCP) account
- Google Drive API enabled in GCP project
- OAuth 2.0 credentials (Client ID and Client Secret)

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable **Google Drive API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

### Step 2: Create OAuth 2.0 Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure OAuth consent screen (if not done):
   - User Type: External (or Internal for G Suite)
   - App name: "CyberSentinel DLP"
   - Scopes: `https://www.googleapis.com/auth/drive.activity.readonly`
4. Create OAuth client:
   - Application type: Web application
   - Authorized redirect URIs: `http://YOUR_SERVER_IP:55000/api/v1/google-drive/callback`
   - Save Client ID and Client Secret

### Step 3: Configure Environment Variables

Add to `.env` file:

```bash
# Google Drive OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://YOUR_SERVER_IP:55000/api/v1/google-drive/callback
```

**Replace:**
- `YOUR_SERVER_IP` with your server IP address
- `your-client-id` and `your-client-secret` with your OAuth credentials

### Step 4: Restart Services

```bash
docker-compose restart manager celery-worker celery-beat
```

### Step 5: Create Google Drive Policy

1. Open dashboard: `http://YOUR_SERVER_IP:3000`
2. Navigate to **Policies** page
3. Click **"Create Policy"**
4. Select **"Google Drive Cloud"** policy type
5. Click **"Connect Google Drive"** button
6. Complete OAuth flow:
   - Authorize CyberSentinel to access Google Drive
   - Select folders to protect
   - Confirm folder selection
7. Configure policy:
   - Name, description, severity, priority
   - Review selected protected folders
   - Save policy

### Step 6: Verify Polling

1. Create a file in a protected Google Drive folder
2. Wait up to 5 minutes (or click "Manual Refresh" in Events page)
3. Check Events page for new Google Drive event
4. Event should show:
   - Source: `google_drive_cloud`
   - Event type: `file`
   - Event subtype: `file_created` (or `file_modified`, `file_deleted`)
   - File path: Google Drive folder path
   - Timestamp: Actual Google Drive activity timestamp

### Baseline Management

**What is a baseline?**
- A timestamp stored per protected folder indicating when monitoring started
- Only events after the baseline are fetched (prevents historical data re-ingestion)
- Baseline is automatically set to `datetime.utcnow()` when folder is added to policy

**Reset Baseline:**
1. Go to Policies page
2. Edit Google Drive Cloud policy
3. Use "Reset Selected Baseline" or "Reset Connection Baseline" buttons
4. This will start monitoring from the current time forward

**View Baseline:**
- Policy form shows "Monitoring since" date for each connection
- Individual folder baselines shown in protected folders list

### Troubleshooting Google Drive Integration

**OAuth flow fails:**
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
- Check redirect URI matches GCP OAuth client configuration
- Ensure Google Drive API is enabled in GCP project

**No events appearing:**
- Check Celery worker logs: `docker-compose logs celery-worker | grep -i "google\|drive"`
- Verify protected folders are configured in policy
- Check baseline timestamps (may need to reset if too old)
- Use "Manual Refresh" button to trigger immediate poll

**Duplicate events:**
- Baseline system should prevent this
- If duplicates appear, reset baseline for affected folders
- Check event IDs are deterministic (should not change between polls)

**Polling not running:**
- Verify Celery Beat is running: `docker-compose ps celery-beat`
- Check Celery Beat logs: `docker-compose logs celery-beat`
- Verify schedule in `server/app/tasks/reporting_tasks.py` (default: every 5 minutes)

---

## OneDrive Integration Setup

### Prerequisites

- Microsoft account (Personal or Microsoft 365)
- Azure Portal access (free account works)
- Microsoft Graph API access (included with Microsoft account)

**Note:** File download detection requires a Microsoft 365 subscription. Personal OneDrive accounts can monitor file creation, modification, deletion, and movement, but not downloads.

### Step 1: Create Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com/)
2. Sign in with your Microsoft account
3. Navigate to **Azure Active Directory** (or **Microsoft Entra ID**)
4. Click **App registrations** in the left sidebar
5. Click **+ New registration**

### Step 2: Configure App Registration

1. **Name**: Enter "CyberSentinel DLP" (or your preferred name)
2. **Supported account types**: 
   - Select **"Accounts in any organizational directory and personal Microsoft accounts"** for maximum compatibility
   - Or **"Personal Microsoft accounts only"** if only personal accounts will be used
3. **Redirect URI**:
   - Platform: **Web**
   - URI: `http://YOUR_SERVER_IP:55000/api/v1/onedrive/callback`
   - Replace `YOUR_SERVER_IP` with your server IP address
4. Click **Register**

### Step 3: Configure API Permissions

1. In your app registration, click **API permissions** in the left sidebar
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Choose **Delegated permissions**
5. Add the following permissions:
   - `Files.Read` - Read user files
   - `Files.Read.All` - Read all files that the user can access
   - `Sites.Read.All` - Read items in all site collections (if needed)
   - `User.Read` - Sign in and read user profile
6. Click **Add permissions**
7. **Important**: Click **Grant admin consent** (if you have admin rights) or users will need to consent during OAuth flow

### Step 4: Create Client Secret

1. In your app registration, click **Certificates & secrets** in the left sidebar
2. Click **+ New client secret**
3. **Description**: Enter "CyberSentinel DLP Secret" (or any description)
4. **Expires**: Choose expiration (recommended: 24 months or Never for testing)
5. Click **Add**
6. **IMPORTANT**: Copy the **Value** immediately (it won't be shown again)
   - Save it securely - you'll need it for the `.env` file

### Step 5: Get Application (Client) ID

1. In your app registration, go to **Overview**
2. Copy the **Application (client) ID** - this is your `ONEDRIVE_CLIENT_ID`
3. Copy the **Directory (tenant) ID** - this is your `ONEDRIVE_TENANT_ID` (usually `common` or your tenant ID)

### Step 6: Configure Environment Variables

Add to `.env` file:

```bash
# OneDrive OAuth
ONEDRIVE_CLIENT_ID=your-client-id-here
ONEDRIVE_CLIENT_SECRET=your-client-secret-value-here
ONEDRIVE_TENANT_ID=common
ONEDRIVE_REDIRECT_URI=http://YOUR_SERVER_IP:55000/api/v1/onedrive/callback
```

**Replace:**
- `YOUR_SERVER_IP` with your server IP address (e.g., `192.168.1.100` or `localhost` for local testing)
- `your-client-id-here` with your Application (client) ID from Step 5
- `your-client-secret-value-here` with the client secret Value from Step 4
- `ONEDRIVE_TENANT_ID`:
  - Use `common` for personal Microsoft accounts and organizational accounts
  - Use your specific tenant ID if you only want organizational accounts
  - Use `consumers` for personal Microsoft accounts only
  - Use `organizations` for organizational accounts only

**Example:**
```bash
# OneDrive OAuth
ONEDRIVE_CLIENT_ID=12345678-abcd-1234-abcd-123456789abc
ONEDRIVE_CLIENT_SECRET=abc~DEF123ghi456JKL789mno012PQR345stu678
ONEDRIVE_TENANT_ID=common
ONEDRIVE_REDIRECT_URI=http://192.168.1.100:55000/api/v1/onedrive/callback
```

### Step 7: Restart Services

```bash
docker-compose restart manager celery-worker celery-beat
```

### Step 8: Create OneDrive Policy

1. Open dashboard: `http://YOUR_SERVER_IP:3000`
2. Navigate to **Policies** page
3. Click **"Create Policy"**
4. Select **"OneDrive (Cloud)"** policy type
5. Click **"Connect Account"** button
6. Complete OAuth flow:
   - A popup window will open for Microsoft authentication
   - Sign in with your Microsoft account
   - Grant permissions to CyberSentinel DLP
   - Authorize access to your OneDrive files
   - The popup will close automatically after successful authentication
7. Configure policy:
   - Select protected folders using the folder browser
   - Name, description, severity, priority
   - Set polling interval (default: 10 minutes)
   - Review selected protected folders
   - Save policy

### Step 9: Verify Polling

1. Create or modify a file in a protected OneDrive folder
2. Wait up to 5 minutes (or trigger manual poll via API)
3. Check Events page for new OneDrive event
4. Event should show:
   - Source: `onedrive_cloud`
   - Event type: `file`
   - Event subtype: `file_created`, `file_modified`, `file_deleted`, or `file_moved`
   - File path: OneDrive folder path
   - Timestamp: Actual OneDrive activity timestamp

### Baseline Management

**What is a baseline?**
- A timestamp stored per protected folder indicating when monitoring started
- Only events after the baseline are fetched (prevents historical data re-ingestion)
- Baseline is automatically set to `datetime.utcnow()` when folder is added to policy
- Delta tokens are used for efficient incremental sync

**Reset Baseline:**
1. Go to Policies page
2. Edit OneDrive Cloud policy
3. Use "Reset Selected Baseline" or "Reset Connection Baseline" buttons
4. This will start monitoring from the current time forward
5. Delta tokens will be reset, causing a full sync on next poll

**View Baseline:**
- Policy form shows "Monitoring since" date for each connection
- Individual folder baselines shown in protected folders list

### Limitations

**File Download Detection:**
- **Not available** for personal OneDrive accounts
- Requires Microsoft 365 subscription and Audit Logs API access
- Current implementation focuses on file operations (create, modify, delete, move) via Graph API delta queries

**Supported Operations:**
- ✅ File creation
- ✅ File modification (with hybrid detection - uses Redis + ETag comparison)
- ✅ File deletion
- ✅ File movement/renaming
- ❌ File downloads (requires M365 subscription)

**Hybrid Modification Detection:**
- Uses Microsoft Graph API delta queries for reliable file creations and deletions
- For file modifications, uses hybrid approach:
  - Stores file state (ETag, version, lastModifiedDateTime) in Redis
  - When delta reports "updated" or suspected modification, verifies by comparing current ETag with stored state
  - Accurately detects real file content modifications vs. metadata-only changes
  - Prevents false create+delete pairs when users modify file content
- Gracefully falls back to delta-only mode if Redis is unavailable

### Troubleshooting OneDrive Integration

**OAuth flow fails:**
- Verify `ONEDRIVE_CLIENT_ID` and `ONEDRIVE_CLIENT_SECRET` in `.env`
- Check redirect URI matches Azure app registration configuration exactly
- Ensure redirect URI uses `http://` (not `https://`) if testing locally
- Verify tenant ID is correct (`common` for most cases)
- Check browser console for OAuth errors

**"AADSTS50011: Redirect URI mismatch" error:**
- Ensure redirect URI in `.env` exactly matches Azure app registration
- Check for trailing slashes or protocol mismatches
- Verify port number is correct (default: 55000)

**"AADSTS700016: Application not found" error:**
- Verify `ONEDRIVE_CLIENT_ID` is correct
- Check tenant ID matches your account type
- Ensure app registration exists in the correct Azure AD tenant

**No events appearing:**
- Check Celery worker logs: `docker-compose logs celery-worker | grep -i "onedrive"`
- Verify protected folders are configured in policy
- Check baseline timestamps (may need to reset if too old)
- Verify delta tokens are being stored (check database)
- Check Graph API rate limits (shouldn't be an issue for normal usage)

**Duplicate events:**
- Baseline system and delta tokens should prevent this
- If duplicates appear, reset baseline for affected folders
- Check event IDs are deterministic (should not change between polls)
- Verify delta tokens are being properly stored and used

**Polling not running:**
- Verify Celery Beat is running: `docker-compose ps celery-beat`
- Check Celery Beat logs: `docker-compose logs celery-beat`
- Verify schedule in `server/app/tasks/reporting_tasks.py` (default: every 5 minutes)
- Check for errors in OneDrive polling task logs

**Token refresh failures:**
- Verify client secret hasn't expired
- Check refresh token is being stored correctly
- Ensure MSAL library is properly configured
- Check network connectivity to Microsoft identity endpoints

**Graph API errors:**
- Verify API permissions are granted (check Azure Portal)
- Ensure admin consent is granted if required
- Check for rate limiting (429 errors)
- Verify folder IDs are correct

### Manual Testing

**Test OAuth flow:**
```bash
# Get auth URL
curl -X POST http://localhost:55000/api/v1/onedrive/connect \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return auth_url and state
```

**Test folder listing:**
```bash
# List folders for a connection
curl http://localhost:55000/api/v1/onedrive/connections/CONNECTION_ID/folders \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Trigger manual poll:**
```bash
# Manually trigger OneDrive polling
curl -X POST http://localhost:55000/api/v1/onedrive/poll \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Configuration

### Dashboard Configuration

#### Environment Variables Configuration

**Using .env file (Recommended):**

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set:
   - `SERVER_IP`: Your server IP or domain (default: `localhost`)
   - `CORS_ORIGINS`: Comma-separated list of allowed origins (e.g., `http://localhost:3000,http://127.0.0.1:3000`)
   - `VITE_API_URL`: Dashboard API URL (defaults to `http://localhost:55000/api/v1`)
   - `VITE_WS_URL`: WebSocket URL (defaults to `ws://localhost:55000/ws`)
   - Database passwords and `SECRET_KEY`
   - `GOOGLE_CLIENT_ID`: Google OAuth Client ID (for Google Drive integration)
   - `GOOGLE_CLIENT_SECRET`: Google OAuth Client Secret (for Google Drive integration)
   - `GOOGLE_REDIRECT_URI`: OAuth redirect URI (e.g., `http://YOUR_SERVER_IP:55000/api/v1/google-drive/callback`)
   - `ONEDRIVE_CLIENT_ID`: Microsoft Azure App (client) ID (for OneDrive integration)
   - `ONEDRIVE_CLIENT_SECRET`: Microsoft Azure Client Secret (for OneDrive integration)
   - `ONEDRIVE_TENANT_ID`: Azure AD Tenant ID (usually `common` for personal and organizational accounts)
   - `ONEDRIVE_REDIRECT_URI`: OAuth redirect URI (e.g., `http://YOUR_SERVER_IP:55000/api/v1/onedrive/callback`)

**Manual Configuration (docker-compose.yml):**

Set in `docker-compose.yml` under `dashboard.build.args`:

- `VITE_API_URL`: API server URL (defaults to `http://localhost:55000/api/v1`)
- `VITE_WS_URL`: WebSocket URL (defaults to `ws://localhost:55000/ws`)

Set in `docker-compose.yml` under `manager.environment`:

```yaml
- CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000,http://127.0.0.1:3000}
- ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost,127.0.0.1}
```

**Note:** All values now use environment variables with sensible defaults. No hardcoded IPs required!

### Agent Configuration

#### Configuration File Location

1. **System-wide:** `/etc/cybersentinel/agent_config.json` (requires root)
2. **User-specific:** `~/cybersentinel_agent_config.json` (fallback)

#### Configuration Options

**Basic Configuration:**
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

**Windows Agent - File Transfer Blocking (USB/Removable Drives):**

The Windows agent can detect and block file transfers to removable drives (USB drives, external SSDs). When enabled, the agent monitors removable drives and automatically deletes files that match files in monitored directories.

**Configuration:**
```json
{
  "server_url": "http://localhost:55000/api/v1",
  "agent_id": "windows-agent-001",
  "agent_name": "Windows-Agent",
  "heartbeat_interval": 30,
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
    "file_extensions": [".pdf", ".docx", ".xlsx", ".txt", ".csv", ".json", ".xml"],
    "transfer_blocking": {
      "enabled": true,
      "block_removable_drives": true,
      "poll_interval_seconds": 5
    }
  },
  "classification": {
    "enabled": true,
    "max_file_size_mb": 10
  }
}
```

**Transfer Blocking Settings:**
- `enabled`: Enable/disable transfer blocking (default: `false`)
- `block_removable_drives`: Block transfers to removable drives (default: `true`)
- `poll_interval_seconds`: How often to check for new files on removable drives (default: `5`)

**How It Works:**
1. Agent monitors specified directories for file changes
2. When a file is copied to a removable drive, the agent detects it
3. Agent calculates SHA256 hash of the copied file
4. Agent searches monitored directories for a file with matching hash
5. If match found, agent deletes the file from the removable drive
6. Agent sends a blocked transfer event to the server with `action: "blocked"`

**Important Notes:**
- Transfer blocking only works for files that exist in monitored directories
- Files are deleted from the removable drive after copy completes (not during copy)
- The agent handles Windows file locking issues automatically with retry mechanism
- Blocked transfers appear in the dashboard Events page with "Action Taken: Blocked"

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


