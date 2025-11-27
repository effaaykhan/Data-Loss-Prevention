### Phase 6: Cloud Policy Form & Protected Folder Selection

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

## Current Status: Phase 8 - End-to-End Testing

### Phase 1 Tasks (Completed ✅)
- [x] Backend policy type support
- [x] Frontend policy form
- [x] Agent integration
- [x] Event processing
- [x] Testing

### Phase 2 Tasks (Completed ✅)
- [x] Alembic migration for Google Drive tables (`google_drive_connections`, `google_drive_protected_folders`)
- [x] SQLAlchemy models for Google Drive entities with helpers (token encryption, relationships)
- [x] Basic migration/model smoke tests

### Phase 3 Tasks (Completed ✅)
- [x] Add Google OAuth service module (`server/app/services/google_drive_oauth.py`)
- [x] Wire dependencies & env vars
- [x] Build API router (`server/app/api/v1/google_drive.py`)
- [x] Register router in `app/main.py`
- [x] Frontend connection test button (Settings page)
- [x] Fix OAuth scopes for user profile

### Phase 4 Tasks (Completed ✅)
- [x] Implement polling service (`server/app/services/google_drive_polling.py`)
- [x] Build normalizer (`server/app/services/google_drive_event_normalizer.py`)
- [x] Add persistence hook
- [x] Unit/integration tests for polling

### Phase 5 Tasks (Completed ✅)
- [x] Create Celery task (`google_drive_polling_tasks.py`)
- [x] Add task to Celery Beat schedule (`reporting_tasks.py`)
- [x] Update Docker Compose with Celery services
- [x] Verify task execution

### Phase 6 Tasks (Completed ✅)
- [x] Update policy types interface
- [x] Create ProtectedFolderSelector component
- [x] Create PollingIntervalSettings component (Merged into Form)
- [x] Create GoogleDriveCloudPolicyForm
- [x] Update backend policy transformers (Also part of Phase 7)

### Phase 7 Tasks (Completed ✅)
- [x] Integrate Google Drive configs into Policy Transformer
- [x] Update Database Policy Evaluator to handle Cloud events
- [x] Implement folder synchronization logic (`sync_google_drive_folders`) in Policies API
- [x] Verify policy creation and DB persistence

### Phase 8 Tasks (Completed ✅)
- [x] Fix `service.activities()` bug in polling logic
- [x] Fix UI styling (Dark mode, Polling presets)
- [x] Verify Polling Task execution (Runs successfully)
- [x] Verify Events appear in Dashboard (Policy-filtered events confirmed)

### Phase 9 Tasks (Completed ✅)
- [x] Store per-folder activity timestamps and filter Drive Activity queries
- [x] Generate deterministic Google Drive event identifiers to avoid duplicates
- [x] Limit cloud monitoring to create/update/delete/move/copy/download actions
- [x] Update documentation and automated tests for the new polling behavior

### Phase 10: Cloud Baseline Controls
- [x] Initialize protected-folder baselines at selection time
- [x] Enforce per-folder baselines with skip-and-touch logic in the poller
- [x] Add API & UI to display/reset Google Drive monitoring baselines
- [ ] Document baseline workflow in `POLLING_ARCHITECTURE.md` / `GOOGLE_DRIVE_POLLING_DIAGNOSIS.md`

### Phase 11: Manual Drive Refresh
- [x] Expose FastAPI endpoint that triggers an immediate Google Drive poll (enqueues Celery task)
- [x] Add dashboard Events page button to call that endpoint and then refetch event data
- [x] Ensure refresh falls back to normal event reload for non-GDrive policies