# CyberSentinel DLP - Ubuntu Server Deployment Guide

Complete step-by-step guide for deploying CyberSentinel DLP on Ubuntu Server in production environments.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Preparation](#preparation)
3. [Deployment Methods](#deployment-methods)
4. [Automated Deployment (Recommended)](#automated-deployment-recommended)
5. [Manual Deployment](#manual-deployment)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### Server Requirements

**For Production Deployment:**
- **OS**: Ubuntu Server 20.04 LTS, 22.04 LTS, or 24.04 LTS
- **CPU**: 8 cores (3.0 GHz+)
- **RAM**: 16 GB
- **Storage**: 200 GB SSD
- **Network**: 1 Gbps with static IP
- **Root Access**: sudo privileges required

### Network Requirements

- Open ports: 3000 (Dashboard), 8000 (API Server)
- Stable internet connection for Docker image downloads
- Internal network access for endpoint agents

### Software Requirements

The deployment script will install:
- Docker Engine 24.0.0+
- Docker Compose Plugin 2.20.0+

---

## 📦 Preparation

### Step 1: Access Your Ubuntu Server

```bash
# SSH into your Ubuntu server
ssh username@your-ubuntu-server-ip

# Switch to root or use sudo
sudo -i
```

### Step 2: Transfer Project Files

**Option A: Using SCP (from your Windows machine)**
```powershell
# From Windows PowerShell
cd "C:\Users\Red Ghost\Desktop"
scp -r cybersentinel-dlp username@your-ubuntu-server-ip:/opt/
```

**Option B: Using Git (Recommended if you have a repository)**
```bash
# On Ubuntu server
cd /opt
git clone <your-repository-url> cybersentinel-dlp
cd cybersentinel-dlp
```

**Option C: Manual Upload**
- Use FileZilla, WinSCP, or similar tools
- Upload the entire `cybersentinel-dlp` folder to `/opt/` on Ubuntu server

### Step 3: Set Permissions

```bash
cd /opt/cybersentinel-dlp
chmod +x deploy-ubuntu.sh
chmod +x deploy.sh
```

---

## 🚀 Deployment Methods

### Method 1: Automated Deployment (RECOMMENDED ✨)

The automated script handles everything: Docker installation, configuration, deployment, and backups.

### Method 2: Manual Deployment

Step-by-step manual installation for advanced users who want full control.

---

## 🎯 Automated Deployment (Recommended)

### Complete One-Command Deployment

```bash
cd /opt/cybersentinel-dlp
sudo ./deploy-ubuntu.sh
```

### What the Script Does

1. ✅ Checks Ubuntu version and system requirements
2. ✅ Updates system packages
3. ✅ Installs Docker and Docker Compose
4. ✅ Configures Docker permissions
5. ✅ Creates secure `.env` file with random passwords
6. ✅ Configures firewall (UFW)
7. ✅ Creates required directories
8. ✅ Deploys all containers with Docker Compose
9. ✅ Sets up automatic daily backups
10. ✅ Verifies deployment and displays access information

### During Deployment

The script will prompt you for:
- **Server IP Address**: Your Ubuntu server's IP (auto-detected)
- **Firewall Configuration**: Confirmation to enable UFW
- **Existing .env File**: Overwrite confirmation if file exists

### Expected Output

```
==========================================
  CyberSentinel DLP - Ubuntu Deployment
==========================================

[INFO] Checking Ubuntu version...
[SUCCESS] Running on Ubuntu 22.04.3 LTS
[INFO] Updating system packages...
[SUCCESS] System updated
[INFO] Installing Docker...
[SUCCESS] Docker installed successfully: Docker version 24.0.7
...
[SUCCESS] All 5 containers are running
[SUCCESS] API server is healthy

==========================================
  CyberSentinel DLP Deployment Complete!
==========================================

Access URLs:
  Dashboard: http://192.168.1.100:3000
  API Server: http://192.168.1.100:8000
  API Docs: http://192.168.1.100:8000/docs

Default Credentials:
  Username: admin
  Password: admin
```

### Deployment Time

- **Total Time**: 10-15 minutes
- **Docker Installation**: 2-3 minutes
- **Container Download & Build**: 5-8 minutes
- **Service Startup**: 2-3 minutes

---

## 🛠️ Manual Deployment

For users who prefer step-by-step manual control.

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Docker

```bash
# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
docker compose version
```

### Step 3: Configure Environment

```bash
cd /opt/cybersentinel-dlp

# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

**Required Configuration:**
```bash
# Change these values!
SECRET_KEY=your-random-secret-key-here
POSTGRES_PASSWORD=your-strong-password
MONGODB_PASSWORD=your-strong-password
REDIS_PASSWORD=your-strong-password

# Set your server IP
HOST_IP=your-ubuntu-server-ip
```

**Generate Secure Passwords:**
```bash
# Generate random passwords
openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
```

### Step 4: Configure Firewall

```bash
# Allow SSH, Dashboard, and API
sudo ufw allow 22/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 5: Create Required Directories

```bash
sudo mkdir -p /var/log/cybersentinel
sudo mkdir -p /var/quarantine/dlp
sudo mkdir -p /backup/postgres
sudo mkdir -p /backup/mongodb

# Set permissions
sudo chown -R $USER:$USER /var/log/cybersentinel /var/quarantine/dlp
```

### Step 6: Deploy with Docker Compose

```bash
cd /opt/cybersentinel-dlp

# Pull images
docker compose pull

# Build and start containers
docker compose up -d --build

# View logs
docker compose logs -f
```

### Step 7: Wait for Services to Start

```bash
# Check container status (wait 2-3 minutes)
docker compose ps

# You should see all 5 services running:
# - cybersentinel-postgres (healthy)
# - cybersentinel-mongodb (healthy)
# - cybersentinel-redis (healthy)
# - cybersentinel-server (healthy)
# - cybersentinel-dashboard (running)
```

---

## ⚙️ Post-Deployment Configuration

### 1. Change Default Password

1. Access dashboard: `http://your-server-ip:3000`
2. Login with `admin` / `admin`
3. Navigate to Settings > Security
4. Change administrator password

### 2. Configure Email Alerts (Optional)

Edit `.env` file:
```bash
nano /opt/cybersentinel-dlp/.env
```

Add email configuration:
```bash
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@company.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=dlp-alerts@company.com
ALERT_EMAIL=admin@company.com
```

Restart services:
```bash
docker compose restart
```

### 3. Setup SSL/TLS with Nginx (Recommended)

#### Install Nginx

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

#### Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/cybersentinel
```

Add configuration:
```nginx
server {
    listen 80;
    server_name dlp.yourcompany.com;

    # Dashboard
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Server
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Docs
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

#### Enable Site and Get SSL Certificate

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cybersentinel /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Get SSL certificate
sudo certbot --nginx -d dlp.yourcompany.com

# Reload Nginx
sudo systemctl reload nginx
```

### 4. Setup Automatic Backups

The automated deployment script already sets this up, but for manual installations:

```bash
# Create backup script
sudo nano /usr/local/bin/cybersentinel-backup.sh
```

Add content:
```bash
#!/bin/bash
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
docker exec cybersentinel-postgres pg_dump -U dlp_user cybersentinel_dlp | gzip > /backup/postgres/backup_${BACKUP_DATE}.sql.gz

# MongoDB backup
docker exec cybersentinel-mongodb mongodump --archive=/backup/mongodb/backup_${BACKUP_DATE}.archive

# Delete backups older than 30 days
find /backup/postgres -name "*.sql.gz" -mtime +30 -delete
find /backup/mongodb -name "*.archive" -mtime +30 -delete

echo "Backup completed: $BACKUP_DATE"
```

Make executable and add to cron:
```bash
sudo chmod +x /usr/local/bin/cybersentinel-backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/cybersentinel-backup.sh") | crontab -
```

---

## ✅ Verification

### Check All Services Running

```bash
docker compose ps
```

Expected output:
```
NAME                         STATUS          PORTS
cybersentinel-postgres       Up (healthy)    0.0.0.0:5432->5432/tcp
cybersentinel-mongodb        Up (healthy)    0.0.0.0:27017->27017/tcp
cybersentinel-redis          Up (healthy)    0.0.0.0:6379->6379/tcp
cybersentinel-server         Up (healthy)    0.0.0.0:8000->8000/tcp
cybersentinel-dashboard      Up              0.0.0.0:3000->3000/tcp
```

### Test API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-02T10:30:00Z"
}
```

### Test Dashboard Access

```bash
curl -I http://localhost:3000
```

Expected: HTTP 200 OK

### Access from Browser

1. **Dashboard**: `http://your-server-ip:3000`
2. **API Docs**: `http://your-server-ip:8000/docs`

Default credentials:
- Username: `admin`
- Password: `admin`

---

## 🔧 Management Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f server
docker compose logs -f dashboard
```

### Stop System

```bash
docker compose down
```

### Start System

```bash
docker compose up -d
```

### Restart System

```bash
docker compose restart
```

### Restart Specific Service

```bash
docker compose restart server
docker compose restart dashboard
```

### Update System

```bash
# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker compose up -d --build
```

### View Resource Usage

```bash
docker stats
```

---

## 🐛 Troubleshooting

### Issue: Containers Not Starting

**Check logs:**
```bash
docker compose logs
```

**Check Docker status:**
```bash
sudo systemctl status docker
```

**Restart Docker:**
```bash
sudo systemctl restart docker
docker compose up -d
```

### Issue: Port Already in Use

**Find process using port:**
```bash
sudo lsof -i :3000
sudo lsof -i :8000
```

**Kill process:**
```bash
sudo kill -9 <PID>
```

### Issue: API Health Check Failing

**Wait longer:**
Services may need 2-3 minutes to fully start.

**Check server logs:**
```bash
docker compose logs server
```

**Restart server:**
```bash
docker compose restart server
```

### Issue: Database Connection Errors

**Check database containers:**
```bash
docker compose ps postgres mongodb redis
```

**Restart databases:**
```bash
docker compose restart postgres mongodb redis
docker compose restart server
```

### Issue: Permission Denied

**Fix Docker permissions:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: Disk Space Full

**Check disk usage:**
```bash
df -h
docker system df
```

**Clean up Docker:**
```bash
docker system prune -a
docker volume prune
```

### Get Support

**View all container logs:**
```bash
docker compose logs --tail=100 > /tmp/dlp-logs.txt
```

**Check system resources:**
```bash
free -h
df -h
top
```

---

## 📊 Monitoring

### Setup Monitoring Dashboard

Install monitoring tools:
```bash
docker run -d \
  --name=netdata \
  --restart=always \
  -p 19999:19999 \
  netdata/netdata
```

Access monitoring: `http://your-server-ip:19999`

### Check Service Health

Create health check script:
```bash
nano /usr/local/bin/check-dlp-health.sh
```

Add:
```bash
#!/bin/bash
echo "=== DLP System Health Check ==="
echo ""
echo "Docker Containers:"
docker compose ps
echo ""
echo "API Health:"
curl -s http://localhost:8000/health | jq
echo ""
echo "Dashboard Status:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:3000
```

Make executable:
```bash
chmod +x /usr/local/bin/check-dlp-health.sh
```

Run health check:
```bash
/usr/local/bin/check-dlp-health.sh
```

---

## 🎯 Next Steps After Deployment

1. ✅ Change default admin password
2. ✅ Configure email alerts
3. ✅ Setup SSL/TLS certificates
4. ✅ Create custom DLP policies
5. ✅ Deploy agents to endpoints
6. ✅ Configure Wazuh SIEM integration
7. ✅ Test DLP detection capabilities
8. ✅ Train users on data handling policies

---

## 📚 Additional Resources

- Main Documentation: `MASTER_DOCUMENTATION.md`
- Deployment Guide: `DEPLOYMENT_GUIDE.md`
- Quick Start: `QUICKSTART.md`
- API Documentation: `http://your-server-ip:8000/docs`

---

## ✅ Deployment Checklist

- [ ] Ubuntu server meets minimum requirements
- [ ] SSH access with sudo privileges
- [ ] Project files transferred to `/opt/cybersentinel-dlp`
- [ ] Deployment script executed successfully
- [ ] All 5 containers running and healthy
- [ ] Dashboard accessible via browser
- [ ] API health check passing
- [ ] Firewall configured (ports 3000, 8000 open)
- [ ] Default admin password changed
- [ ] Email alerts configured (optional)
- [ ] SSL/TLS configured (recommended)
- [ ] Automatic backups scheduled
- [ ] First endpoint agent deployed
- [ ] DLP policies created and tested

---

**Deployment Complete! 🎉**

Your CyberSentinel DLP system is now running on Ubuntu Server and ready for production use.
