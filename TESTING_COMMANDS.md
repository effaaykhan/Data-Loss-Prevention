# CyberSentinel DLP - Step-by-Step Testing Guide

**Date:** November 15, 2025  
**Purpose:** Manual testing of committed code from scratch

> **Doc map:** Pair this runbook with `INSTALLATION_GUIDE.md` for setup. Anything not explicitly covered lives in `archive/docs/` as historical reference.

---

## Prerequisites Check

### 1. Verify Docker is Running
```bash
docker ps
# Should show running containers or empty list
```

### 2. Verify Python is Installed (for agents)
```bash
python3 --version
# Should show Python 3.9 or higher
```

### 3. Check Required Ports
```bash
# Check if ports are available
netstat -tuln | grep -E "3000|55000|5432|27017|6379|9200"
# Or use: ss -tuln | grep -E "3000|55000|5432|27017|6379|9200"
```

---

## Step 1: Start Docker Services

### 1.1 Navigate to Project Directory
```bash
cd /home/vansh/Code/Data-Loss-Prevention
```

### 1.2 Start Database Services First
```bash
docker-compose up -d postgres mongodb redis opensearch
```

### 1.3 Wait for Services to be Healthy (30 seconds)
```bash
# Check service status
docker-compose ps

# Wait until all show "healthy" or "Up"
# You can also check logs:
docker-compose logs postgres | tail -10
docker-compose logs mongodb | tail -10
```

### 1.4 Initialize Database
```bash
docker-compose run --rm manager python init_db.py
```

**Expected output:**
```
✓ Users table created
✓ Policies table created
✓ Default admin user created
Database initialization complete!
```

### 1.5 Build and Start All Services
```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Verify all services are running
docker-compose ps
```

**Expected:** All services should show "Up" or "Healthy"

---

## Step 2: Verify Dashboard is Running

### 2.1 Check Dashboard Logs
```bash
docker-compose logs dashboard | tail -20
```

### 2.2 Check Manager/API Logs
```bash
docker-compose logs manager | tail -20
```

### 2.3 Test API Health Endpoint
```bash
curl http://localhost:55000/health
```

**Expected response:**
```json
{"status":"healthy","service":"CyberSentinel DLP","version":"2.0.0"}
```

### 2.4 Access Dashboard in Browser
```bash
# Open in browser:
http://localhost:3000
```

**Login credentials:**
- **Email:** `admin`
- **Password:** `admin`

---

## Step 3: Test Dashboard Functionality

### 3.1 Login Test
1. Open `http://localhost:3000` in browser
2. You should see login page
3. Enter credentials: `admin` / `admin`
4. Click "Sign In"
5. Should redirect to dashboard

### 3.2 Dashboard Overview Verification
1. After login, verify dashboard loads without errors and cards populate. The exact counts depend on current DB state (e.g., during final QA we expect **Total Agents = 2**, **Active Agents = 2**, **Total Events ≈ 100+**, **Critical Alerts ≥ recent violations**). The key check is that numbers render and update as events/agents come online.
2. Charts (Events Over Time / by Type / by Severity / DLP Actions) should render with whatever live data exists. If you initialized a brand-new database they will start at zero.

### 3.3 Navigate to Agents Page
1. Click "Agents" in sidebar
2. After the agents (Step 4/5) register you should see both Linux and Windows entries with live `last_seen`, IPs, and policy sync metadata.

### 3.4 Navigate to Events Page
1. Click "Events" in sidebar
2. If you have not generated events yet it will say “0 events found”. With existing data, use `*` in the search bar and hit **Search** to list all records.
3. Confirm the table renders and that clicking a row shows the right-hand drawer with policy match details.

### 3.5 Backend API Smoke Tests
Run these from another terminal (still inside the repo root) after services are up:

```bash
# 1) Obtain token (capture JSON)
curl -i -X POST http://localhost:55000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# Convenience: store token in ENV for the shell session
export TOKEN=$(curl -s -X POST http://localhost:55000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2) Policy listing + stats
curl -i http://localhost:55000/api/v1/policies/ -H "Authorization: Bearer $TOKEN"
curl -i http://localhost:55000/api/v1/policies/stats/summary -H "Authorization: Bearer $TOKEN"

# 3) CRUD smoke (creates temporary policy, updates it, toggles, then deletes)
curl -i -X POST http://localhost:55000/api/v1/policies/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"CLI QA Policy","description":"temporary","priority":80,"type":"clipboard_monitoring","severity":"medium","enabled":true,"config":{"patterns":{"predefined":["email"],"custom":[]},"action":"alert"}}'

# Replace POLICY_ID with the ID returned above
curl -i -X PUT http://localhost:55000/api/v1/policies/POLICY_ID \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"CLI QA Policy","description":"updated","priority":70,"type":"clipboard_monitoring","severity":"high","enabled":false,"config":{"patterns":{"predefined":["email","api_key"],"custom":[]},"action":"alert"}}'

curl -i -X POST http://localhost:55000/api/v1/policies/POLICY_ID/enable \
  -H "Authorization: Bearer $TOKEN"
curl -i -X POST http://localhost:55000/api/v1/policies/POLICY_ID/disable \
  -H "Authorization: Bearer $TOKEN"
curl -i -X DELETE http://localhost:55000/api/v1/policies/POLICY_ID \
  -H "Authorization: Bearer $TOKEN"

# 4) Event ingestion smoke
curl -i -X POST http://localhost:55000/api/v1/events/ \
  -H "Content-Type: application/json" \
  -d '{"event_id":"qa-cli-001","agent_id":"cli-agent","agent_name":"CLI Agent","agent_type":"linux","agent_version":"1.0.0","event_type":"file","event_subtype":"file_created","severity":"medium","file_path":"/home/vansh/Code/Data-Loss-Prevention/tmp_linux_policy/final_ssn.txt","file_extension":".txt","content":"SSN: 123-45-6789","timestamp":"'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"}'

curl -i "http://localhost:55000/api/v1/events/?limit=5" -H "Authorization: Bearer $TOKEN"
```

These steps confirm the policy transformer, stats endpoint, EventProcessor, and Mongo persistence are healthy before moving on to agent tests.

---

## Step 4: Start Linux Agent

### 4.1 Navigate to Linux Agent Directory
```bash
cd /home/vansh/Code/Data-Loss-Prevention/agents/endpoint/linux
```

### 4.2 Check Configuration
```bash
cat agent_config.json
```

**Verify:**
- `server_url` is set to `http://localhost:55000/api/v1`
- `agent_id` is set (or empty for auto-generation)

### 4.3 Install Dependencies (if needed)
```bash
pip3 install -r requirements.txt
```

### 4.4 Start Linux Agent
```bash
python3 agent.py
```

**Expected output:**
```
[INFO] Starting CyberSentinel DLP Agent
[INFO] Agent ID: <generated-uuid>
[INFO] Server URL: http://localhost:55000/api/v1
[INFO] Registering agent...
[INFO] Agent registered successfully
[INFO] Starting file monitoring...
[INFO] Monitoring paths: [...]
```

**Keep this terminal open** - agent should keep running

### 4.5 Verify Linux Agent in Dashboard
1. Go back to browser
2. Navigate to **Agents** page
3. Refresh page (F5)
4. Should see Linux agent in list:
   - Agent ID: Your agent ID
   - OS: `linux`
   - Status: `online`
   - Last Seen: Recent timestamp

### 4.6 Test Linux Agent File Monitoring
```bash
# In a NEW terminal (keep agent running in first terminal)
# Create test file with sensitive data
echo "SSN: 123-45-6789" > /tmp/test_linux_ssn.txt

# Wait 5 seconds, then check agent logs (in first terminal)
# You should see file event detection logs
```

### 4.7 Verify Linux Agent Events in Dashboard
1. Go to **Events** page in browser
2. Refresh page
3. Should see new file event:
   - Event type: `file`
   - Severity: `critical` (due to SSN detection)
   - Agent ID: Your Linux agent ID
   - File path: `/tmp/test_linux_ssn.txt`

### 4.8 Verify Dashboard Overview Updated
1. Go to **Dashboard** page
2. Refresh page
3. Should show:
   - **Total Agents:** 1
   - **Active Agents:** 1
   - **Total Events:** 1 (or more)
   - **Critical Alerts:** 1 (or more)
4. Charts should show data

---

## Step 5: Start Windows Agent

### 5.1 Copy Agent Files to Windows (if needed)
```bash
# From WSL terminal
cp -r /home/vansh/Code/Data-Loss-Prevention/agents/endpoint/windows/* /mnt/d/CyberSentinelAgent/
```

### 5.2 On Windows Machine - Navigate to Agent Directory
```powershell
# Open PowerShell
cd D:\CyberSentinelAgent
```

### 5.3 Verify Configuration
```powershell
Get-Content agent_config.json
```

**Verify:**
- `server_url` is set to `http://localhost:55000/api/v1`
- `agent_id` is set (e.g., `windows-agent-001`)

### 5.4 Install Dependencies (if needed)
```powershell
pip install -r requirements.txt
```

### 5.5 Start Windows Agent
```powershell
python agent.py
```

**Expected output:**
```
2025-11-15 XX:XX:XX - INFO - Agent initialized: windows-agent-001
2025-11-15 XX:XX:XX - INFO - Starting CyberSentinel DLP Agent...
2025-11-15 XX:XX:XX - INFO - Agent registered with server
2025-11-15 XX:XX:XX - INFO - Monitoring path: C:\Users\Public\Documents
2025-11-15 XX:XX:XX - INFO - Monitoring path: C:\Users\YourUsername\Documents
2025-11-15 XX:XX:XX - INFO - Clipboard monitoring started
2025-11-15 XX:XX:XX - INFO - USB monitoring started
2025-11-15 XX:XX:XX - INFO - Agent started successfully
```

**Important:** Should NOT see any USB monitoring threading errors!

**Keep this PowerShell window open** - agent should keep running

### 5.6 Verify Windows Agent in Dashboard
1. Go to **Agents** page in browser
2. Refresh page
3. Should see both agents:
   - Linux agent
   - Windows agent (with `windows-agent-001` ID)
   - Both showing status: `online`

### 5.7 Test Windows Agent File Monitoring
```powershell
# In PowerShell (on Windows machine)
# Create test file with sensitive data
echo "Credit Card: 4532-1234-5678-9010" | Out-File -FilePath "$env:USERPROFILE\Documents\test_windows_cc.txt" -Encoding utf8
```

### 5.8 Test Windows Agent Clipboard Monitoring
```powershell
# Copy sensitive data to clipboard
Set-Clipboard -Value "API Key: sk-1234567890abcdef"
```

### 5.9 Verify Windows Agent Events in Dashboard
1. Go to **Events** page in browser
2. Refresh page
3. Should see new events:
   - File event: `test_windows_cc.txt` (severity: critical)
   - Clipboard event: API key detection (severity: high/critical)
   - Both from agent: `windows-agent-001`

### 5.10 Verify Dashboard Overview Updated
1. Go to **Dashboard** page
2. Refresh page
3. Should show:
   - **Total Agents:** 2
   - **Active Agents:** 2
   - **Total Events:** Increased count
   - **Critical Alerts:** Increased count
4. Charts should show data from both agents

---

## Step 6: Test Alerts Page

### 6.1 Navigate to Alerts Page
1. Click **Alerts** in sidebar
2. Should see alerts generated from critical/high severity events

### 6.2 Verify Alerts Display
- Stats cards show alert counts
- Alert list shows:
  - File alerts (from file events)
  - Clipboard alerts (from clipboard events)
  - Severity badges (critical, high)
  - Status badges (New)

---

## Step 7: Test Search and Filtering

### 7.1 Test Event Search
1. Go to **Events** page
2. In search box, type: `agent_id:windows-agent-001`
3. Click "Search"
4. Should show only Windows agent events

### 7.2 Test Event Filter by Type
1. Clear search
2. Try searching: `event_type:file`
3. Should show only file events

### 7.3 Test Event Filter by Severity
1. Clear search
2. Try searching: `severity:critical`
3. Should show only critical events

---

## Step 8: Verify USB Monitoring (Windows Agent)

### 8.1 Check Windows Agent Logs
```powershell
# In PowerShell (on Windows machine)
Get-Content D:\CyberSentinelAgent\cybersentinel_agent.log -Tail 20
```

**Verify:**
- Should see: "USB monitoring started"
- Should NOT see: `wmi.x_wmi_uninitialised_thread` error

### 8.2 Test USB Device Connection (Optional)
- Connect a USB device to Windows machine
- Check agent logs for USB connection event
- Check Events page for USB event

---

## Step 9: Final Verification

### 9.1 Dashboard Data Consistency Check
1. **Dashboard Overview:**
   - Total Agents = 2
   - Active Agents = 2
   - Total Events = Sum of all events
   - Critical Alerts = Count of critical/high events

2. **Agents Page:**
   - Shows 2 agents (Linux + Windows)
   - Both showing "online" status
   - Recent "Last Seen" timestamps

3. **Events Page:**
   - Shows events from both agents
   - Can filter by agent_id
   - Events have correct severity and types

4. **Alerts Page:**
   - Shows alerts generated from critical/high events
   - Alert count matches dashboard "Critical Alerts"

### 9.2 API Verification (Optional)
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:55000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Test agents endpoint
curl -s http://localhost:55000/api/v1/agents \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -30

# Test events endpoint
curl -s "http://localhost:55000/api/v1/events?limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## Step 10: Cleanup (After Testing)

### 10.1 Stop Agents
```bash
# Linux agent: Press Ctrl+C in the terminal running agent.py
# Windows agent: Press Ctrl+C in PowerShell window
```

### 10.2 Stop Docker Services
```bash
cd /home/vansh/Code/Data-Loss-Prevention
docker-compose down
```

### 10.3 Verify Everything Stopped
```bash
# Check Docker containers
docker ps

# Check agent processes
ps aux | grep agent.py | grep -v grep
```

---

## Troubleshooting

### Dashboard Not Loading
- Check: `docker-compose logs dashboard`
- Verify port 3000 is not in use: `netstat -tuln | grep 3000`

### Agent Not Connecting
- Check: `docker-compose logs manager | grep -i error`
- Verify server URL in agent config
- Test: `curl http://localhost:55000/health`

### Events Not Showing
- Check agent logs for errors
- Verify agent is sending events: `docker-compose logs manager | grep -i event`
- Check MongoDB: `docker-compose exec mongodb mongosh --eval "use cybersentinel_dlp; db.dlp_events.countDocuments()"`

### USB Monitoring Error (Windows)
- Ensure using latest `agent.py` with COM initialization fix
- Verify `pywin32` is installed: `pip show pywin32`
- Check agent logs for specific error messages

---

## Expected Test Results

✅ **Dashboard:**
- Login works
- All pages load correctly
- Stats show correct counts
- Charts display data

✅ **Linux Agent:**
- Registers successfully
- File monitoring works
- Events appear in dashboard

✅ **Windows Agent:**
- Registers successfully
- File monitoring works
- Clipboard monitoring works
- USB monitoring works (no threading errors)
- Events appear in dashboard

✅ **Data Consistency:**
- Dashboard stats match Agents/Events/Alerts pages
- All numbers are consistent across pages

---

**End of Testing Guide**

