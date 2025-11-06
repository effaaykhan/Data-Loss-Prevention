# CyberSentinel DLP - Quick Start Guide

Get your enterprise DLP system running in 10 minutes!

## Prerequisites

Before you begin, ensure you have:

- **Docker**: Version 24.0 or higher
- **Docker Compose**: Version 2.20 or higher
- **Operating System**: Linux, macOS, or Windows 10+ with WSL2
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: At least 50GB free
- **Network**: Ports 3000, 8000, 5432, 27017, 6379 available

## Installation Steps

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourorg/cybersentinel-dlp.git
cd cybersentinel-dlp
```

### Step 2: Configure Environment

```bash
# Copy environment templates
cp config/env-templates/.env.server.example server/.env

# Copy dashboard template (either option works):
cp config/env-templates/.env.dashboard.example dashboard/.env.local
# OR: cp dashboard/.env.local.example dashboard/.env.local

# IMPORTANT: Update with your host IP address
# Get your IP address:
# Linux/macOS:
hostname -I | awk '{print $1}'
# Windows:
ipconfig | findstr IPv4

# Edit dashboard/.env.local and replace localhost with your IP
# Example: NEXT_PUBLIC_API_URL=http://192.168.1.100:8000/api/v1
```

### Step 3: Deploy with Docker

```bash
# Make deploy script executable (Linux/macOS)
chmod +x deploy.sh

# Install and start all services
./deploy.sh install
./deploy.sh start

# On Windows (use Git Bash or WSL2):
bash deploy.sh install
bash deploy.sh start

# Or use docker-compose directly:
docker-compose up -d
```

### Step 4: Verify Installation

```bash
# Check service status
docker-compose ps

# All services should show "healthy" or "Up"
```

### Step 5: Access the Dashboard

Open your web browser and navigate to:

```
http://<your-host-ip>:3000
```

**Default Login Credentials:**
- Email: `admin@cybersentinel.local`
- Password: `ChangeMe123!`

**IMPORTANT**: Change the password immediately after first login!

## Quick Test

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"CyberSentinel DLP","version":"1.0.0"}
```

### Test the Dashboard

1. Login with default credentials
2. You should see the dashboard with:
   - Real-time statistics
   - Event timeline chart
   - Recent events (may be empty initially)
   - Active policies

### Create Your First Policy

1. Navigate to **Policies** in the sidebar
2. Click **Create Policy**
3. Fill in policy details:
   - Name: "Test Credit Card Detection"
   - Description: "Block credit card numbers"
   - Add condition: `classification.labels contains PAN`
   - Add action: `block`
4. Save policy

### Generate Test Event (Optional)

```bash
# Send a test event to the API
curl -X POST http://localhost:8000/api/v1/events \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test",
    "user_email": "test@example.com",
    "classification": {
      "score": 0.95,
      "labels": ["TEST"],
      "method": "manual"
    }
  }'
```

## Common Commands

### Start Services

```bash
./deploy.sh start
# or
docker-compose up -d
```

### Stop Services

```bash
./deploy.sh stop
# or
docker-compose down
```

### View Logs

```bash
# All services
./deploy.sh logs

# Specific service
./deploy.sh logs server
./deploy.sh logs dashboard

# Or with docker-compose
docker-compose logs -f server
docker-compose logs -f dashboard
```

### Restart Services

```bash
./deploy.sh restart
# or
docker-compose restart
```

### Check Status

```bash
./deploy.sh status
# or
docker-compose ps
```

## Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| Dashboard | `http://<host-ip>:3000` | Web interface |
| API | `http://<host-ip>:8000` | REST API |
| API Docs | `http://<host-ip>:8000/api/v1/docs` | Swagger UI |
| Metrics | `http://<host-ip>:8000/metrics` | Prometheus metrics |
| PostgreSQL | `localhost:5432` | Relational database |
| MongoDB | `localhost:27017` | Document database |
| Redis | `localhost:6379` | Cache |

## Next Steps

### 1. Configure Policies

Review and customize the pre-configured policies:

```bash
ls config/policies/
# - pci-dss-credit-card.yaml
# - gdpr-pii-protection.yaml
# - hipaa-phi-protection.yaml
```

Edit these files or create new ones based on your requirements.

### 2. Set Up Wazuh Integration

```bash
# Copy Wazuh configuration files
sudo cp integrations/wazuh/decoders/dlp.xml /var/ossec/etc/decoders/
sudo cp integrations/wazuh/rules/dlp.xml /var/ossec/etc/rules/

# Restart Wazuh
sudo systemctl restart wazuh-manager
```

### 3. Deploy Endpoint Agents

Follow the agent deployment guide for your operating system:

```bash
# See docs/modules/AGENTS.md
```

### 4. Configure Email Alerts

Update email settings in `server/.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=dlp@company.com
```

### 5. Enable HTTPS (Production)

Set up Nginx reverse proxy with SSL:

```bash
# See docs/deployment/NGINX_SETUP.md
```

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are already in use
lsof -i :3000  # Dashboard
lsof -i :8000  # API
lsof -i :5432  # PostgreSQL
lsof -i :27017 # MongoDB
lsof -i :6379  # Redis

# Kill conflicting processes if needed
```

### Can't Access Dashboard

```bash
# 1. Check if dashboard is running
docker-compose ps dashboard

# 2. Check dashboard logs
docker-compose logs dashboard

# 3. Verify API URL in dashboard/.env.local
cat dashboard/.env.local

# 4. Test from browser
curl http://localhost:3000
```

### Login Fails

```bash
# 1. Verify API is running
curl http://localhost:8000/health

# 2. Check API logs
docker-compose logs server

# 3. Use default credentials
# Email: admin@cybersentinel.local
# Password: ChangeMe123!
```

### Database Connection Errors

```bash
# Check database containers
docker-compose ps postgres mongodb

# Restart databases
docker-compose restart postgres mongodb

# View logs
docker-compose logs postgres
docker-compose logs mongodb
```

## Getting Help

- **Documentation**: See [MASTER_DOCUMENTATION.md](MASTER_DOCUMENTATION.md)
- **Module Docs**: Check `docs/modules/` for specific components
- **GitHub Issues**: [Report issues here](https://github.com/yourorg/cybersentinel-dlp/issues)
- **Email Support**: support@cybersentinel.local

## Security Checklist

Before going to production:

- [ ] Change default admin password
- [ ] Generate new SECRET_KEY (32+ characters)
- [ ] Set strong database passwords
- [ ] Configure firewall rules
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure CORS for your domain only
- [ ] Set up regular backups
- [ ] Enable audit logging
- [ ] Configure email alerts
- [ ] Review and test all policies
- [ ] Set up monitoring and alerting
- [ ] Document your configuration
- [ ] Train users on the system

## Backup & Recovery

### Create Backup

```bash
./deploy.sh backup

# Backup file will be saved to:
# backups/cybersentinel_backup_<timestamp>.tar.gz
```

### Restore from Backup

```bash
# Extract backup
tar -xzf backups/cybersentinel_backup_<timestamp>.tar.gz

# Restore databases
docker-compose exec -T postgres psql -U dlp_user < postgres_backup.sql
docker-compose exec -T mongodb mongorestore --archive < mongodb_backup.archive
```

## Performance Tuning

For high-volume environments:

```bash
# Increase workers in server/.env
WORKERS=8

# Scale services
docker-compose up -d --scale server=3

# Configure connection pools
POSTGRES_POOL_SIZE=50
MONGODB_MAX_POOL_SIZE=200
```

## Monitoring

View real-time metrics:

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Service stats
docker stats

# System resources
htop
```

## Upgrading

```bash
# Pull latest changes
git pull

# Rebuild and restart
./deploy.sh update

# Or manually:
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Cleanup

To remove all containers and data:

```bash
./deploy.sh cleanup

# WARNING: This will delete all data!
```

---

**Congratulations!** You now have a fully functional enterprise DLP system running.

For detailed documentation, see [MASTER_DOCUMENTATION.md](MASTER_DOCUMENTATION.md).
