# CyberSentinel DLP - Deployment Guide

Complete guide for deploying CyberSentinel DLP in production environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Agent Deployment](#agent-deployment)
6. [Configuration](#configuration)
7. [Security Hardening](#security-hardening)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

**Manager Server:**
- CPU: 4 cores minimum, 8 cores recommended
- RAM: 8GB minimum, 16GB recommended
- Disk: 100GB minimum, 500GB+ for production
- Network: 1Gbps

**Per 100 Agents:**
- +2 CPU cores
- +4GB RAM
- +50GB disk

### Software Requirements

- **OS**: Ubuntu 22.04 LTS, RHEL 8+, or Debian 11+
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Python**: 3.8+ (for agents)
- **Node.js**: 18+ (for dashboard build)

### Network Requirements

**Inbound:**
- Port 55000 (Manager API)
- Port 3000 (Dashboard)
- Port 9200 (OpenSearch - internal only)
- Port 27017 (MongoDB - internal only)
- Port 5432 (PostgreSQL - internal only)
- Port 6379 (Redis - internal only)

**Outbound:**
- Port 443 (HTTPS for updates)
- Port 80 (HTTP for package downloads)

---

## Docker Compose Deployment

### 1. Prepare Environment

```bash
# Create directory
mkdir -p /opt/cybersentinel
cd /opt/cybersentinel

# Clone repository
git clone https://github.com/YOUR_ORG/cybersentinel-dlp.git .

# Create data directories
mkdir -p data/{opensearch,mongodb,postgres,redis}
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

**Required settings:**
```bash
# Manager Configuration
PORT=55000
WORKERS=4
VERSION=2.0.0

# Database Passwords (CHANGE THESE!)
OPENSEARCH_PASSWORD=<strong-password>
MONGODB_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET=<random-secret>

# Manager URL (your server IP/domain)
MANAGER_URL=https://your-server.com:55000
```

### 3. Create Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  opensearch:
    image: opensearchproject/opensearch:2.11.0
    container_name: cybersentinel-opensearch
    environment:
      - cluster.name=cybersentinel-cluster
      - node.name=opensearch-node1
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g"
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=${OPENSEARCH_PASSWORD}
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - ./data/opensearch:/usr/share/opensearch/data
    networks:
      - cybersentinel
    restart: unless-stopped

  mongodb:
    image: mongo:7.0
    container_name: cybersentinel-mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_PASSWORD}
    volumes:
      - ./data/mongodb:/data/db
    networks:
      - cybersentinel
    restart: unless-stopped

  postgres:
    image: postgres:16
    container_name: cybersentinel-postgres
    environment:
      POSTGRES_USER: cybersentinel
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: cybersentinel
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    networks:
      - cybersentinel
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: cybersentinel-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - ./data/redis:/data
    networks:
      - cybersentinel
    restart: unless-stopped

  manager:
    build:
      context: ./server
      dockerfile: Dockerfile
    container_name: cybersentinel-manager
    ports:
      - "55000:55000"
    environment:
      - PORT=55000
      - OPENSEARCH_HOST=opensearch
      - OPENSEARCH_PASSWORD=${OPENSEARCH_PASSWORD}
      - MONGODB_HOST=mongodb
      - MONGODB_PASSWORD=${MONGODB_PASSWORD}
      - POSTGRES_HOST=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - ./config:/etc/cybersentinel
      - ./logs:/var/log/cybersentinel
    depends_on:
      - opensearch
      - mongodb
      - postgres
      - redis
    networks:
      - cybersentinel
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:55000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    container_name: cybersentinel-dashboard
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://manager:55000
    depends_on:
      - manager
    networks:
      - cybersentinel
    restart: unless-stopped

networks:
  cybersentinel:
    driver: bridge

volumes:
  opensearch_data:
  mongodb_data:
  postgres_data:
  redis_data:
```

### 4. Deploy

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f manager

# Verify health
curl http://localhost:55000/health
```

### 5. Initialize Database

```bash
# Create initial admin user
docker exec -it cybersentinel-manager python -m app.init_admin

# Or manually
docker exec -it cybersentinel-manager python
>>> from app.services.user_service import create_admin_user
>>> create_admin_user("admin@example.com", "secure-password")
```

---

## Manual Deployment

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3.8 python3-pip python3-venv nginx certbot
```

**RHEL/CentOS:**
```bash
sudo yum install -y python38 python3-pip nginx certbot
```

### 2. Install OpenSearch

```bash
# Import GPG key
wget -qO - https://artifacts.opensearch.org/publickeys/opensearch.pgp | sudo apt-key add -

# Add repository
echo "deb https://artifacts.opensearch.org/releases/bundle/opensearch/2.x/apt stable main" | \
  sudo tee /etc/apt/sources.list.d/opensearch-2.x.list

# Install
sudo apt update
sudo apt install -y opensearch

# Configure
sudo nano /etc/opensearch/opensearch.yml

# Start
sudo systemctl enable opensearch
sudo systemctl start opensearch
```

### 3. Install MongoDB

```bash
# Import MongoDB GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install
sudo apt update
sudo apt install -y mongodb-org

# Start
sudo systemctl enable mongod
sudo systemctl start mongod
```

### 4. Install PostgreSQL & Redis

```bash
sudo apt install -y postgresql-14 redis-server

sudo systemctl enable postgresql redis-server
sudo systemctl start postgresql redis-server
```

### 5. Deploy Manager

```bash
# Create user
sudo useradd -r -s /bin/bash -d /opt/cybersentinel cybersentinel

# Clone and setup
sudo mkdir -p /opt/cybersentinel
cd /opt/cybersentinel
sudo git clone https://github.com/YOUR_ORG/cybersentinel-dlp.git .
sudo chown -R cybersentinel:cybersentinel /opt/cybersentinel

# Create virtual environment
sudo -u cybersentinel python3 -m venv venv
sudo -u cybersentinel ./venv/bin/pip install -r server/requirements.txt

# Configure
sudo cp config/manager.yml.example /etc/cybersentinel/manager.yml
sudo nano /etc/cybersentinel/manager.yml

# Create systemd service
sudo nano /etc/systemd/system/cybersentinel-manager.service
```

**systemd service file:**
```ini
[Unit]
Description=CyberSentinel DLP Manager
After=network.target opensearch.service mongodb.service

[Service]
Type=simple
User=cybersentinel
WorkingDirectory=/opt/cybersentinel/server
Environment="PATH=/opt/cybersentinel/venv/bin"
ExecStart=/opt/cybersentinel/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 55000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable cybersentinel-manager
sudo systemctl start cybersentinel-manager
```

### 6. Deploy Dashboard

```bash
# Build dashboard
cd /opt/cybersentinel/dashboard
sudo -u cybersentinel npm install
sudo -u cybersentinel npm run build

# Configure Nginx
sudo nano /etc/nginx/sites-available/cybersentinel
```

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name your-server.com;

    # Dashboard
    location / {
        root /opt/cybersentinel/dashboard/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:55000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cybersentinel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Configure SSL/TLS

```bash
# Get Let's Encrypt certificate
sudo certbot --nginx -d your-server.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## Agent Deployment

### Mass Deployment

**Windows (GPO/SCCM):**
```powershell
# Create deployment script
$script = @'
$ManagerUrl = "https://your-server.com:55000"
iwr -useb https://your-server.com/agents/windows/install.ps1 | iex -ManagerUrl $ManagerUrl
'@

# Deploy via GPO startup script or SCCM
```

**Linux (Ansible):**
```yaml
# playbook.yml
- hosts: all
  become: yes
  tasks:
    - name: Install CyberSentinel Agent
      shell: |
        curl -fsSL https://your-server.com/agents/linux/install.sh | \
        bash -s -- --manager-url https://your-server.com:55000
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 55000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# Firewalld (RHEL)
sudo firewall-cmd --permanent --add-port=55000/tcp
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

### 2. TLS/SSL

- Use Let's Encrypt for public domains
- Use internal CA for private networks
- Enable TLS for all database connections
- Set `verify_certs: true` in OpenSearch config

### 3. Access Control

- Implement IP whitelisting for admin APIs
- Use strong JWT secrets (32+ characters)
- Enable rate limiting
- Configure CORS properly

### 4. Database Security

```bash
# MongoDB
mongo admin
> use admin
> db.createUser({user: "cybersentinel", pwd: "strong-password", roles: [{role: "readWrite", db: "cybersentinel"}]})

# PostgreSQL
sudo -u postgres psql
postgres=# ALTER USER cybersentinel WITH PASSWORD 'strong-password';

# Redis
sudo nano /etc/redis/redis.conf
# requirepass strong-password
```

---

## Monitoring & Maintenance

### Health Monitoring

```bash
# Check service status
systemctl status cybersentinel-manager

# Check logs
journalctl -u cybersentinel-manager -f

# Check OpenSearch health
curl -k -u admin:password https://localhost:9200/_cluster/health?pretty

# Check disk space
df -h
```

### Backup Strategy

```bash
# Backup script
#!/bin/bash
BACKUP_DIR=/backup/cybersentinel/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --out $BACKUP_DIR/mongodb

# Backup PostgreSQL
pg_dump cybersentinel > $BACKUP_DIR/postgres.sql

# Backup configuration
cp -r /etc/cybersentinel $BACKUP_DIR/config

# Backup OpenSearch snapshots (configure repository first)
curl -X PUT "localhost:9200/_snapshot/backup/$(date +%Y%m%d)" -H 'Content-Type: application/json' -d'
{
  "indices": "cybersentinel-*"
}'
```

### Log Rotation

```bash
# /etc/logrotate.d/cybersentinel
/var/log/cybersentinel/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 cybersentinel cybersentinel
    sharedscripts
    postrotate
        systemctl reload cybersentinel-manager
    endscript
}
```

---

## Troubleshooting

### Manager Won't Start

```bash
# Check logs
journalctl -u cybersentinel-manager -n 100

# Common issues:
# 1. Database connection failed
systemctl status opensearch mongodb postgres

# 2. Port already in use
sudo lsof -i :55000

# 3. Permission issues
sudo chown -R cybersentinel:cybersentinel /opt/cybersentinel
```

### Agents Not Connecting

```bash
# Check connectivity
curl -k https://your-server.com:55000/health

# Check agent logs
# Windows: C:\ProgramData\CyberSentinel\agent.log
# Linux: /etc/cybersentinel/logs/agent.log

# Common issues:
# 1. Firewall blocking port 55000
# 2. SSL certificate issues (use --insecure for testing)
# 3. Manager URL incorrect in agent config
```

### OpenSearch Issues

```bash
# Check cluster health
curl -k -u admin:password https://localhost:9200/_cluster/health?pretty

# Check indices
curl -k -u admin:password https://localhost:9200/_cat/indices?v

# Increase heap size if needed
sudo nano /etc/opensearch/jvm.options
# -Xms4g
# -Xmx4g

sudo systemctl restart opensearch
```

---

## Performance Tuning

### Manager Tuning

```yaml
# manager.yml
server:
  workers: 8  # 2x CPU cores
  worker_connections: 1000

event_processing:
  batch_size: 200  # Increase for higher throughput
  queue_size: 10000
```

### OpenSearch Tuning

```yaml
# opensearch.yml
indices.memory.index_buffer_size: 30%
thread_pool.write.queue_size: 1000
```

### Database Connection Pooling

```python
# config.py
POOL_SIZE = 20
MAX_OVERFLOW = 40
POOL_RECYCLE = 3600
```

---

**Deployment guide v2.0.0**
**Last updated: 2025-01-12**
