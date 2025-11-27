# Google Drive Polling Architecture & Analysis

## Why We're Using Celery

### 1. **Background Task Execution**
- **Non-blocking**: Polling Google Drive API can take time (network I/O, API rate limits)
- **Async processing**: Doesn't block the main FastAPI server from handling HTTP requests
- **Resource isolation**: Celery workers run in separate containers/processes

### 2. **Scheduled Execution**
- **Periodic polling**: Google Drive activity needs to be checked regularly (every 5 minutes per `reporting_tasks.py`)
- **Celery Beat**: Built-in scheduler that triggers tasks on cron-like schedules
- **Reliability**: If a task fails, Celery can retry it automatically

### 3. **Scalability**
- **Horizontal scaling**: Can run multiple worker containers to handle more connections
- **Task queue**: Redis acts as message broker, allowing distributed task execution
- **Load distribution**: Multiple Google Drive connections can be polled in parallel

### 4. **Separation of Concerns**
- **API server**: Handles HTTP requests (fast, stateless)
- **Worker processes**: Handle long-running/background tasks (polling, reporting)
- **Clear boundaries**: Each service has a single responsibility

## What We're Doing in Polling

### Current Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Celery Beat (Scheduler)                                      │
│ - Runs every 5 minutes (crontab: minute="*/5")              │
│ - Triggers: poll_google_drive_activity                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Celery Worker                                                │
│ - Receives task from Redis queue                            │
│ - Executes: poll_google_drive_activity()                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ GoogleDrivePollingService.poll_all_connections()            │
│ 1. Query PostgreSQL for all GoogleDriveConnection records    │
│ 2. For each connection:                                      │
│    - Check if token expired → refresh if needed             │
│    - Load protected folders                                  │
│    - Poll each folder                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ GoogleDrivePollingService._fetch_folder_events()             │
│ 1. Build Google Drive Activity API service client            │
│ 2. Create request body:                                      │
│    {                                                          │
│      "ancestorName": "items/{folder_id}",                    │
│      "pageSize": 50,                                         │
│      "pageToken": "<cursor>" (if resuming)                   │
│    }                                                          │
│ 3. Call: service.activity().query(body=body).execute()      │
│ 4. Handle pagination (loop until no nextPageToken)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Google Drive Activity API (Google's Server)                 │
│ - Returns activity events (file created, modified, deleted)  │
│ - Returns nextPageToken for pagination                      │
│ ⚠️ CURRENTLY FAILING WITH HTTP 500                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Event Normalization & Processing                             │
│ 1. normalize_drive_activity() - Convert Google format       │
│ 2. _persist_event() - Check for duplicates                  │
│ 3. EventProcessor.process_event() - Run through DLP pipeline│
│ 4. Store in MongoDB (dlp_events collection)                 │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **Polling Service** (`google_drive_polling.py`)
- **Purpose**: Orchestrates polling for all connections
- **Key methods**:
  - `poll_all_connections()`: Entry point, iterates all connections
  - `poll_connection()`: Handles one connection (token refresh, folder iteration)
  - `_fetch_folder_events()`: Makes API call, handles pagination
  - `_execute_activity_query()`: Actual Google API call
  - `_persist_event()`: Stores events in MongoDB

#### 2. **Celery Task** (`google_drive_polling_tasks.py`)
- **Purpose**: Wrapper to run async polling in Celery context
- **Function**: `poll_google_drive_activity()` → calls `run_polling()`
- **Async handling**: Uses `asyncio.run()` to execute async polling service

#### 3. **Scheduler** (`reporting_tasks.py`)
- **Celery Beat schedule**: Runs every 5 minutes
- **Task name**: `app.tasks.google_drive_polling_tasks.poll_google_drive_activity`

## Current Issue: HTTP 500 Error

### Symptom
- **Error**: `HttpError 500: Internal error encountered.`
- **Location**: `driveactivity.googleapis.com/v2/activity:query`
- **Context**: Works in debug script from `manager` container, fails in `celery-worker`

### Possible Causes

1. **Request Body Differences**
   - Missing/extra fields
   - Incorrect data types
   - Malformed JSON structure

2. **Environment Differences**
   - Python version mismatch
   - googleapiclient library version
   - Network/proxy settings
   - SSL/TLS configuration

3. **Google API Issues**
   - Rate limiting (unlikely - would be 429)
   - Service account vs OAuth differences
   - Scope/permission issues
   - API quota exceeded

4. **Request Format**
   - URL encoding differences
   - Header differences
   - Authentication token format

## Potential Improvements

### 1. **Error Handling & Retry Logic**
```python
# Add exponential backoff for transient errors
@celery_app.task(bind=True, max_retries=3)
def poll_google_drive_activity(self):
    try:
        # ... polling logic ...
    except HttpError as e:
        if e.resp.status == 500:
            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

### 2. **Request Logging**
- ✅ **DONE**: Added detailed logging of request body
- Capture full request/response for comparison
- Log environment variables that might affect API calls

### 3. **Alternative Approaches**

#### Option A: Webhook Instead of Polling
- **Pros**: Real-time, no polling overhead, more efficient
- **Cons**: Requires public endpoint, more complex setup
- **Use case**: When real-time monitoring is critical

#### Option A: Direct API Integration (No Celery)
- **Pros**: Simpler, fewer moving parts
- **Cons**: Blocks API server, harder to scale
- **Use case**: Low-volume, on-demand polling

#### Option C: Hybrid Approach
- **Scheduled polling** (Celery) for regular checks
- **Webhook** for critical events
- **On-demand API** for manual triggers

### 4. **Connection Pooling**
- Reuse Google API service clients
- Cache credentials (with expiry)
- Reduce API client initialization overhead

### 5. **Incremental Polling**
- Store last successful cursor per folder
- Only fetch new activities since last poll
- Reduce API calls and processing time

### 6. **Parallel Processing**
- Poll multiple folders concurrently (asyncio.gather)
- Poll multiple connections in parallel
- Use Celery's concurrency settings

### 7. **Monitoring & Alerting**
- Track polling success/failure rates
- Alert on consecutive failures
- Dashboard showing polling status per connection

## Next Steps for Debugging

1. **Compare Request Bodies**
   - Run debug script and capture request
   - Run Celery task and capture request
   - Diff the two to find differences

2. **Environment Comparison**
   - Check Python versions in both containers
   - Compare installed packages (`pip list`)
   - Check environment variables

3. **API Client Comparison**
   - Log service object type/version
   - Log credentials object details
   - Compare authentication headers

4. **Test with Minimal Request**
   - Try with just `ancestorName` (no pageSize)
   - Try with different folder IDs
   - Test with different OAuth scopes



