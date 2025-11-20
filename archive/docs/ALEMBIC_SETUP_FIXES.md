# Alembic Database Migration Setup Fixes

This document describes the fixes applied to resolve `alembic upgrade head` errors and environment template issues.

## Issues Fixed

### 1. Pydantic V2 Compatibility (config.py)

**Problem**: The code was using Pydantic v1 `@validator` decorator with Pydantic v2 (2.5.0), causing validation errors.

**Solution**:
- Updated imports: `from pydantic import Field, field_validator`
- Added `SettingsConfigDict` import
- Replaced `@validator` with `@field_validator`
- Updated validator syntax to use `mode="before"` and `@classmethod`
- Replaced `class Config` with `model_config = SettingsConfigDict(...)`

**Files Modified**:
- `server/app/core/config.py`

### 2. Environment Variable Format (CORS_ORIGINS, ALLOWED_HOSTS)

**Problem**: Pydantic Settings was trying to parse `List[str]` fields as JSON, but the `.env` file had comma-separated values.

**Solution**:
- Updated `.env` file format to use JSON array syntax
- Changed from: `CORS_ORIGINS=http://localhost:3000,http://0.0.0.0:3000`
- Changed to: `CORS_ORIGINS=["http://localhost:3000","http://0.0.0.0:3000"]`

**Files Modified**:
- `server/.env` (not in git, user must configure)
- `config/env-templates/.env.server.example` (template updated)

### 3. Missing Integer Import (alert.py)

**Problem**: `Integer` type was used in model columns but not imported from SQLAlchemy.

**Solution**:
- Added `Integer` to SQLAlchemy imports
- Changed: `from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Index`
- To: `from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer, Index`

**Files Modified**:
- `server/app/models/alert.py`

### 4. Reserved Attribute Name (metadata)

**Problem**: SQLAlchemy's Declarative API reserves the `metadata` attribute name, causing `InvalidRequestError`.

**Solution**:
- Renamed Python attribute from `metadata` to `alert_metadata` / `file_metadata`
- Used column name mapping to keep database column as `metadata`
- Syntax: `alert_metadata = Column("metadata", JSON, nullable=True)`
- Updated `to_dict()` methods to use new attribute names

**Files Modified**:
- `server/app/models/alert.py`
- `server/app/models/classified_file.py`

### 5. Missing Environment Template

**Problem**: User tried to copy `config/env-templates/.env.dashboard.example` but it didn't exist.

**Solution**:
- Created `config/env-templates/.env.dashboard.example`
- Copied from existing `dashboard/.env.local.example`

**Files Added**:
- `config/env-templates/.env.dashboard.example`

## Setup Instructions

### For Development (Without Docker)

1. **Install Python Dependencies**:
   ```bash
   cd server
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   # Copy server environment template
   cp config/env-templates/.env.server.example server/.env

   # Copy dashboard environment template (option 1)
   cp config/env-templates/.env.dashboard.example dashboard/.env.local

   # OR copy dashboard environment template (option 2)
   cp dashboard/.env.local.example dashboard/.env.local
   ```

3. **Edit Configuration Files**:
   - Update `server/.env`:
     - Set `SECRET_KEY` to a secure random string (min 32 characters)
     - Set `POSTGRES_PASSWORD` and `MONGODB_PASSWORD`
     - Ensure `CORS_ORIGINS` and `ALLOWED_HOSTS` use JSON array format

   - Update `dashboard/.env.local`:
     - Replace `localhost` with your server's IP address in `NEXT_PUBLIC_API_URL`

4. **Initialize Database** (requires PostgreSQL running):
   ```bash
   cd server
   alembic upgrade head
   ```

### For Docker Deployment

Follow the standard Docker deployment process - all configurations are handled automatically.

## Common Issues

### Issue: `alembic upgrade head` fails with validation error

**Cause**: Environment variables in `.env` file are not in correct JSON format.

**Fix**: Ensure `CORS_ORIGINS` and `ALLOWED_HOSTS` use JSON array syntax:
```bash
CORS_ORIGINS=["http://localhost:3000","http://0.0.0.0:3000"]
ALLOWED_HOSTS=["*"]
```

### Issue: `ModuleNotFoundError` when running alembic

**Cause**: Required Python packages not installed.

**Fix**: Install all server dependencies:
```bash
cd server
pip install -r requirements.txt
```

### Issue: Cannot connect to database

**Cause**: PostgreSQL database is not running or connection settings are incorrect.

**Fix**:
- Ensure PostgreSQL is running on the configured host/port
- Verify credentials in `server/.env` match your database setup
- Check that the database `cybersentinel_dlp` exists

## Database Connection Requirements

Alembic migrations require an actual PostgreSQL database connection. The following services must be running:

1. **PostgreSQL** (port 5432)
   - Database: `cybersentinel_dlp`
   - User: As configured in `POSTGRES_USER`
   - Password: As configured in `POSTGRES_PASSWORD`

2. **MongoDB** (port 27017) - for application runtime
3. **Redis** (port 6379) - for caching and queuing

For Docker deployments, these are automatically started via docker-compose.

For development deployments, you must install and configure these services manually.

## Testing Database Migrations

To test if migrations can be applied:

```bash
# Navigate to server directory
cd server

# Check current migration status
alembic current

# See migration history
alembic history

# Upgrade to latest version
alembic upgrade head

# Downgrade one version (if needed)
alembic downgrade -1
```

## Summary

All issues related to `alembic upgrade head` have been resolved. The main problems were:

1. ✅ Pydantic v2 compatibility issues
2. ✅ Environment variable format issues
3. ✅ Missing imports in model files
4. ✅ SQLAlchemy reserved attribute names
5. ✅ Missing environment template files

The system is now ready for deployment. Ensure you have PostgreSQL, MongoDB, and Redis running before attempting database migrations.
