# CyberSentinel DLP - Wazuh-Based Architecture Design

**Version:** 2.0 (Complete Redesign)
**Date:** 2025-01-12
**Status:** Phase 1 - MVP Development

---

## 🎯 Executive Summary

CyberSentinel DLP is an enterprise-grade Data Loss Prevention solution built following Wazuh's proven architecture. This system provides real-time monitoring, classification, and prevention of sensitive data exfiltration across Windows and Linux endpoints.

---

## 🏗️ Architecture Overview (Wazuh-Based 3-Tier)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          TIER 1: AGENTS                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │ Windows Agent   │  │  Linux Agent    │  │  More Agents    │    │
│  │  (Python)       │  │  (Python)       │  │  (Python)       │    │
│  │                 │  │                 │  │                 │    │
│  │ • File Monitor  │  │ • File Monitor  │  │ • File Monitor  │    │
│  │ • Clipboard     │  │ • Clipboard     │  │ • Clipboard     │    │
│  │ • USB Monitor   │  │ • USB Monitor   │  │ • USB Monitor   │    │
│  │ • Network Mon   │  │ • Network Mon   │  │ • Network Mon   │    │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘    │
│           │                    │                     │              │
│           └────────────────────┼─────────────────────┘              │
│                                │                                    │
└────────────────────────────────┼────────────────────────────────────┘
                                 │ HTTPS/TLS (Port 55000)
                                 │ JSON Events
┌────────────────────────────────┼────────────────────────────────────┐
│                          TIER 2: MANAGER                             │
│                                 ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    DLP Manager (Server)                       │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │  Event Processor & Analyzer                             │ │  │
│  │  │  • Agent Communication Handler                          │ │  │
│  │  │  • Event Queue Manager                                  │ │  │
│  │  │  • Classification Engine                                │ │  │
│  │  │  • Policy Engine (YAML Rules)                           │ │  │
│  │  │  • Correlation Engine                                   │ │  │
│  │  │  • Alert Generator                                      │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │  Storage Layer                                          │ │  │
│  │  │  • OpenSearch / Elasticsearch (Events, Logs)           │ │  │
│  │  │  • PostgreSQL (Users, Config, Agents)                  │ │  │
│  │  │  • Redis (Cache, Sessions, Queue)                      │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    RESTful API Server                         │  │
│  │                  FastAPI (Port 55000/tcp)                     │  │
│  │  • Agent Management API                                       │  │
│  │  • Event Ingestion API                                        │  │
│  │  • Policy Management API                                      │  │
│  │  • User & Auth API                                            │  │
│  │  • Analytics & Reporting API                                  │  │
│  │  • Integration API (SIEM, Cloud, etc)                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ HTTPS/REST (Port 55000)
┌────────────────────────────────┼────────────────────────────────────┐
│                          TIER 3: DASHBOARD                           │
│                                 ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              CyberSentinel Dashboard (React)                  │  │
│  │                    Port 3000 (HTTP/HTTPS)                     │  │
│  │                                                               │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐           │  │
│  │  │  Overview Dashboard │  │  Agents Management  │           │  │
│  │  │  • Real-time Stream │  │  • Agent List       │           │  │
│  │  │  • Event Charts     │  │  • Agent Details    │           │  │
│  │  │  • Alerts Summary   │  │  • Agent Groups     │           │  │
│  │  └─────────────────────┘  └─────────────────────┘           │  │
│  │                                                               │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐           │  │
│  │  │  Events & Logs      │  │  Policy Management  │           │  │
│  │  │  • KQL Search Bar   │  │  • YAML Editor      │           │  │
│  │  │  • Time Filters     │  │  • Policy Templates │           │  │
│  │  │  • Event Details    │  │  • Rule Testing     │           │  │
│  │  └─────────────────────┘  └─────────────────────┘           │  │
│  │                                                               │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐           │  │
│  │  │  Visualizations     │  │  Settings & Admin   │           │  │
│  │  │  • Graphs           │  │  • User Management  │           │  │
│  │  │  • Bar Charts       │  │  • Integrations     │           │  │
│  │  │  • Pie Charts       │  │  • System Config    │           │  │
│  │  └─────────────────────┘  └─────────────────────┘           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Breakdown

### 1. **DLP Agents (TIER 1)**

**Purpose:** Deployed on endpoints to monitor and collect DLP events

**Technology:**
- Language: Python 3.10+
- Service: Windows Service / systemd daemon
- Communication: HTTPS/TLS to Manager
- Configuration: YAML files

**Capabilities:**

#### Windows Agent
```python
- File System Monitor (watchdog library)
  • Desktop, Documents, Downloads, Network shares
  • Real-time file operations (create, modify, delete, copy, move)
  • Content extraction and classification

- Clipboard Monitor (pyperclip/win32clipboard)
  • Text content monitoring
  • Sensitive data detection in clipboard

- USB Device Monitor (WMI)
  • Device connection/disconnection
  • File transfer detection
  • Auto-block policies

- Network Monitor (scapy)
  • Email attachments (SMTP)
  • HTTP/HTTPS uploads
  • Cloud storage uploads

- Process Monitor
  • Application-level DLP
  • Print job monitoring
  • Screenshot detection
```

#### Linux Agent
```python
- File System Monitor (inotify)
  • /home, /tmp, /var, custom paths
  • File operations monitoring

- Clipboard Monitor (xclip/xsel)
  • X11 clipboard monitoring

- USB Monitor (udev)
  • Device events

- Network Monitor (tcpdump/scapy)
  • Network traffic analysis
```

**Agent Registration Flow:**
```
1. Agent starts → Reads config.yaml
2. If not registered:
   - Generate agent key
   - Send registration request to Manager (POST /v1/agents/register)
   - Manager validates and assigns agent_id
   - Agent stores credentials
3. Establish persistent connection
4. Send heartbeat every 60s
5. Stream events in real-time
```

---

### 2. **DLP Manager (TIER 2)**

**Purpose:** Central server for event processing, policy enforcement, and data storage

**Technology:**
- Framework: FastAPI (Python 3.11+)
- ASGI Server: Uvicorn with Gunicorn workers
- Task Queue: Celery with Redis broker
- Storage: OpenSearch + PostgreSQL + Redis

**Components:**

#### A. Event Processor
```yaml
Input: Raw events from agents (JSON)
Process:
  1. Event validation
  2. Normalization
  3. Enrichment (geo-location, threat intel)
  4. Classification (ML models)
  5. Policy evaluation
  6. Alert generation
  7. Storage (OpenSearch)
Output: Processed events, alerts, incidents
```

#### B. Policy Engine
```yaml
Rules Format: YAML
Location: /etc/cybersentinel/policies/*.yml

Example Policy:
  name: "Credit Card Detection"
  id: "policy-001"
  enabled: true
  severity: critical
  conditions:
    - field: "content"
      pattern: '\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
      type: regex
  actions:
    - type: alert
      severity: critical
    - type: block
      message: "Credit card detected"
    - type: notify
      channels: ["email", "slack"]
```

#### C. Classification Engine
```python
Classifiers:
  1. Pattern-Based (Regex)
     - Credit cards (PAN)
     - SSN
     - Email addresses
     - Phone numbers
     - API keys, tokens

  2. ML-Based (scikit-learn/TensorFlow)
     - Document classification
     - Sensitive data scoring
     - Anomaly detection
     - User behavior analysis

  3. Fingerprinting
     - SHA-256 hashing
     - Fuzzy hashing (ssdeep)
     - Document fingerprinting
```

#### D. Correlation Engine
```python
Purpose: Detect complex attack patterns
Examples:
  - Multiple file copies + USB connection
  - Large data transfer + external email
  - After-hours access + sensitive data access

Implementation: Rule-based correlation with time windows
```

---

### 3. **RESTful API (TIER 2)**

**Port:** 55000 (Wazuh standard)
**Protocol:** HTTPS with JWT authentication
**Documentation:** OpenAPI 3.0 (Swagger UI at /docs)

**API Categories:**

#### Core Endpoints (Phase 1 MVP)
```http
# Agent Management
POST   /v1/agents/register           # Agent auto-enrollment
POST   /v1/agents/auth               # Agent authentication
GET    /v1/agents                    # List all agents
GET    /v1/agents/{agent_id}         # Get agent details
PATCH  /v1/agents/{agent_id}/status  # Update agent status
DELETE /v1/agents/{agent_id}         # Remove agent

# Event Ingestion
POST   /v1/events                    # Submit single event
POST   /v1/events/batch              # Batch event submission
GET    /v1/events                    # Query events (KQL support)
GET    /v1/events/{event_id}         # Get event details

# Authentication
POST   /v1/auth/login                # User login
POST   /v1/auth/logout               # User logout
POST   /v1/auth/refresh              # Refresh token

# Policies
GET    /v1/policies                  # List policies
GET    /v1/policies/{policy_id}      # Get policy details
POST   /v1/policies                  # Create policy
PATCH  /v1/policies/{policy_id}      # Update policy

# System
GET    /v1/system/health             # Health check
GET    /v1/system/version            # Version info
```

#### Extended Endpoints (Phase 2+)
```http
# All remaining 70+ endpoints to be implemented incrementally
```

---

### 4. **Dashboard (TIER 3)**

**Technology:**
- Framework: React 18+ with TypeScript
- Build Tool: Vite
- State Management: Redux Toolkit
- UI Library: Material-UI (MUI) or Ant Design
- Charts: Recharts / ApexCharts
- KQL Parser: Custom implementation

**Pages & Features:**

#### A. Overview Dashboard
```
┌────────────────────────────────────────────────────┐
│  📊 Real-Time Event Stream                         │
│  ┌──────────────────────────────────────────────┐ │
│  │ [14:30:45] CRITICAL - Credit card detected   │ │
│  │ [14:30:32] WARNING - Large file transfer     │ │
│  │ [14:30:15] INFO - USB device connected       │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  📈 Events Timeline (Last 24h)                    │
│  ┌──────────────────────────────────────────────┐ │
│  │        ▂▃▅▆█▆▅▄▃▂▁▂▃▅▆█▆▅▄▃                 │ │
│  │  00:00  06:00  12:00  18:00  24:00          │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  🥧 Events by Severity      📊 Top 10 Agents     │
│  ┌────────────┐             ┌──────────────────┐ │
│  │ Critical   │             │ AGENT-001 ████   │ │
│  │ High       │             │ AGENT-002 ███    │ │
│  │ Medium     │             │ AGENT-003 ██     │ │
│  └────────────┘             └──────────────────┘ │
└────────────────────────────────────────────────────┘
```

#### B. Events & Logs Page (KQL Search)
```
┌────────────────────────────────────────────────────┐
│  🔍 Search: event.type:"file" AND severity:"high"  │
│  📅 Time: Last 24 hours ▼    [Custom Range]       │
├────────────────────────────────────────────────────┤
│  Timestamp          | Event Type | Agent    | Sev │
│  2025-01-12 14:30  | file_copy  | AGENT-001| 🔴  │
│  2025-01-12 14:29  | clipboard  | AGENT-002| 🟡  │
│  2025-01-12 14:28  | usb_conn   | AGENT-001| 🔵  │
├────────────────────────────────────────────────────┤
│  << Previous | Page 1 of 10 | Next >>             │
└────────────────────────────────────────────────────┘
```

#### C. KQL Parser Implementation
```javascript
Supported KQL Syntax:
- Field queries: event.type:"file"
- Boolean operators: AND, OR, NOT
- Wildcards: event.type:file*
- Ranges: timestamp > "2025-01-01"
- Nested fields: agent.os:"windows"
- Grouping: (field1:value1 OR field2:value2) AND field3:value3

Parser: Custom recursive descent parser
Output: OpenSearch/Elasticsearch query DSL
```

#### D. Visualizations
```
Charts Library: Recharts / ApexCharts
Types:
  - Line Charts (time series)
  - Bar Charts (top N analysis)
  - Pie Charts (distribution)
  - Heatmaps (correlation)
  - Gauges (metrics)
  - Sankey diagrams (data flow)
```

---

## 💾 Data Storage Architecture

### OpenSearch/Elasticsearch (Primary Event Store)
```yaml
Indices:
  - cybersentinel-events-{YYYY.MM.DD}
    • Daily rolling indices
    • Event data with full-text search
    • 90-day retention (configurable)

  - cybersentinel-alerts-{YYYY.MM.DD}
    • Alert data
    • 1-year retention

  - cybersentinel-incidents
    • Incident tracking
    • No auto-deletion

Mappings:
  timestamp: date
  event_id: keyword
  agent_id: keyword
  event_type: keyword
  severity: keyword
  user: text + keyword
  file_path: text + keyword
  content: text
  classification: nested
  metadata: object
```

### PostgreSQL (Configuration & Users)
```sql
Tables:
  - users (id, username, email, password_hash, role)
  - agents (id, agent_id, name, os, ip, status, last_seen)
  - policies (id, name, yaml_content, enabled, created_at)
  - agent_groups (id, name, description)
  - agent_group_members (agent_id, group_id)
  - api_keys (id, key_hash, user_id, permissions)
  - audit_logs (id, user_id, action, timestamp, details)
```

### Redis (Cache & Queue)
```
Use Cases:
  - Session storage (user sessions)
  - Rate limiting (API throttling)
  - Task queue (Celery broker)
  - Real-time metrics cache
  - Agent connection pool
```

---

## 🔐 Security Architecture

### Agent-Manager Communication
```yaml
Protocol: TLS 1.3
Port: 55000
Authentication:
  - Initial: Agent registration key (one-time)
  - Persistent: JWT tokens (refresh every 24h)
Certificate: Self-signed or Let's Encrypt
```

### User Authentication
```yaml
Method: JWT (JSON Web Tokens)
Token Types:
  - Access Token (15 min expiry)
  - Refresh Token (7 days expiry)
Hashing: bcrypt (password)
MFA: Optional TOTP support
```

### RBAC (Role-Based Access Control)
```yaml
Roles:
  - admin: Full system access
  - analyst: View events, create reports
  - operator: Manage agents, policies
  - viewer: Read-only access

Permissions: Granular per API endpoint
```

---

## 📝 Configuration Files (YAML)

### Manager Configuration: `/etc/cybersentinel/manager.yml`
```yaml
server:
  host: 0.0.0.0
  port: 55000
  workers: 4
  tls:
    enabled: true
    cert: /etc/cybersentinel/certs/server.crt
    key: /etc/cybersentinel/certs/server.key

databases:
  opensearch:
    hosts: ["localhost:9200"]
    username: admin
    password: ${OPENSEARCH_PASSWORD}
    index_prefix: cybersentinel

  postgresql:
    host: localhost
    port: 5432
    database: cybersentinel_dlp
    username: dlp_user
    password: ${POSTGRES_PASSWORD}

  redis:
    host: localhost
    port: 6379
    password: ${REDIS_PASSWORD}
    db: 0

authentication:
  jwt_secret: ${JWT_SECRET}
  access_token_expire_minutes: 15
  refresh_token_expire_days: 7

agent_enrollment:
  auto_approve: true
  require_registration_key: false

policies:
  directory: /etc/cybersentinel/policies
  reload_interval: 300  # seconds

logging:
  level: INFO
  file: /var/log/cybersentinel/manager.log
  max_size_mb: 100
  backup_count: 10
```

### Agent Configuration: `C:\Program Files\CyberSentinel\config.yml` (Windows)
### Agent Configuration: `/etc/cybersentinel/agent_config.json` (Linux)
```yaml
agent:
  id: ""  # Auto-assigned during registration
  name: "${HOSTNAME}"
  manager_url: "https://SERVER_IP:55000"
  registration_key: ""  # Optional

monitoring:
  file_system:
    enabled: true
    paths:
      - "C:\\Users\\${USERNAME}\\Desktop"      # Windows
      - "C:\\Users\\${USERNAME}\\Documents"
      - "C:\\Users\\Public\\Documents"
      # Linux:
      # - "/home/${USER}/Desktop"
      # - "/home/${USER}/Documents"
    extensions:
      - .pdf
      - .docx
      - .xlsx
      - .txt
      - .csv
      - .pptx
    exclude_patterns:
      - "*.tmp"
      - "~$*"

  clipboard:
    enabled: true
    scan_interval: 5  # seconds

  usb:
    enabled: true
    auto_block: false
    allowed_devices: []

  network:
    enabled: false  # Resource intensive
    protocols: ["http", "smtp", "ftp"]

classification:
  enabled: true
  max_file_size_mb: 10
  patterns_file: patterns.yml  # Local pattern cache

reporting:
  heartbeat_interval: 60
  batch_size: 100
  batch_interval: 30
  retry_attempts: 3
  retry_delay: 5

logging:
  level: INFO
  file: cybersentinel_agent.log
  max_size_mb: 50
```

### Policy Example: `/etc/cybersentinel/policies/pci-dss.yml`
```yaml
policy:
  id: policy-pci-001
  name: "PCI-DSS Credit Card Protection"
  description: "Detects and blocks credit card numbers (PAN)"
  enabled: true
  severity: critical
  category: compliance
  compliance: ["PCI-DSS 3.2.1"]

  rules:
    - id: rule-001
      name: "Credit Card Pattern Detection"
      conditions:
        - field: content
          operator: regex
          value: '\b(?:\d{4}[\s-]?){3}\d{4}\b'
        - field: content
          operator: luhn_check  # Special validator
          value: true

      actions:
        - type: alert
          severity: critical
          message: "Credit card number detected in ${file_path}"

        - type: block
          enabled: true
          message: "This action has been blocked due to PCI-DSS policy"

        - type: quarantine
          enabled: true
          destination: /var/quarantine/

        - type: notify
          channels:
            - email: security@company.com
            - slack: "#security-alerts"

      metadata:
        mitre_attack: ["T1005"]  # Data from Local System
        tags: ["pci-dss", "credit-card", "financial"]
```

---

## 🚀 Deployment Architecture

### Docker Compose Setup
```yaml
services:
  # Manager (Backend API + Event Processor)
  cybersentinel-manager:
    image: cybersentinel/manager:latest
    ports:
      - "55000:55000"
    volumes:
      - ./config:/etc/cybersentinel
      - ./policies:/etc/cybersentinel/policies
      - manager-logs:/var/log/cybersentinel
    environment:
      - OPENSEARCH_PASSWORD=changeme
      - POSTGRES_PASSWORD=changeme
      - REDIS_PASSWORD=changeme
      - JWT_SECRET=changeme
    depends_on:
      - opensearch
      - postgresql
      - redis

  # Dashboard (React Frontend)
  cybersentinel-dashboard:
    image: cybersentinel/dashboard:latest
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=https://localhost:55000

  # OpenSearch (Event Storage)
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=changeme
    volumes:
      - opensearch-data:/usr/share/opensearch/data

  # PostgreSQL (Config Storage)
  postgresql:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=cybersentinel_dlp
      - POSTGRES_USER=dlp_user
      - POSTGRES_PASSWORD=changeme
    volumes:
      - postgres-data:/var/lib/postgresql/data

  # Redis (Cache & Queue)
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass changeme
    volumes:
      - redis-data:/data

volumes:
  opensearch-data:
  postgres-data:
  redis-data:
  manager-logs:
```

---

## 📦 Repository Structure

### Monorepo (Single Repository)
```
cybersentinel-dlp/
├── README.md
├── LICENSE
├── ARCHITECTURE.md (this file)
├── CHANGELOG.md
├── docker-compose.yml
├── .gitignore
├── .env.example
│
├── manager/                    # Backend (Python FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── setup.py
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agents.py
│   │   │   │   ├── events.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── policies.py
│   │   │   │   ├── users.py
│   │   │   │   ├── incidents.py
│   │   │   │   ├── detection.py
│   │   │   │   ├── audit.py
│   │   │   │   └── system.py
│   │   ├── core/
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   ├── opensearch.py
│   │   │   ├── redis.py
│   │   │   └── config_loader.py
│   │   ├── models/
│   │   │   ├── agent.py
│   │   │   ├── event.py
│   │   │   ├── policy.py
│   │   │   ├── user.py
│   │   │   └── incident.py
│   │   ├── services/
│   │   │   ├── event_processor.py
│   │   │   ├── policy_engine.py
│   │   │   ├── classifier.py
│   │   │   ├── correlation_engine.py
│   │   │   ├── alert_manager.py
│   │   │   └── agent_manager.py
│   │   ├── schemas/
│   │   │   ├── agent.py
│   │   │   ├── event.py
│   │   │   └── policy.py
│   │   └── utils/
│   │       ├── kql_parser.py
│   │       ├── validators.py
│   │       └── helpers.py
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
│
├── dashboard/                  # Frontend (React)
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── public/
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── components/
│       │   ├── Dashboard/
│       │   │   ├── Overview.tsx
│       │   │   ├── EventStream.tsx
│       │   │   └── Charts.tsx
│       │   ├── Agents/
│       │   │   ├── AgentList.tsx
│       │   │   ├── AgentDetails.tsx
│       │   │   └── AgentGroups.tsx
│       │   ├── Events/
│       │   │   ├── EventsList.tsx
│       │   │   ├── EventDetails.tsx
│       │   │   ├── KQLSearchBar.tsx
│       │   │   └── TimeRangePicker.tsx
│       │   ├── Policies/
│       │   │   ├── PolicyList.tsx
│       │   │   ├── PolicyEditor.tsx
│       │   │   └── YAMLValidator.tsx
│       │   ├── Incidents/
│       │   ├── Settings/
│       │   └── Common/
│       ├── services/
│       │   ├── api.ts
│       │   ├── auth.ts
│       │   └── websocket.ts
│       ├── utils/
│       │   ├── kqlParser.ts
│       │   ├── dateFormatter.ts
│       │   └── validators.ts
│       ├── store/              # Redux
│       │   ├── index.ts
│       │   ├── agentSlice.ts
│       │   ├── eventSlice.ts
│       │   └── authSlice.ts
│       └── types/
│           ├── agent.ts
│           ├── event.ts
│           └── policy.ts
│
├── agents/                     # Python Agents
│   ├── common/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── config.py
│   │   ├── communication.py
│   │   └── monitors/
│   │       ├── file_monitor.py
│   │       ├── clipboard_monitor.py
│   │       ├── usb_monitor.py
│   │       └── network_monitor.py
│   │
│   ├── windows/
│   │   ├── requirements.txt
│   │   ├── agent.py
│   │   ├── service.py
│   │   ├── install.ps1
│   │   ├── uninstall.ps1
│   │   ├── config.yml.template
│   │   └── README.md
│   │
│   └── linux/
│       ├── requirements.txt
│       ├── agent.py
│       ├── service.py
│       ├── install.sh
│       ├── uninstall.sh
│       ├── config.yml.template
│       └── README.md
│
├── config/
│   ├── manager.yml.example
│   └── policies/
│       ├── default.yml
│       ├── pci-dss.yml
│       ├── gdpr.yml
│       └── hipaa.yml
│
├── docs/
│   ├── installation/
│   │   ├── server.md
│   │   ├── windows-agent.md
│   │   └── linux-agent.md
│   ├── api/
│   │   └── api-reference.md
│   ├── user-guide/
│   │   ├── getting-started.md
│   │   ├── kql-guide.md
│   │   └── policy-creation.md
│   └── development/
│       ├── contributing.md
│       └── architecture.md
│
└── scripts/
    ├── init_db.py
    ├── generate_certs.sh
    └── deploy.sh
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
Coverage Target: 80%+
Framework: pytest
Location: manager/tests/unit/

Test Categories:
  - API endpoint tests
  - Service layer tests
  - Model validation tests
  - Utility function tests
  - KQL parser tests
```

### Integration Tests
```python
Framework: pytest with testcontainers
Location: manager/tests/integration/

Test Scenarios:
  - Database integration (PostgreSQL, OpenSearch)
  - Redis caching
  - Event processing pipeline
  - Policy engine execution
  - Agent communication
```

### End-to-End Tests
```typescript
Framework: Playwright / Cypress
Location: dashboard/tests/e2e/

Test Flows:
  - User login → Dashboard → View events
  - Agent registration → Event submission → Dashboard display
  - Policy creation → Event triggering → Alert generation
  - KQL search → Filtering → Export
```

---

## 📋 Phase 1 MVP - Implementation Checklist

### Week 1-2: Core Infrastructure
- [ ] Project structure setup
- [ ] Docker Compose configuration
- [ ] PostgreSQL schema + migrations
- [ ] OpenSearch index templates
- [ ] Redis configuration
- [ ] FastAPI base setup with auth
- [ ] Core API endpoints:
  - [ ] POST /v1/agents/register
  - [ ] POST /v1/agents/auth
  - [ ] GET /v1/agents
  - [ ] POST /v1/events
  - [ ] GET /v1/events
  - [ ] POST /v1/auth/login
  - [ ] GET /v1/system/health
- [ ] Basic event processor
- [ ] YAML config loader

### Week 3-4: Agents & Dashboard
- [ ] Python agent framework (common)
- [ ] Windows agent implementation
  - [ ] File monitor
  - [ ] Clipboard monitor
  - [ ] USB monitor
  - [ ] Auto-enrollment
  - [ ] Windows service setup
- [ ] Linux agent implementation
  - [ ] File monitor
  - [ ] Clipboard monitor
  - [ ] USB monitor
  - [ ] systemd service
- [ ] React dashboard base
  - [ ] Authentication flow
  - [ ] Agent list page
  - [ ] Event list page
  - [ ] Basic KQL search
  - [ ] Time range filters
- [ ] One-liner installation scripts

### Week 5-6: Polish & Testing
- [ ] Unit tests for all API endpoints
- [ ] Integration tests
- [ ] E2E tests
- [ ] Documentation
  - [ ] API documentation
  - [ ] Installation guides
  - [ ] User guides
  - [ ] KQL reference
- [ ] GitHub repository setup
- [ ] CI/CD pipeline (GitHub Actions)

---

## 🚀 Phase 2+ Features (Post-MVP)

### Extended API Endpoints
- [ ] All 70+ API endpoints
- [ ] ML-based classification
- [ ] Forensics capabilities
- [ ] Sandbox integration
- [ ] SIEM integrations
- [ ] Cloud connectors

### Advanced Dashboard
- [ ] Advanced visualizations
- [ ] Custom dashboards
- [ ] Report builder
- [ ] Real-time collaboration
- [ ] Mobile app

### Enterprise Features
- [ ] Multi-tenancy
- [ ] HA/clustering
- [ ] Advanced RBAC
- [ ] Compliance reports
- [ ] SLA management

---

## 📚 Documentation Standards

All documentation will be maintained in Markdown format with:
- Clear table of contents
- Code examples
- Screenshots/diagrams
- Version compatibility matrix
- Troubleshooting guides
- FAQ sections

---

## 🎯 Success Metrics

**MVP Success Criteria:**
- ✅ Agent auto-enrollment working
- ✅ Real-time event streaming functional
- ✅ KQL search operational
- ✅ Basic visualizations working
- ✅ One-liner agent installation
- ✅ 80%+ test coverage
- ✅ Complete documentation
- ✅ Deployable via Docker Compose

---

**Document Version:** 2.0
**Last Updated:** 2025-01-12
**Next Review:** Phase 1 Completion
