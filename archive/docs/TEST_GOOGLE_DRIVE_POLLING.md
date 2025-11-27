# Testing Google Drive Cloud Polling

## ✅ Current Status

**Polling is working!** We found 36 Google Drive events in MongoDB from the last hour.

## How It Works

### Flow Diagram
```
1. File Created in Protected Google Drive Folder
   ↓
2. Google Drive Activity API detects change
   ↓
3. Celery Beat triggers polling (every 5 minutes)
   ↓
4. Polling Service queries Google Drive Activity API
   ↓
5. Events normalized and processed through DLP pipeline
   ↓
6. Events stored in MongoDB (dlp_events collection)
   ↓
7. Dashboard displays events via /api/v1/events endpoint
```

## Testing Steps

### 1. Create a File in Protected Folder

1. Go to your Google Drive
2. Navigate to a folder that's configured as "protected" in your Google Drive Cloud policy
3. Create a new file (e.g., `test_file.txt`)
4. Add some content (optionally with PII to test policy matching)

### 2. Wait for Polling (or Trigger Manually)

**Option A: Wait for Automatic Polling**
- Polling runs every 5 minutes (configured in `reporting_tasks.py`)
- Wait up to 5 minutes for the next scheduled run

**Option B: Trigger Polling Manually**
```bash
cd /home/vansh/Code/Data-Loss-Prevention
docker compose exec celery-worker python test_polling_manual.py
```

### 3. Verify Events in MongoDB

```bash
# Check for Google Drive events
docker compose exec celery-worker python test_google_drive_events.py
```

Or directly query MongoDB:
```bash
MONGODB_PASSWORD=$(grep "^MONGODB_PASSWORD=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
docker exec cybersentinel-mongodb mongosh -u dlp_user -p "$MONGODB_PASSWORD" \
  --authenticationDatabase admin cybersentinel_dlp \
  --eval "db.dlp_events.find({agent_id: /^gdrive-/}).sort({timestamp: -1}).limit(5).forEach(e => print(JSON.stringify(e, null, 2)))"
```

### 4. Verify Events in Dashboard

1. Open dashboard: http://localhost:3000
2. Login (admin/admin)
3. Go to Events page
4. Filter by source: "google_drive" or look for events with agent_id starting with "gdrive-"
5. Events should show:
   - File name and path
   - Event type (file created, modified, etc.)
   - Timestamp
   - User email
   - Folder information

### 5. Verify via API

```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:55000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Get Google Drive events
curl -s "http://localhost:55000/api/v1/events?limit=10" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -m json.tool | grep -A 5 "gdrive-"
```

## Event Format

Google Drive events are stored with:
- **agent_id**: `gdrive-{connection_id}` (e.g., `gdrive-ecf98f5d-2d93-46f2-8671-7a2df080d1c6`)
- **tags**: `["google_drive", "cloud", "file"]`
- **source**: `google_drive_cloud`
- **event_type**: `file` (or other activity types)
- **file_name**: Name of the file
- **file_path**: Full path in Google Drive (e.g., `My Drive/Projects/test_files`)
- **folder_id**: Google Drive folder ID
- **user_email**: Google account email

## Troubleshooting

### No Events Appearing?

1. **Check if polling is running:**
   ```bash
   docker compose logs celery-worker --tail 50 | grep "Google Drive polling"
   ```

2. **Check for errors:**
   ```bash
   docker compose logs celery-worker --tail 100 | grep -i error
   ```

3. **Verify protected folders are configured:**
   ```bash
   docker compose exec postgres psql -U dlp_user -d cybersentinel_dlp \
     -c "SELECT id, folder_name, folder_id FROM google_drive_protected_folders;"
   ```

4. **Check Google Drive connection status:**
   ```bash
   docker compose exec postgres psql -U dlp_user -d cybersentinel_dlp \
     -c "SELECT id, google_user_email, status, last_polled_at FROM google_drive_connections;"
   ```

5. **Trigger polling manually and check logs:**
   ```bash
   docker compose exec celery-worker python test_polling_manual.py
   docker compose logs celery-worker --tail 20
   ```

### Events Not Showing in Dashboard?

1. **Check API endpoint:**
   ```bash
   curl http://localhost:55000/api/v1/events?limit=5 \
     -H "Authorization: Bearer $TOKEN"
   ```

2. **Check dashboard logs:**
   ```bash
   docker compose logs dashboard --tail 50
   ```

3. **Hard refresh browser** (Ctrl+Shift+R) to clear cache

## Polling Schedule

- **Frequency**: Every 5 minutes
- **Configuration**: `server/app/tasks/reporting_tasks.py` line 54
- **Schedule**: `crontab(minute="*/5")`

To change the interval, modify the crontab expression:
- Every 1 minute: `crontab(minute="*")`
- Every 10 minutes: `crontab(minute="*/10")`
- Every hour: `crontab(minute=0)`

## Expected Behavior

1. **File Created** → Event appears within 5 minutes (or immediately if polling manually)
2. **File Modified** → New event created
3. **File Deleted** → Deletion event created
4. **File Moved** → Move event created

All events go through the DLP policy evaluation pipeline, so if the file contains PII and matches a policy, it will be flagged accordingly.



