# CyberSentinel DLP - Master Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Installation & Deployment](#installation--deployment)
5. [Module Documentation](#module-documentation)
6. [Configuration](#configuration)
7. [Compliance & Security](#compliance--security)
8. [Wazuh SIEM Integration](#wazuh-siem-integration)
9. [Performance & Scalability](#performance--scalability)
10. [Monitoring & Alerting](#monitoring--alerting)
11. [Troubleshooting](#troubleshooting)
12. [API Reference](#api-reference)
13. [Best Practices](#best-practices)

---

## System Overview

CyberSentinel DLP is an enterprise-grade Data Loss Prevention platform designed to protect sensitive data across endpoints, networks, and cloud environments. The system provides real-time detection, classification, and enforcement capabilities to prevent data exfiltration and ensure regulatory compliance.

### Key Capabilities

- **Multi-Layer Protection**: Endpoint agents, network collectors, and cloud connectors
- **Advanced Detection**: Hybrid classification using deterministic and ML-based methods
- **Real-Time Enforcement**: Block, alert, quarantine, and redact sensitive data
- **Compliance Ready**: GDPR, HIPAA, PCI-DSS, SOX, PHI, PI support
- **Enterprise Scale**: Designed for high availability and horizontal scalability
- **Modern UI**: Beautiful Next.js dashboard accessible via host IP

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Detection Precision | ≥ 0.90 | - |
| Detection Recall | ≥ 0.85 | - |
| Mean Time to Detect | < 5 minutes | - |
| False Positive Rate | < 3% | - |
| Classification Latency | < 300ms | - |
| System Availability | 99.9% | - |

---

## Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Next.js Dashboard                        │
│            (React, TypeScript, Tailwind CSS)                  │
│          Accessible via Host IP (0.0.0.0:3000)               │
└────────────────────────┬─────────────────────────────────────┘
                         │ REST API + WebSocket
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Server                      │
│  - Authentication (JWT, OAuth2)                               │
│  - API Gateway & Rate Limiting                                │
│  - Business Logic & Orchestration                             │
└─┬────────────┬────────────┬────────────┬─────────────────────┘
  │            │            │            │
  ▼            ▼            ▼            ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐
│Endpoint │ │ Network  │ │  Cloud   │ │ Policy Engine  │
│ Agents  │ │Collectors│ │Connectors│ │ & Classifier   │
└─────────┘ └──────────┘ └──────────┘ └────────────────┘
     │            │            │              │
     └────────────┴────────────┴──────────────┘
                    │
                    ▼
     ┌──────────────────────────────────┐
     │      Hybrid Database Layer        │
     │  PostgreSQL      │    MongoDB     │
     │  (Structured)    │  (Logs/Events) │
     └──────────────┬───────────────────┘
                    │ Redis (Cache)
                    ▼
     ┌──────────────────────────────────┐
     │      Wazuh SIEM Integration       │
     │   (Alerts, Monitoring, SOC)       │
     └──────────────────────────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
├─────────────────────────────────────────────────────────────┤
│ • Dashboard (Next.js)                                        │
│ • Real-time Event Viewer                                     │
│ • Policy Management UI                                       │
│ • User Management                                            │
│ • Compliance Reporting                                       │
└─────────────────────────────────────────────────────────────┘
                         ↕ HTTPS/WSS
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
├─────────────────────────────────────────────────────────────┤
│ • FastAPI Server                                             │
│ • Authentication & Authorization                             │
│ • API Gateway                                                │
│ • Rate Limiting & Security Middleware                        │
└─────────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────────┐
│                        Business Layer                        │
├─────────────────────────────────────────────────────────────┤
│ • Policy Evaluation Engine                                   │
│ • ML-Based Classifier                                        │
│ • Event Processing Pipeline                                  │
│ • Enforcement Adapters                                       │
└─────────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────────┐
│                         Data Layer                           │
├─────────────────────────────────────────────────────────────┤
│ • PostgreSQL (Users, Policies, Metadata)                     │
│ • MongoDB (Events, Logs, Audit Trail)                        │
│ • Redis (Cache, Sessions, Rate Limiting)                     │
└─────────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────────┐
│                      Integration Layer                       │
├─────────────────────────────────────────────────────────────┤
│ • Wazuh SIEM (Alerts & Monitoring)                           │
│ • SMTP (Email Notifications)                                 │
│ • Cloud Providers (Office 365, AWS, GCP)                     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Event Generation**: Endpoint agents, network collectors, or cloud connectors detect data operations
2. **Event Ingestion**: Events sent to FastAPI server via REST API
3. **Preprocessing**: Content extraction, fingerprinting, entropy calculation
4. **Classification**: Hybrid detection (regex, fingerprints, ML models)
5. **Policy Evaluation**: Match against active policies
6. **Enforcement**: Execute actions (block, alert, quarantine)
7. **Storage**: Save to MongoDB (events) and PostgreSQL (metadata)
8. **SIEM Forwarding**: Send alerts to Wazuh
9. **Dashboard Update**: Real-time updates via WebSocket

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| API Framework | FastAPI | 0.104+ | High-performance async API |
| Language | Python | 3.11+ | Backend development |
| Database (SQL) | PostgreSQL | 15+ | Structured data storage |
| Database (NoSQL) | MongoDB | 7+ | Event logs and documents |
| Cache | Redis | 7+ | Caching and rate limiting |
| ORM | SQLAlchemy | 2.0+ | Database ORM |
| Authentication | JWT + OAuth2 | - | User authentication |
| Validation | Pydantic | 2.5+ | Data validation |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Next.js | 14+ | React framework |
| Language | TypeScript | 5.3+ | Type-safe development |
| UI Framework | Tailwind CSS | 3.3+ | Utility-first CSS |
| State Management | Zustand | 4.4+ | Client-side state |
| Data Fetching | React Query | 5.14+ | Server state management |
| Charts | Recharts | 2.10+ | Data visualization |
| Icons | Lucide React | 0.294+ | Icon library |

### Infrastructure

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Containerization | Docker | 24+ | Application containers |
| Orchestration | Docker Compose | 2.20+ | Multi-container management |
| Reverse Proxy | Nginx | 1.25+ | Load balancing |
| SIEM | Wazuh | 4.7+ | Security monitoring |

### Machine Learning

| Component | Technology | Purpose |
|-----------|-----------|---------|
| ML Framework | TensorFlow / PyTorch | Deep learning models |
| NLP | spaCy, transformers | Natural language processing |
| Data Processing | pandas, numpy | Data manipulation |
| Training | scikit-learn | Classical ML algorithms |

---

## Installation & Deployment

### Prerequisites

Before installation, ensure you have:

- **Operating System**: Linux (Ubuntu 22.04+ recommended), Windows 10+, or macOS
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Python**: 3.11+ (for local development)
- **Node.js**: 18+ (for dashboard development)
- **PostgreSQL**: 15+ (if not using Docker)
- **MongoDB**: 7+ (if not using Docker)
- **Redis**: 7+ (if not using Docker)
- **RAM**: Minimum 8GB, recommended 16GB+
- **Disk**: Minimum 50GB free space
- **Network**: Open ports 3000 (dashboard), 8000 (API), 5432 (PostgreSQL), 27017 (MongoDB), 6379 (Redis)

### Quick Start (Docker)

The fastest way to get started is using Docker Compose:

```bash
# 1. Clone the repository
git clone https://github.com/yourorg/cybersentinel-dlp.git
cd cybersentinel-dlp

# 2. Create environment file
cp config/env-templates/.env.server.example server/.env
cp dashboard/.env.local.example dashboard/.env.local

# 3. Update environment variables
# Edit server/.env and dashboard/.env.local with your configuration
# IMPORTANT: Set your host IP in dashboard/.env.local

# 4. Start all services
docker-compose up -d

# 5. Check service health
docker-compose ps

# 6. View logs
docker-compose logs -f

# 7. Access the dashboard
# Open browser: http://<your-host-ip>:3000
# Default credentials:
#   Email: admin@cybersentinel.local
#   Password: ChangeMe123!
```

### Production Deployment

For production deployments, follow these steps:

#### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

#### Step 2: Application Deployment

```bash
# Clone repository
git clone https://github.com/yourorg/cybersentinel-dlp.git
cd cybersentinel-dlp

# Set up environment
cp config/env-templates/.env.server.example server/.env

# Generate strong secrets
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
MONGODB_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)

# Update .env file with generated secrets
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" server/.env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" server/.env
sed -i "s/MONGODB_PASSWORD=.*/MONGODB_PASSWORD=$MONGODB_PASSWORD/" server/.env
sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" server/.env

# Set HOST_IP for dashboard access
HOST_IP=$(hostname -I | awk '{print $1}')
echo "HOST_IP=$HOST_IP" >> .env

# Update dashboard configuration
echo "NEXT_PUBLIC_API_URL=http://$HOST_IP:8000/api/v1" > dashboard/.env.local

# Build and start services
docker-compose up -d --build

# Wait for services to be healthy
sleep 30

# Check service status
docker-compose ps
```

#### Step 3: Database Initialization

```bash
# Run PostgreSQL migrations
docker-compose exec server alembic upgrade head

# Create MongoDB indexes
docker-compose exec server python scripts/init_mongodb.py

# Create admin user
docker-compose exec server python scripts/create_admin.py
```

#### Step 4: Verification

```bash
# Check API health
curl http://localhost:8000/health

# Check dashboard
curl http://localhost:3000

# View logs
docker-compose logs -f server
docker-compose logs -f dashboard
```

### Manual Installation (Without Docker)

If you prefer to install without Docker:

#### Backend Setup

```bash
cd server

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../config/env-templates/.env.server.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Dashboard Setup

```bash
cd dashboard

# Install dependencies
npm install

# Set up environment
cp .env.local.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev

# Or build for production
npm run build
npm start
```

### Accessing the Dashboard

After deployment, access the dashboard:

1. **Local Access**: `http://localhost:3000`
2. **Network Access**: `http://<your-host-ip>:3000`
3. **Production**: Configure Nginx reverse proxy for HTTPS

**Default Credentials**:
- Email: `admin@cybersentinel.local`
- Password: `ChangeMe123!`

**IMPORTANT**: Change the default password immediately after first login!

---

## Module Documentation

### 1. FastAPI Backend Server

**Location**: `server/`

The FastAPI server is the core of the DLP platform, providing:

- RESTful API endpoints
- Authentication and authorization
- Business logic orchestration
- Database management
- Real-time WebSocket connections

**Key Files**:
- `app/main.py`: Application entry point
- `app/core/config.py`: Configuration management
- `app/core/security.py`: Authentication and security
- `app/core/database.py`: Database connections
- `app/api/v1/`: API endpoints

**Starting the Server**:
```bash
cd server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**API Documentation**:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

For detailed documentation, see [docs/modules/SERVER.md](docs/modules/SERVER.md)

### 2. Hybrid Database Layer

**PostgreSQL** (Structured Data):
- Users and authentication
- Policies and rules
- System configuration
- Metadata

**MongoDB** (Events and Logs):
- DLP events
- Audit logs
- Classification results
- Historical data

**Redis** (Cache):
- Session storage
- Rate limiting counters
- Policy cache
- Temporary data

For detailed documentation, see [docs/modules/DATABASE.md](docs/modules/DATABASE.md)

### 3. Next.js Dashboard

**Location**: `dashboard/`

Beautiful, modern web interface for:
- Real-time event monitoring
- Policy management
- User administration
- Compliance reporting
- System configuration

**Features**:
- Accessible via host IP (0.0.0.0)
- Real-time updates
- Responsive design
- Role-based access control
- Interactive charts and graphs

**Starting the Dashboard**:
```bash
cd dashboard
npm run dev  # Development
npm run build && npm start  # Production
```

For detailed documentation, see [docs/modules/DASHBOARD.md](docs/modules/DASHBOARD.md)

### 4. Endpoint Agents

**Location**: `agents/endpoint/`

Cross-platform agents for Windows, Linux, and macOS:

- File system monitoring
- Clipboard interception
- Network activity tracking
- Local policy enforcement
- Offline queuing

For detailed documentation, see [docs/modules/AGENTS.md](docs/modules/AGENTS.md)

### 5. Network Collectors

**Location**: `collectors/network/`

Network traffic analysis:

- Inline proxy or TAP deployment
- TLS interception
- Protocol parsing (HTTP, SMTP, FTP)
- Deep packet inspection
- Session tracking

For detailed documentation, see [docs/modules/COLLECTORS.md](docs/modules/COLLECTORS.md)

### 6. Cloud Connectors

**Location**: `connectors/`

Cloud service integrations:

- Office 365 / Microsoft 365
- Google Workspace
- AWS S3
- Box
- Dropbox

For detailed documentation, see [docs/modules/CONNECTORS.md](docs/modules/CONNECTORS.md)

### 7. ML-Based Classifiers

**Location**: `ml/`

Machine learning pipeline:

- Training pipeline
- Model registry
- Inference service
- Drift detection
- Model monitoring

For detailed documentation, see [docs/modules/ML.md](docs/modules/ML.md)

### 8. Policy Engine

**Location**: `policy-engine/`

Rule evaluation and enforcement:

- YAML-based policy DSL
- Complex condition evaluation
- Stateful rule processing
- Policy versioning
- A/B testing

For detailed documentation, see [docs/modules/POLICY_ENGINE.md](docs/modules/POLICY_ENGINE.md)

### 9. Wazuh SIEM Integration

**Location**: `integrations/wazuh/`

Security monitoring integration:

- Custom decoders
- Alert rules
- Event forwarding
- Compliance reporting

For detailed documentation, see [docs/modules/WAZUH.md](docs/modules/WAZUH.md)

---

## Configuration

### Environment Variables

#### Server Configuration

```bash
# Application
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<generate-strong-secret>
HOST=0.0.0.0
PORT=8000

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=dlp_user
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=cybersentinel_dlp

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=dlp_user
MONGODB_PASSWORD=<secure-password>
MONGODB_DB=cybersentinel_dlp

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=<secure-password>

# Security
CORS_ORIGINS=http://localhost:3000,http://<your-host-ip>:3000
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Wazuh
WAZUH_HOST=localhost
WAZUH_PORT=1514
WAZUH_PROTOCOL=udp
```

#### Dashboard Configuration

```bash
# API
NEXT_PUBLIC_API_URL=http://<your-host-ip>:8000/api/v1

# Application
NEXT_PUBLIC_APP_NAME=CyberSentinel DLP
NEXT_PUBLIC_APP_VERSION=1.0.0

# Features
NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES=true
NEXT_PUBLIC_DASHBOARD_REFRESH_INTERVAL=30000
```

### Generating Secrets

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate passwords
openssl rand -hex 16
```

---

## Compliance & Security

### Supported Regulations

#### GDPR (General Data Protection Regulation)

- **Article 5**: Data minimization and purpose limitation
- **Article 32**: Security of processing
- **Article 33**: Breach notification
- **Article 35**: Data protection impact assessment

**Implementation**:
- Personal data identification and classification
- Automated data subject rights (access, deletion)
- Audit logging and data lineage
- Breach detection and notification

#### HIPAA (Health Insurance Portability and Accountability Act)

- **Security Rule**: Administrative, physical, and technical safeguards
- **Privacy Rule**: Protected Health Information (PHI) protection
- **Breach Notification Rule**: Notification requirements

**Implementation**:
- PHI classification (18 identifiers)
- Access controls and audit trails
- Encryption at rest and in transit
- Breach detection and reporting

#### PCI-DSS (Payment Card Industry Data Security Standard)

- **Requirement 3**: Protect stored cardholder data
- **Requirement 4**: Encrypt transmission of cardholder data
- **Requirement 10**: Track and monitor all access to network resources

**Implementation**:
- PAN (Primary Account Number) detection
- Luhn algorithm validation
- Card data masking and tokenization
- Comprehensive audit logging

#### SOX (Sarbanes-Oxley Act)

- **Section 302**: Corporate responsibility for financial reports
- **Section 404**: Management assessment of internal controls
- **Section 802**: Criminal penalties for document destruction

**Implementation**:
- Financial data classification
- Immutable audit logs
- Access control and segregation of duties
- Change management tracking

### Security Features

#### Authentication & Authorization

- JWT-based authentication
- OAuth2 / OIDC support
- Role-based access control (RBAC)
- Multi-factor authentication (MFA) ready
- Session management with Redis

#### Encryption

- **At Rest**: AES-256 encryption for databases
- **In Transit**: TLS 1.3 for all communications
- **Key Management**: HashiCorp Vault integration
- **Field-Level**: Sensitive data encryption in database

#### Audit Logging

- Immutable audit trail in MongoDB
- All user actions logged
- Timestamp and user attribution
- Tamper-evident seals
- WORM (Write Once Read Many) storage option

#### Security Hardening

- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF tokens
- Rate limiting and DDoS protection
- Security headers (HSTS, CSP, etc.)

---

## Wazuh SIEM Integration

### Overview

CyberSentinel DLP integrates with Wazuh SIEM for centralized security monitoring, alerting, and compliance reporting.

### Integration Architecture

```
CyberSentinel DLP
       │
       ├─> Event Processing
       │
       ├─> Policy Violation Detection
       │
       ├─> Event Formatting (JSON)
       │
       ▼
Wazuh Agent/Forwarder
       │
       ├─> UDP/TCP Socket (Port 1514)
       │
       ▼
Wazuh Manager
       │
       ├─> Custom Decoders
       │
       ├─> Custom Rules
       │
       ├─> Alert Generation
       │
       ▼
Wazuh Dashboard / API
       │
       ├─> SOC Monitoring
       │
       ├─> Compliance Reports
       │
       └─> Incident Response
```

### Custom Decoders

**Location**: `integrations/wazuh/decoders/dlp.xml`

```xml
<decoder name="dlp-event">
  <prematch>"source":"endpoint|network|cloud"</prematch>
</decoder>

<decoder name="dlp-event-child">
  <parent>dlp-event</parent>
  <regex offset="after_parent">"classification":{"score":(\.\d+),"labels":\["(\w+)"</regex>
  <order>dlp.score,dlp.label</order>
</decoder>
```

### Custom Rules

**Location**: `integrations/wazuh/rules/dlp.xml`

```xml
<!-- High-confidence data exfiltration blocked -->
<rule id="100100" level="12">
  <decoded_as>dlp-event</decoded_as>
  <field name="dlp.score">\.9|1\.0</field>
  <field name="policy.action">block</field>
  <description>DLP: High-confidence data exfiltration blocked</description>
  <mitre>
    <id>T1048</id>
  </mitre>
</rule>

<!-- PCI-DSS credit card detection -->
<rule id="100101" level="10">
  <decoded_as>dlp-event</decoded_as>
  <field name="dlp.label">PAN</field>
  <description>DLP: Credit card data detected</description>
  <group>pci_dss_3.4,</group>
</rule>

<!-- GDPR PII detection -->
<rule id="100102" level="8">
  <decoded_as>dlp-event</decoded_as>
  <field name="dlp.label">PII</field>
  <description>DLP: Personal identifiable information detected</description>
  <group>gdpr_IV_32,</group>
</rule>

<!-- HIPAA PHI detection -->
<rule id="100103" level="10">
  <decoded_as>dlp-event</decoded_as>
  <field name="dlp.label">PHI</field>
  <description>DLP: Protected health information detected</description>
  <group>hipaa_164.312.a.1,</group>
</rule>
```

### Event Forwarding

Events are forwarded to Wazuh in JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "event_id": "evt-12345",
  "source": "endpoint",
  "user": "john.doe@company.com",
  "classification": {
    "score": 0.92,
    "labels": ["PAN", "HIGH_ENTROPY"],
    "method": "regex+ml"
  },
  "policy": {
    "id": "pol-001",
    "action": "block",
    "severity": "critical"
  },
  "context": {
    "file_path": "/home/user/export.csv",
    "destination": "external-server.com",
    "protocol": "https"
  }
}
```

### Wazuh Dashboard Integration

1. **Import Custom Decoders**:
```bash
sudo cp integrations/wazuh/decoders/dlp.xml /var/ossec/etc/decoders/
```

2. **Import Custom Rules**:
```bash
sudo cp integrations/wazuh/rules/dlp.xml /var/ossec/etc/rules/
```

3. **Restart Wazuh**:
```bash
sudo systemctl restart wazuh-manager
```

4. **Configure Agent** (on DLP server):
```bash
/var/ossec/bin/agent-auth -m <wazuh-manager-ip>
sudo systemctl start wazuh-agent
```

### Compliance Reporting

Wazuh provides built-in compliance reports for:

- **PCI-DSS**: Sections 1-12
- **GDPR**: Articles 5, 32, 33, 35
- **HIPAA**: Security and Privacy Rules
- **NIST 800-53**: All control families
- **SOX**: Sections 302, 404, 802

Access reports via Wazuh Dashboard:
- Navigate to **Modules** > **Security Events**
- Select **Compliance** tab
- Choose regulation and time period

---

## Performance & Scalability

### System Requirements

#### Minimum Requirements

| Component | Specification |
|-----------|--------------|
| CPU | 4 cores |
| RAM | 8 GB |
| Storage | 100 GB SSD |
| Network | 1 Gbps |

#### Recommended for Production

| Component | Specification |
|-----------|--------------|
| CPU | 16+ cores |
| RAM | 32+ GB |
| Storage | 500+ GB NVMe SSD |
| Network | 10 Gbps |

### Scaling Strategies

#### Horizontal Scaling

1. **FastAPI Server**: Run multiple instances behind load balancer
2. **Database**: PostgreSQL replication, MongoDB sharding
3. **Redis**: Redis Cluster for distributed caching
4. **Kubernetes**: Deploy on K8s for auto-scaling

#### Vertical Scaling

1. **Increase Server Resources**: More CPU, RAM, faster storage
2. **Database Tuning**: Optimize queries, add indexes
3. **Connection Pooling**: Increase pool sizes
4. **Worker Processes**: Increase Uvicorn workers

### Performance Tuning

#### FastAPI Server

```python
# Increase worker processes
uvicorn app.main:app --workers 8 --worker-class uvicorn.workers.UvicornWorker

# Configure connection pools
POSTGRES_POOL_SIZE=50
POSTGRES_MAX_OVERFLOW=20
MONGODB_MAX_POOL_SIZE=200
REDIS_POOL_SIZE=20
```

#### PostgreSQL

```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '4GB';

-- Increase work memory
ALTER SYSTEM SET work_mem = '256MB';

-- Enable parallel queries
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;

-- Reload configuration
SELECT pg_reload_conf();
```

#### MongoDB

```javascript
// Create indexes for frequent queries
db.dlp_events.createIndex({ "timestamp": -1 });
db.dlp_events.createIndex({ "user_email": 1 });
db.dlp_events.createIndex({ "classification.labels": 1 });
db.dlp_events.createIndex({ "blocked": 1 });

// Enable sharding for large collections
sh.enableSharding("cybersentinel_dlp");
sh.shardCollection("cybersentinel_dlp.dlp_events", { "timestamp": 1 });
```

#### Redis

```bash
# Increase max memory
redis-cli CONFIG SET maxmemory 4gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Persistence configuration
redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### Load Balancing

#### Nginx Configuration

```nginx
upstream fastapi_backend {
    least_conn;
    server 192.168.1.10:8000 weight=5;
    server 192.168.1.11:8000 weight=5;
    server 192.168.1.12:8000 weight=5;
    keepalive 32;
}

server {
    listen 80;
    server_name dlp.company.com;

    location / {
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Caching Strategy

1. **Policy Cache**: Cache active policies in Redis (TTL: 5 minutes)
2. **User Sessions**: Store in Redis with automatic expiration
3. **API Responses**: Cache non-sensitive GET requests
4. **ML Models**: Keep loaded models in memory
5. **Fingerprints**: Use Bloom filters for efficient lookups

---

## Monitoring & Alerting

### Health Checks

#### API Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "CyberSentinel DLP",
  "version": "1.0.0"
}
```

#### Readiness Check

```bash
curl http://localhost:8000/ready
```

#### Metrics Endpoint

Prometheus metrics available at:
```bash
curl http://localhost:8000/metrics
```

### Logging

#### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about system operation
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical issues requiring immediate attention

#### Log Format

Structured JSON logging:

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "service": "CyberSentinel DLP",
  "environment": "production",
  "version": "1.0.0",
  "request_id": "req-abc123",
  "message": "Event processed successfully",
  "event_id": "evt-12345",
  "user": "john.doe@company.com"
}
```

#### Log Locations

- **Server Logs**: `server/logs/app.log`
- **Access Logs**: `server/logs/access.log`
- **Error Logs**: `server/logs/error.log`
- **Docker Logs**: `docker-compose logs -f <service>`

### Monitoring Stack

#### Prometheus + Grafana

1. **Install Prometheus**:
```bash
docker run -d -p 9090:9090 \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

2. **Prometheus Configuration** (`prometheus.yml`):
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cybersentinel-dlp'
    static_configs:
      - targets: ['localhost:8000']
```

3. **Install Grafana**:
```bash
docker run -d -p 3001:3000 grafana/grafana
```

4. **Add Prometheus Data Source** in Grafana
5. **Import Dashboard**: Use dashboard ID 1860 for basic metrics

### Alerting Rules

#### Critical Alerts

1. **High False Positive Rate**:
   - Condition: FPR > 5%
   - Action: Email to security team

2. **Service Down**:
   - Condition: Health check fails 3 consecutive times
   - Action: PagerDuty alert

3. **Database Connection Lost**:
   - Condition: Connection pool exhausted
   - Action: Auto-restart service, alert ops team

4. **High CPU/Memory Usage**:
   - Condition: Usage > 90% for 5 minutes
   - Action: Alert ops team, trigger auto-scaling

#### Warning Alerts

1. **Increased Event Volume**:
   - Condition: 50% increase in hourly events
   - Action: Email to security team

2. **Slow Response Times**:
   - Condition: API latency > 1 second
   - Action: Log warning, investigate

3. **Cache Miss Rate High**:
   - Condition: Cache miss > 30%
   - Action: Review caching strategy

---

## Troubleshooting

### Common Issues

#### 1. Server Won't Start

**Symptom**: FastAPI server fails to start

**Possible Causes**:
- Database connection failure
- Port already in use
- Missing environment variables

**Solutions**:
```bash
# Check if port is in use
lsof -i :8000

# Verify database connectivity
docker-compose ps
docker-compose logs postgres
docker-compose logs mongodb

# Check environment variables
cat server/.env

# View detailed error logs
docker-compose logs server
```

#### 2. Dashboard Can't Connect to API

**Symptom**: Dashboard shows connection errors

**Possible Causes**:
- Incorrect API URL
- CORS configuration
- API server not running

**Solutions**:
```bash
# Verify API is running
curl http://localhost:8000/health

# Check dashboard environment
cat dashboard/.env.local

# Verify CORS settings in server/.env
grep CORS_ORIGINS server/.env

# Update CORS to include your IP
CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:3000
```

#### 3. Authentication Fails

**Symptom**: Login returns 401 error

**Possible Causes**:
- Incorrect credentials
- JWT secret mismatch
- Token expiration

**Solutions**:
```bash
# Use default credentials
Email: admin@cybersentinel.local
Password: ChangeMe123!

# Check JWT secret key
grep SECRET_KEY server/.env

# Clear browser cache and cookies
# Try incognito mode
```

#### 4. Events Not Appearing in Dashboard

**Symptom**: Dashboard shows no events

**Possible Causes**:
- No agents running
- MongoDB connection issue
- Events not being generated

**Solutions**:
```bash
# Check MongoDB connection
docker-compose exec mongodb mongosh -u dlp_user -p

# Check if events exist
docker-compose exec mongodb mongosh -u dlp_user -p
use cybersentinel_dlp
db.dlp_events.count()
db.dlp_events.find().limit(5)

# Generate test event via API
curl -X POST http://localhost:8000/api/v1/events \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"type": "test", "user": "test@example.com"}'
```

#### 5. High CPU Usage

**Symptom**: Server consuming excessive CPU

**Possible Causes**:
- Too many concurrent requests
- Inefficient queries
- Memory leak

**Solutions**:
```bash
# Check container stats
docker stats

# Review slow queries
docker-compose logs server | grep "slow query"

# Scale up workers
docker-compose up -d --scale server=3

# Check for memory leaks
docker-compose exec server top
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# In server/.env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart server
docker-compose restart server

# View debug logs
docker-compose logs -f server
```

### Database Troubleshooting

#### PostgreSQL

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U dlp_user -d cybersentinel_dlp

# Check connections
SELECT count(*) FROM pg_stat_activity;

# View slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

# Check table sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname='public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### MongoDB

```bash
# Connect to MongoDB
docker-compose exec mongodb mongosh -u dlp_user -p

# Check database size
use cybersentinel_dlp
db.stats()

# View collection sizes
db.dlp_events.stats()

# Check indexes
db.dlp_events.getIndexes()

# Rebuild indexes if slow
db.dlp_events.reIndex()
```

#### Redis

```bash
# Connect to Redis
docker-compose exec redis redis-cli -a <password>

# Check memory usage
INFO memory

# Check connected clients
CLIENT LIST

# Clear cache if needed
FLUSHDB

# Monitor commands
MONITOR
```

### Getting Help

1. **Check Logs**: Always start by checking logs for error messages
2. **Documentation**: Review module-specific documentation
3. **GitHub Issues**: Search for similar issues
4. **Support**: Contact support@cybersentinel.local
5. **Community**: Join our Slack channel

---

## API Reference

### Authentication

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@cybersentinel.local&password=ChangeMe123!
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json
Authorization: Bearer <refresh_token>

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Events API

#### Get Events

```http
GET /api/v1/events?skip=0&limit=100&severity=critical
Authorization: Bearer <access_token>
```

Response:
```json
[
  {
    "id": "evt-12345",
    "timestamp": "2024-01-15T10:30:45Z",
    "event_type": "file_transfer",
    "source": "endpoint",
    "user_email": "john.doe@company.com",
    "classification_score": 0.92,
    "classification_labels": ["PAN", "HIGH_ENTROPY"],
    "policy_id": "pol-001",
    "action_taken": "block",
    "severity": "critical",
    "blocked": true
  }
]
```

#### Get Event Stats

```http
GET /api/v1/events/stats/summary
Authorization: Bearer <access_token>
```

### Policies API

#### Get Policies

```http
GET /api/v1/policies
Authorization: Bearer <access_token>
```

#### Create Policy

```http
POST /api/v1/policies
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Block Credit Card Exfiltration",
  "description": "Prevent credit card numbers from being sent externally",
  "enabled": true,
  "priority": 100,
  "conditions": [
    {
      "field": "classification.labels",
      "operator": "contains",
      "value": "PAN"
    }
  ],
  "actions": [
    {
      "type": "block"
    }
  ],
  "compliance_tags": ["PCI-DSS"]
}
```

### Dashboard API

#### Get Dashboard Overview

```http
GET /api/v1/dashboard/overview
Authorization: Bearer <access_token>
```

#### Get Event Timeline

```http
GET /api/v1/dashboard/timeline?hours=24
Authorization: Bearer <access_token>
```

For complete API documentation, visit:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

---

## Best Practices

### Security

1. **Change Default Credentials**: Immediately after installation
2. **Use Strong Passwords**: Minimum 16 characters, mixed case, numbers, symbols
3. **Enable HTTPS**: Use TLS certificates in production
4. **Regular Updates**: Keep all components up to date
5. **Principle of Least Privilege**: Grant minimum necessary permissions
6. **Monitor Logs**: Regularly review audit logs
7. **Backup Data**: Regular automated backups
8. **Incident Response Plan**: Have a documented response plan

### Performance

1. **Database Indexes**: Create indexes for frequent queries
2. **Connection Pooling**: Configure appropriate pool sizes
3. **Caching**: Use Redis for frequently accessed data
4. **Load Balancing**: Distribute traffic across multiple servers
5. **Monitoring**: Set up alerting for performance degradation
6. **Regular Maintenance**: Vacuum databases, clear old logs

### Operational

1. **Documentation**: Keep configuration documented
2. **Version Control**: Track all configuration changes
3. **Testing**: Test in staging before production
4. **Rollback Plan**: Have rollback procedures ready
5. **Maintenance Windows**: Schedule regular maintenance
6. **Disaster Recovery**: Test recovery procedures regularly

### Compliance

1. **Policy Reviews**: Quarterly policy effectiveness reviews
2. **Audit Logs**: Retain logs per regulatory requirements
3. **Access Reviews**: Regular user access audits
4. **Compliance Reports**: Generate and review regularly
5. **Training**: Regular security awareness training
6. **Incident Documentation**: Document all security incidents

---

## Appendix

### Glossary

- **DLP**: Data Loss Prevention
- **PII**: Personally Identifiable Information
- **PHI**: Protected Health Information
- **PAN**: Primary Account Number (credit card)
- **SIEM**: Security Information and Event Management
- **RBAC**: Role-Based Access Control
- **JWT**: JSON Web Token
- **TLS**: Transport Layer Security
- **mTLS**: Mutual Transport Layer Security
- **GDPR**: General Data Protection Regulation
- **HIPAA**: Health Insurance Portability and Accountability Act
- **PCI-DSS**: Payment Card Industry Data Security Standard
- **SOX**: Sarbanes-Oxley Act

### References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Wazuh Documentation](https://documentation.wazuh.com/)
- [GDPR Official Text](https://gdpr-info.eu/)
- [HIPAA Official Guidance](https://www.hhs.gov/hipaa/)
- [PCI-DSS Standards](https://www.pcisecuritystandards.org/)

### Change Log

#### Version 1.0.0 (2024-01-15)
- Initial release
- FastAPI backend server
- Next.js dashboard
- PostgreSQL + MongoDB hybrid database
- Wazuh SIEM integration
- Docker deployment support
- Comprehensive documentation

### Support

For technical support, please contact:

- **Email**: support@cybersentinel.local
- **Documentation**: https://docs.cybersentinel.local
- **GitHub Issues**: https://github.com/yourorg/cybersentinel-dlp/issues
- **Community Forum**: https://community.cybersentinel.local

---

**Last Updated**: January 2024
**Version**: 1.0.0
**Maintained By**: CyberSentinel Security Team
