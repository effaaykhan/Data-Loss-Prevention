# CyberSentinel DLP - Complete Deployment Guide

## ✅ YES, THE SERVER IS READY FOR DEPLOYMENT!

This guide provides complete details for deploying the CyberSentinel DLP system in production environments.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Supported Platforms](#supported-platforms)
3. [Deployment Methods](#deployment-methods)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Configuration](#configuration)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Hardware Requirements

#### **Minimum Requirements** (For Testing/Small Organizations <50 endpoints)
- **CPU**: 4 cores (2.5 GHz+)
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 100 Mbps
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+, RHEL 8+) or Windows Server 2019+

#### **Recommended Requirements** (For Production/Medium Organizations 50-500 endpoints)
- **CPU**: 8 cores (3.0 GHz+)
- **RAM**: 16 GB
- **Storage**: 200 GB SSD (RAID 1 recommended)
- **Network**: 1 Gbps
- **OS**: Ubuntu 22.04 LTS or RHEL 9

#### **Enterprise Requirements** (Large Organizations 500+ endpoints)
- **CPU**: 16+ cores (3.5 GHz+)
- **RAM**: 32 GB+
- **Storage**: 500 GB+ SSD (RAID 10 recommended)
- **Network**: 10 Gbps
- **OS**: Ubuntu 22.04 LTS or RHEL 9
- **High Availability**: Load balancer + 2+ nodes

### Software Requirements

#### **Required Software**
- **Docker**: 24.0.0+ (Docker Engine or Docker Desktop)
- **Docker Compose**: 2.20.0+
- **Git**: 2.30.0+

#### **Optional (for manual deployment)**
- **Python**: 3.11+
- **Node.js**: 18.0.0+
- **PostgreSQL**: 15+
- **MongoDB**: 7.0+
- **Redis**: 7.0+

---

## 🌍 Supported Platforms

### ✅ Supported Operating Systems

| Platform | Versions | Status | Notes |
|----------|----------|--------|-------|
| **Ubuntu** | 20.04, 22.04, 24.04 LTS | ✅ Recommended | Best tested platform |
| **Red Hat Enterprise Linux** | 8, 9 | ✅ Supported | Enterprise-grade |
| **CentOS** | 8, 9 Stream | ✅ Supported | Community alternative to RHEL |
| **Debian** | 11, 12 | ✅ Supported | Stable and reliable |
| **Windows Server** | 2019, 2022 | ✅ Supported | Requires Docker Desktop |
| **macOS** | 12+ (Monterey+) | ⚠️ Development Only | Not recommended for production |

### ✅ Cloud Platforms

| Provider | Service | Status | Notes |
|----------|---------|--------|-------|
| **AWS** | EC2, ECS, Fargate | ✅ Fully Supported | Use t3.large+ instances |
| **Azure** | Virtual Machines, Container Instances | ✅ Fully Supported | Use Standard_D4s_v3+ |
| **Google Cloud** | Compute Engine, GKE | ✅ Fully Supported | Use n2-standard-4+ |
| **DigitalOcean** | Droplets, App Platform | ✅ Supported | Use 4GB+ droplets |
| **On-Premises** | VMware, Hyper-V, Proxmox | ✅ Fully Supported | Any virtualization platform |
| **Bare Metal** | Physical Servers | ✅ Fully Supported | Best performance |

---

## 🚀 Deployment Methods

### Method 1: Docker Compose (Recommended - Easiest)
- ✅ **Best for**: Production, Testing, Development
- ⏱️ **Setup Time**: 10-15 minutes
- 💪 **Difficulty**: Easy
- 📦 **Components**: Everything in containers

### Method 2: Manual Installation
- ✅ **Best for**: Custom setups, Advanced users
- ⏱️ **Setup Time**: 30-60 minutes
- 💪 **Difficulty**: Advanced
- 📦 **Components**: Installed separately

### Method 3: Kubernetes (Enterprise)
- ✅ **Best for**: Large deployments, High availability
- ⏱️ **Setup Time**: 2-4 hours
- 💪 **Difficulty**: Expert
- 📦 **Components**: Orchestrated pods

---

## 📖 Step-by-Step Deployment

### 🔥 Method 1: Docker Compose Deployment (RECOMMENDED)

This is the fastest and most reliable method for deploying CyberSentinel DLP.

#### **Step 1: System Preparation**

##### On Ubuntu/Debian:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Add user to docker group (to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

##### On RHEL/CentOS:
```bash
# Update system
sudo dnf update -y

# Install Docker
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

##### On Windows Server:
```powershell
# Download and install Docker Desktop for Windows
# From: https://www.docker.com/products/docker-desktop/

# After installation, restart the system
# Verify installation
docker --version
docker compose version
```

#### **Step 2: Download/Clone the Project**

```bash
# Clone the repository (if using Git)
git clone <your-repository-url>
cd cybersentinel-dlp

# OR if you already have the files
cd /path/to/cybersentinel-dlp
```

#### **Step 3: Configure Environment Variables**

```bash
# Create environment file
cp .env.example .env

# Edit the .env file with your settings
nano .env  # or use your preferred editor
```

**Important Environment Variables to Set:**

```bash
# Security (CHANGE THESE!)
SECRET_KEY=your-super-secret-key-change-this-in-production
POSTGRES_PASSWORD=your-strong-postgres-password
MONGODB_PASSWORD=your-strong-mongodb-password
REDIS_PASSWORD=your-strong-redis-password

# Network Configuration
HOST_IP=10.220.143.130  # Your server's IP address

# Optional: Email Alerts
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@company.com
SMTP_PASSWORD=your-email-password
ALERT_EMAIL=admin@company.com
```

#### **Step 4: Deploy the System**

```bash
# Option A: Using the deployment script (Recommended)
chmod +x deploy.sh
./deploy.sh install
./deploy.sh start

# Option B: Manual deployment
docker compose up -d

# Wait for all services to start (2-3 minutes)
docker compose ps

# Check logs
docker compose logs -f
```

#### **Step 5: Verify Deployment**

```bash
# Check all services are running
docker compose ps

# You should see:
# - cybersentinel-postgres (healthy)
# - cybersentinel-mongodb (healthy)
# - cybersentinel-redis (healthy)
# - cybersentinel-server (healthy)
# - cybersentinel-dashboard (running)

# Check server health
curl http://10.220.143.130:8000/health

# Check dashboard
curl http://10.220.143.130:3000
```

#### **Step 6: Access the Dashboard**

1. Open your web browser
2. Navigate to: `http://10.220.143.130:3000`
3. Login with credentials:
   - **Username**: `admin`
   - **Password**: `admin`
4. **IMPORTANT**: Change the default password immediately!

---

### 🛠️ Method 2: Manual Installation (Advanced)

#### **Step 1: Install Dependencies**

##### Install PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt install postgresql-15 postgresql-contrib -y

# RHEL/CentOS
sudo dnf install postgresql15-server postgresql15-contrib -y
sudo postgresql-15-setup initdb
sudo systemctl start postgresql-15
sudo systemctl enable postgresql-15
```

##### Install MongoDB:
```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# RHEL/CentOS
# Create repo file /etc/yum.repos.d/mongodb-org-7.0.repo
sudo dnf install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

##### Install Redis:
```bash
# Ubuntu/Debian
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

# RHEL/CentOS
sudo dnf install redis -y
sudo systemctl start redis
sudo systemctl enable redis
```

##### Install Python 3.11+:
```bash
# Ubuntu/Debian
sudo apt install python3.11 python3.11-venv python3-pip -y

# RHEL/CentOS
sudo dnf install python3.11 python3.11-pip -y
```

##### Install Node.js 18+:
```bash
# Using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Or using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

#### **Step 2: Configure Databases**

##### PostgreSQL:
```bash
sudo -u postgres psql

CREATE USER dlp_user WITH PASSWORD 'changeme123';
CREATE DATABASE cybersentinel_dlp OWNER dlp_user;
GRANT ALL PRIVILEGES ON DATABASE cybersentinel_dlp TO dlp_user;
\q
```

##### MongoDB:
```bash
mongosh

use admin
db.createUser({
  user: "dlp_user",
  pwd: "changeme123",
  roles: [ { role: "root", db: "admin" } ]
})

use cybersentinel_dlp
\q
```

#### **Step 3: Install Backend Server**

```bash
cd server

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key-here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=dlp_user
POSTGRES_PASSWORD=changeme123
POSTGRES_DB=cybersentinel_dlp
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=dlp_user
MONGODB_PASSWORD=changeme123
MONGODB_DB=cybersentinel_dlp
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=changeme123
EOF

# Run database migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### **Step 4: Install Dashboard**

```bash
cd ../dashboard

# Install dependencies
npm install

# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://10.220.143.130:8000/api/v1
NEXT_PUBLIC_APP_NAME=CyberSentinel DLP
NEXT_PUBLIC_APP_VERSION=1.0.0
EOF

# Build for production
npm run build

# Start dashboard
npm run start
```

---

### ☸️ Method 3: Kubernetes Deployment (Enterprise)

For Kubernetes deployment, see the separate `docs/kubernetes/KUBERNETES_DEPLOYMENT.md` guide.

**Quick Start:**
```bash
# Apply Kubernetes manifests
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/configmaps/
kubectl apply -f infrastructure/kubernetes/secrets/
kubectl apply -f infrastructure/kubernetes/deployments/
kubectl apply -f infrastructure/kubernetes/services/
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

---

## ⚙️ Configuration

### Network Configuration

#### Firewall Rules (Required)

```bash
# Allow inbound traffic on required ports
sudo ufw allow 3000/tcp   # Dashboard
sudo ufw allow 8000/tcp   # API Server
sudo ufw allow 5432/tcp   # PostgreSQL (if external access needed)
sudo ufw allow 27017/tcp  # MongoDB (if external access needed)
sudo ufw allow 6379/tcp   # Redis (if external access needed)

# Enable firewall
sudo ufw enable
```

#### For Production (Recommended):
```bash
# Only expose Dashboard and API
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp

# Database ports should NOT be exposed to the internet
# Only allow from specific IPs if needed
sudo ufw allow from 192.168.1.0/24 to any port 5432
```

### SSL/TLS Configuration (Recommended for Production)

#### Using Nginx Reverse Proxy:

```bash
# Install Nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/cybersentinel
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name dlp.yourcompany.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
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

# Get SSL certificate
sudo certbot --nginx -d dlp.yourcompany.com

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx
```

### Database Backup Configuration

```bash
# Add to crontab (daily backups at 2 AM)
crontab -e

# PostgreSQL backup
0 2 * * * docker exec cybersentinel-postgres pg_dump -U dlp_user cybersentinel_dlp > /backup/postgres-$(date +\%Y\%m\%d).sql

# MongoDB backup
0 2 * * * docker exec cybersentinel-mongodb mongodump --username dlp_user --password changeme123 --db cybersentinel_dlp --out /backup/mongodb-$(date +\%Y\%m\%d)
```

---

## 🎯 Post-Deployment

### 1. Initial Setup Checklist

- [ ] Change default admin password
- [ ] Configure email alerts
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Configure monitoring
- [ ] Deploy first endpoint agent
- [ ] Test DLP policies

### 2. Deploy Your First Agent

1. Navigate to `http://10.220.143.130:3000/dashboard/agents`
2. Click **"Deploy Agent"**
3. Select OS (Windows or Linux)
4. Enter agent name (e.g., `WIN-DESK-01`)
5. Verify server IP (`10.220.143.130`)
6. Click **"Generate Installation Script"**
7. Download or copy the script
8. Run on target endpoint
9. Verify agent appears in dashboard

### 3. Configure DLP Policies

1. Go to **Policies** page
2. Enable desired policies:
   - ✅ Block USB Transfers
   - ✅ Cloud Storage Monitor
   - ✅ Clipboard Protection
   - ✅ PCI-DSS Compliance
   - ✅ GDPR Personal Data
3. Customize rules as needed

### 4. Monitoring & Alerts

Check these dashboards regularly:
- **Dashboard**: Overall system health
- **Events**: DLP violations
- **Agents**: Endpoint status
- **Users**: User risk scores

---

## 🐛 Troubleshooting

### Common Issues

#### **Issue**: Containers won't start
```bash
# Check logs
docker compose logs

# Restart services
docker compose restart

# Rebuild if needed
docker compose build --no-cache
docker compose up -d
```

#### **Issue**: Dashboard shows "Connection Refused"
```bash
# Check if server is running
docker compose ps
curl http://localhost:8000/health

# Check firewall
sudo ufw status

# Check if port is listening
netstat -tuln | grep 3000
```

#### **Issue**: Database connection errors
```bash
# Check database health
docker compose exec postgres pg_isready -U dlp_user
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Restart databases
docker compose restart postgres mongodb
```

#### **Issue**: High memory usage
```bash
# Check container stats
docker stats

# Increase Docker memory limit
# Edit docker-compose.yml and add:
# mem_limit: 2g  # under each service
```

### Getting Help

- **Documentation**: Check `MASTER_DOCUMENTATION.md`
- **Quick Start**: See `QUICKSTART.md`
- **Logs**: `docker compose logs -f`
- **Health Check**: `http://10.220.143.130:8000/health`

---

## 📊 Performance Tuning

### Database Optimization

**PostgreSQL:**
```bash
# Edit postgresql.conf
docker exec -it cybersentinel-postgres bash
vi /var/lib/postgresql/data/postgresql.conf

# Increase these values based on your RAM
shared_buffers = 2GB          # 25% of RAM
effective_cache_size = 6GB    # 75% of RAM
maintenance_work_mem = 512MB
work_mem = 50MB
```

**MongoDB:**
```bash
# Increase WiredTiger cache
docker exec -it cybersentinel-mongodb mongosh
db.adminCommand({ setParameter: 1, wiredTigerEngineRuntimeConfig: "cache_size=4GB" })
```

### Application Scaling

For high-traffic environments:
```yaml
# In docker-compose.yml
server:
  deploy:
    replicas: 3  # Run 3 instances
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

---

## 🎓 Summary

**YES, THE SERVER IS READY FOR DEPLOYMENT!**

### Quick Deployment Summary:

1. **Choose Platform**: Ubuntu 22.04 LTS (Recommended)
2. **Install Docker**: `curl -fsSL https://get.docker.com | sh`
3. **Clone Project**: Get the code
4. **Configure**: Edit `.env` file
5. **Deploy**: Run `./deploy.sh start`
6. **Access**: `http://10.220.143.130:3000`
7. **Login**: admin / admin

**Deployment Time**: 10-15 minutes with Docker Compose

**Recommended Hosting**:
- Small: AWS t3.large or DigitalOcean 8GB Droplet
- Medium: AWS t3.xlarge or Dedicated Server with 16GB RAM
- Enterprise: Kubernetes cluster with load balancing

**Cost Estimate**:
- AWS: $50-200/month depending on scale
- DigitalOcean: $40-160/month
- On-Premises: Hardware cost only

The system is production-ready and can scale from 10 to 10,000+ endpoints!
