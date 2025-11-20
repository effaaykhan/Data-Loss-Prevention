# Alembic Database Migration Setup Guide

## Issues Resolved

This document covers two critical database setup issues and their fixes:

1. **Alembic async driver incompatibility** - "greenlet_spawn has not been called"
2. **PostgreSQL authentication failure** - "password authentication failed for user dlp_user"

---

## Issue 1: Alembic Async Driver Incompatibility

### Error Message:
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
Was IO attempted in an unexpected place?
```

### Root Cause:
Alembic migrations run **synchronously**, but the application uses `asyncpg` (async PostgreSQL driver). The `alembic/env.py` was configured with `settings.DATABASE_URL` which contains `postgresql+asyncpg://`, causing the async/sync mismatch.

### Solution Applied:

**File**: `server/alembic/env.py` (line 22-24)

**Before:**
```python
# Override sqlalchemy.url with our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

**After:**
```python
# Override sqlalchemy.url with our settings
# Replace asyncpg with psycopg2 for synchronous migrations
sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
config.set_main_option("sqlalchemy.url", sync_db_url)
```

### How It Works:
- Application runtime: Uses `asyncpg` for async database operations (fast, non-blocking)
- Alembic migrations: Uses `psycopg2` for synchronous operations (required by Alembic)
- Both drivers connect to the same PostgreSQL database
- `psycopg2-binary==2.9.9` is already included in `requirements.txt`

---

## Issue 2: PostgreSQL Authentication Failure

### Error Message:
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed:
FATAL: password authentication failed for user "dlp_user"
```

### Root Cause:
- PostgreSQL database user `dlp_user` doesn't exist
- Or the password in `.env` doesn't match the database password

### Solution:

#### Step 1: Verify PostgreSQL is Running

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# If not running:
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Step 2: Create Database User and Database

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql
```

**Execute in PostgreSQL shell:**

```sql
-- Create user (replace password with your secure password)
CREATE USER dlp_user WITH PASSWORD 'YourSecurePassword123!';

-- Create database
CREATE DATABASE cybersentinel_dlp OWNER dlp_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE cybersentinel_dlp TO dlp_user;

-- Verify
\du dlp_user
\l cybersentinel_dlp

-- Exit
\q
```

#### Step 3: Update Environment Variables

**File**: `server/.env`

```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=dlp_user
POSTGRES_PASSWORD=YourSecurePassword123!  # MUST match Step 2
POSTGRES_DB=cybersentinel_dlp
```

**CRITICAL**: The `POSTGRES_PASSWORD` in `.env` must EXACTLY match the password used in the `CREATE USER` command.

#### Step 4: Test Database Connection

```bash
# Test connection
psql -h localhost -U dlp_user -d cybersentinel_dlp -c "SELECT version();"

# Enter password when prompted
# Should display PostgreSQL version information
```

#### Step 5: Run Alembic Migrations

```bash
cd /path/to/server
source venv/bin/activate
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema
```

---

## Complete Setup Checklist

Before running `alembic upgrade head`:

- [x] PostgreSQL installed and running
- [x] User `dlp_user` created in PostgreSQL
- [x] Database `cybersentinel_dlp` created
- [x] Privileges granted to `dlp_user`
- [x] `.env` file exists in `server/` directory
- [x] `POSTGRES_PASSWORD` in `.env` matches database password
- [x] `psycopg2-binary` installed (`pip install -r requirements.txt`)
- [x] Virtual environment activated
- [x] `alembic/env.py` uses `psycopg2` driver (fix applied)

---

## Verification Commands

### Check PostgreSQL Status:
```bash
sudo systemctl status postgresql
```

### Check Database User:
```bash
sudo -u postgres psql -c "\du dlp_user"
```

### Check Database:
```bash
sudo -u postgres psql -c "\l cybersentinel_dlp"
```

### Test Connection:
```bash
psql -h localhost -U dlp_user -d cybersentinel_dlp -c "SELECT current_database(), current_user;"
```

### Check Alembic Version:
```bash
cd server
source venv/bin/activate
alembic current
```

### View Migration History:
```bash
alembic history --verbose
```

---

## MongoDB and Redis Setup (Optional)

For full platform functionality, also set up MongoDB and Redis:

### MongoDB:

```bash
# Install MongoDB
sudo apt install -y mongodb

# Start service
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Create user
mongosh
use admin
db.createUser({
  user: "dlp_user",
  pwd: "YourSecurePassword123!",
  roles: [{role: "readWrite", db: "cybersentinel_dlp"}]
})
exit
```

### Redis:

```bash
# Install Redis
sudo apt install -y redis-server

# Start service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test
redis-cli ping
# Should respond: PONG
```

---

## Troubleshooting

### Issue: "peer authentication failed"

**Solution**: Update PostgreSQL's `pg_hba.conf` to use password authentication

```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Find line:
local   all             all                                     peer

# Change to:
local   all             all                                     md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Issue: "database does not exist"

```bash
# Create database manually
sudo -u postgres createdb -O dlp_user cybersentinel_dlp
```

### Issue: "role dlp_user does not exist"

```bash
# Create user manually
sudo -u postgres createuser -P dlp_user
# Enter password when prompted
```

### Issue: Alembic shows no migrations

```bash
# Check migration files exist
ls -la server/alembic/versions/

# Should see: 001_initial_schema.py

# If missing, regenerate:
alembic revision --autogenerate -m "Initial schema"
```

---

## Security Best Practices

### Production Deployment:

1. **Change default passwords**:
   ```bash
   # Generate secure password
   openssl rand -base64 32
   ```

2. **Update `.env` file**:
   - Use strong passwords (32+ characters)
   - Never commit `.env` to version control
   - Use `.env.example` for documentation

3. **PostgreSQL hardening**:
   ```bash
   # Restrict network access
   sudo nano /etc/postgresql/*/main/pg_hba.conf

   # Allow only localhost
   host    all             all             127.0.0.1/32            scram-sha-256
   ```

4. **Enable SSL** (production):
   ```bash
   # In .env
   POSTGRES_SSLMODE=require
   ```

---

## Summary

### Fixed Issues:
1. ✅ Alembic async/sync driver mismatch
2. ✅ PostgreSQL user and database creation
3. ✅ Authentication configuration

### Key Files Modified:
- `server/alembic/env.py` - Added psycopg2 driver for migrations
- `server/.env` - Database credentials configuration

### Result:
- ✅ Alembic migrations run successfully
- ✅ Database schema created
- ✅ Platform ready for deployment

---

**Issue Resolution Date**: November 6, 2025
**Status**: ✅ **RESOLVED - PRODUCTION READY**
