# Google Drive Monitoring Integration - Phased Implementation

## Overview
Implement two new policy types for Google Drive monitoring in sequential phases:
- **Phase 1**: Local Google Drive Monitoring (Windows only) - Monitor G:\ drive using existing file system monitoring
- **Phases 2-8**: Cloud-based Google Drive Monitoring - OAuth-based polling system for Drive Activity API

---

## Phase 1: Local Google Drive Monitoring (Windows)

### Goal
Enable monitoring of Windows G:\ drive (Google Drive desktop app sync folder) using existing file system monitoring infrastructure.

### 1.1 Backend Policy Type Support

**Files to Modify:**
- `server/app/models/policy.py` - Add `google_drive_local_monitoring` to policy type enum/validation
- `server/app/utils/policy_transformer.py` - Add `_transform_google_drive_local_config()` function
- `server/app/policies/agent_policy_transformer.py` - Add platform support mapping

**Policy Config Format:**
```typescript
interface GoogleDriveLocalConfig {
  basePath: string  // Default: "G:\\"
  monitoredFolders: string[]  // Subfolders within G:\ to monitor
  fileExtensions?: string[]
  events: {
    create: boolean
    modify: boolean
    delete: boolean
    move: boolean
    copy: boolean
  }
  action: 'alert' | 'quarantine' | 'block' | 'log'
  quarantinePath?: string
}
```

### 1.2 Frontend Policy Form

**New Files:**
- `dashboard/src/types/policy.ts` - Add `GoogleDriveLocalConfig` type
- `dashboard/src/components/policies/GoogleDriveLocalPolicyForm.tsx` - Form component

**Files to Modify:**
- `dashboard/src/components/policies/PolicyTypeSelector.tsx` - Add "Google Drive (Local)" option
- `dashboard/src/components/policies/PolicyCreatorModal.tsx` - Add form rendering
- `dashboard/src/utils/policyUtils.ts` - Add validation

### 1.3 Agent Integration (Windows)

**Files to Modify:**
- `agents/endpoint/windows/agent.py` - Add G:\ drive monitoring support

### 1.4 Event Processing

**Files to Modify:**
- `server/app/policies/database_policy_evaluator.py` - Ensure it handles `google_drive_local_monitoring` policies
- `server/app/api/v1/events.py` - Accept events with `source: "google_drive_local"`

### 1.5 Testing Phase 1

**Test Scenarios:**
1. Create Google Drive local monitoring policy via UI
2. Verify policy appears in agent policy sync
3. Create/modify/delete file in G:\ monitored folder
4. Verify event appears in dashboard with correct source tag
5. Verify policy evaluation works (action execution)
6. Test with multiple monitored folders
7. Test file extension filtering
8. Test event type filtering

**Validation Checklist:**
- [ ] Policy creation form works
- [ ] Policy syncs to Windows agent
- [ ] Agent monitors G:\ drive correctly
- [ ] Events are created with `source: "google_drive_local"`
- [ ] Events appear in dashboard
- [ ] Policy evaluation triggers correct actions
- [ ] File extension filtering works
- [ ] Event type filtering works

---

## Phase 2: Cloud Google Drive Monitoring - Database & Models

### Goal
Set up database schema and models for storing Google Drive OAuth connections and protected folders.

### 2.1 Database Schema

**New Alembic Migration:**
- `server/alembic/versions/XXXX_add_google_drive_tables.py`

**Tables:**
- `google_drive_connections` - Store OAuth tokens and connection metadata
- `google_drive_protected_folders` - Store protected folder selections per connection

### 2.2 SQLAlchemy Models

**New File:**
- `server/app/models/google_drive.py`

### 2.3 Testing Phase 2

**Test Scenarios:**
- Run migration successfully
- Create connection and folder records
- Test relationships and cascade delete

---

## Phase 3: OAuth Service & API Endpoints

### Goal
Implement Google OAuth flow for users to connect their Google Drive accounts.

### 3.1 OAuth Service

**New File:**
- `server/app/services/google_drive_oauth.py`

**Dependencies:**
- Add `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client` to requirements.txt

**Environment Variables:**
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`

### 3.2 API Endpoints

**New File:**
- `server/app/api/v1/google_drive.py`

**Endpoints:**
- `POST /api/v1/google-drive/connect` - Initiate OAuth
- `GET /api/v1/google-drive/callback` - OAuth callback
- `GET /api/v1/google-drive/connections` - List connections
- `DELETE /api/v1/google-drive/connections/{id}` - Disconnect

### 3.3 Frontend OAuth UI

**New Files:**
- `dashboard/src/components/google-drive/GoogleDriveConnectionManager.tsx`

### 3.4 Testing Phase 3

**Test Scenarios:**
- OAuth flow end-to-end
- Token storage and refresh
- Connection management

---

## Phase 4: Drive Activity Polling Service

### Goal
Implement polling service to query Google Drive Activity API for changes in protected folders.

### 4.1 Polling Service

**New File:**
- `server/app/services/google_drive_polling.py`

### 4.2 Event Normalizer

**New File:**
- `server/app/services/google_drive_event_normalizer.py`

### 4.3 Testing Phase 4

**Test Scenarios:**
- Poll protected folders
- Event normalization
- Error handling

---

## Phase 5: Celery Polling Tasks & Scheduling

### Goal
Set up background polling tasks with configurable intervals.

### 5.1 Celery Tasks

**New File:**
- `server/app/tasks/google_drive_polling_tasks.py`

### 5.2 Celery Beat Schedule

**Files to Modify:**
- `server/app/tasks/reporting_tasks.py` - Add polling schedule

### 5.3 Testing Phase 5

**Test Scenarios:**
- Scheduled polling works
- Custom intervals work
- Rate limiting

---

## Phase 6: Cloud Policy Form & Protected Folder Selection

### Goal
Create frontend UI for cloud-based Google Drive monitoring policy creation.

### 6.1 Policy Type & Config

**Files to Modify:**
- `dashboard/src/types/policy.ts` - Add `GoogleDriveCloudConfig`

### 6.2 Protected Folder Selector

**New File:**
- `dashboard/src/components/google-drive/ProtectedFolderSelector.tsx`

### 6.3 Polling Interval Settings

**New File:**
- `dashboard/src/components/google-drive/PollingIntervalSettings.tsx`

### 6.4 Cloud Policy Form

**New File:**
- `dashboard/src/components/policies/GoogleDriveCloudPolicyForm.tsx`

### 6.5 Backend Policy Transformer

**Files to Modify:**
- `server/app/utils/policy_transformer.py` - Add cloud config transformer
- `server/app/policies/agent_policy_transformer.py` - Add platform support

### 6.6 Testing Phase 6

**Test Scenarios:**
- Create cloud monitoring policy
- Select protected folders
- Configure polling interval

---

## Phase 7: Event Processing Integration

### Goal
Integrate Google Drive cloud events into existing DLP event processing pipeline.

### 7.1 Event Ingestion

**Files to Modify:**
- `server/app/api/v1/events.py`
- `server/app/services/event_processor.py`
- `server/app/policies/database_policy_evaluator.py`

### 7.2 Polling Integration

**Files to Modify:**
- `server/app/tasks/google_drive_polling_tasks.py`

### 7.3 Policy Evaluation

**Files to Modify:**
- `server/app/policies/database_policy_evaluator.py`

### 7.4 Testing Phase 7

**Test Scenarios:**
- Polling creates events
- Events appear in dashboard
- Policy evaluation works

---

## Phase 8: End-to-End Testing & Polish

### Goal
Comprehensive testing of both local and cloud monitoring, plus UI polish.

### 8.1 Integration Testing

**Test Scenarios:**
- Local monitoring end-to-end
- Cloud monitoring end-to-end
- Mixed scenarios
- Error handling

### 8.2 UI Polish

**Improvements:**
- Loading states
- Error messages
- Status indicators
- Event display enhancements

### 8.3 Documentation

**Update:**
- `.cursorrules` - Add Google Drive monitoring notes
- `README.md` - Document new policy types
- `TESTING_COMMANDS.md` - Add testing steps

### 8.4 Final Validation

**Checklist:**
- [ ] Local monitoring works end-to-end
- [ ] Cloud monitoring works end-to-end
- [ ] OAuth flow smooth
- [ ] Polling runs on schedule
- [ ] Events appear in dashboard
- [ ] Policy evaluation works
- [ ] Error handling robust
- [ ] UI polished

---

## Current Status: Phase 1 - In Progress

### Phase 1 Tasks
- [ ] Backend policy type support
- [ ] Frontend policy form
- [ ] Agent integration
- [ ] Event processing
- [ ] Testing
