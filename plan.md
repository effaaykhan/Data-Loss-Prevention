# OneDrive Cloud Integration Implementation Plan

## Overview
Implement OneDrive cloud monitoring similar to Google Drive cloud, using Microsoft Graph API for OAuth authentication, delta queries for change tracking, and Celery-based polling. Accepts limitation that file downloads cannot be detected without Microsoft 365 subscription.

## Feature Parity with Google Drive Cloud

**Google Drive Cloud Features:**
1. ✅ OAuth 2.0 authentication
2. ✅ Connection management (multiple accounts per user)
3. ✅ Protected folder selection with folder tree navigation
4. ✅ Per-folder baseline timestamps (`last_seen_timestamp`)
5. ✅ Celery-based polling (every 5 minutes)
6. ✅ Event normalization (Activity API → DLP events)
7. ✅ Deterministic event IDs (prevent duplicates)
8. ✅ Manual polling trigger endpoint
9. ✅ Baseline reset functionality
10. ✅ Policy integration with protected folders

**OneDrive Cloud Features (Same):**
- All of the above, but using Microsoft Graph API instead
- ⚠️ **Limitation**: File downloads NOT detectable (requires M365 subscription)

## Implementation Structure

### Backend Components

```
server/app/
├── models/
│   └── onedrive.py                    # OneDriveConnection, OneDriveProtectedFolder
├── services/
│   ├── onedrive_oauth.py              # OAuth flow (MSAL instead of google-auth)
│   ├── onedrive_polling.py            # Graph API delta queries (instead of Activity API)
│   └── onedrive_event_normalizer.py   # Graph API → DLP event format
├── api/v1/
│   └── onedrive.py                    # REST endpoints (same structure as google_drive.py)
├── tasks/
│   └── onedrive_polling_tasks.py      # Celery task (same pattern)
└── utils/
    └── policy_transformer.py          # Add _transform_onedrive_cloud_config()
```

### Frontend Components

```
dashboard/src/
├── components/
│   ├── policies/
│   │   └── OneDriveCloudPolicyForm.tsx    # Similar to GoogleDriveCloudPolicyForm.tsx
│   └── onedrive/
│       └── ProtectedFolderSelector.tsx     # Similar to Google Drive version
├── types/
│   └── policy.ts                          # Add OneDriveCloudConfig
├── lib/
│   └── api.ts                              # Add OneDrive API functions
└── utils/
    └── policyUtils.ts                      # Add default config
```

## Implementation Checklist

### Phase 1: Backend Models & Database
- [ ] Create `server/app/models/onedrive.py` with OneDriveConnection and OneDriveProtectedFolder models
- [ ] Create Alembic migration `add_onedrive_tables.py`
- [ ] Test database schema

### Phase 2: OAuth Service
- [ ] Create `server/app/services/onedrive_oauth.py`
- [ ] Implement MSAL-based OAuth flow
- [ ] Add OAuth configuration to `server/app/core/config.py`
- [ ] Add `msal` to `server/requirements.txt`
- [ ] Test OAuth flow

### Phase 3: Polling Service
- [ ] Create `server/app/services/onedrive_polling.py`
- [ ] Implement Graph API delta query polling
- [ ] Create `server/app/services/onedrive_event_normalizer.py`
- [ ] Test polling and event normalization

### Phase 4: Celery Tasks
- [ ] Create `server/app/tasks/onedrive_polling_tasks.py`
- [ ] Add to Celery beat schedule in `reporting_tasks.py`
- [ ] Test Celery task execution

### Phase 5: API Endpoints
- [ ] Create `server/app/api/v1/onedrive.py`
- [ ] Implement all REST endpoints (connect, callback, connections, folders, etc.)
- [ ] Test API endpoints

### Phase 6: Policy Integration
- [ ] Add `_transform_onedrive_cloud_config()` to `policy_transformer.py`
- [ ] Test policy matching with OneDrive events

### Phase 7: Frontend Types
- [ ] Add `OneDriveCloudConfig` to `dashboard/src/types/policy.ts`
- [ ] Add default config to `dashboard/src/utils/policyUtils.ts`

### Phase 8: Frontend API Client
- [ ] Add OneDrive API functions to `dashboard/src/lib/api.ts`
- [ ] Test API client functions

### Phase 9: Frontend Components
- [ ] Create `dashboard/src/components/policies/OneDriveCloudPolicyForm.tsx`
- [ ] Create `dashboard/src/components/onedrive/ProtectedFolderSelector.tsx`
- [ ] Integrate into `PolicyCreatorModal.tsx`
- [ ] Add to `PolicyTypeSelector.tsx`
- [ ] Test UI components

### Phase 10: Testing & Documentation
- [ ] Unit tests for OAuth service
- [ ] Unit tests for polling service
- [ ] Unit tests for event normalizer
- [ ] Integration tests for API endpoints
- [ ] Update documentation

## Key Differences from Google Drive

| Feature | Google Drive | OneDrive |
|---------|-------------|----------|
| **OAuth Library** | `google-auth-oauthlib` | `msal` |
| **API** | Drive Activity API | Graph API Delta Queries |
| **Event Source** | Activity feed | Delta changes |
| **Download Detection** | ✅ Yes | ❌ No (limitation) |
| **Baseline** | Timestamp | Timestamp + Delta Token |
| **Token Refresh** | Google OAuth | Microsoft Identity Platform |

## Configuration

**Environment Variables (.env):**
```bash
ONEDRIVE_CLIENT_ID=your-azure-app-client-id
ONEDRIVE_CLIENT_SECRET=your-azure-app-client-secret
ONEDRIVE_REDIRECT_URI=http://YOUR_SERVER_IP:55000/api/v1/onedrive/callback
ONEDRIVE_TENANT_ID=common
```

**Azure App Registration:**
1. Register app in Azure Portal
2. Redirect URI: `http://YOUR_SERVER:55000/api/v1/onedrive/callback`
3. API permissions: `Files.Read.All`, `User.Read`, `offline_access`
4. Create client secret

## Event Types Detected

- ✅ `file_created` - New file uploaded/created
- ✅ `file_modified` - File content changed (with hybrid detection using Redis + ETag comparison)
- ✅ `file_deleted` - File removed
- ✅ `file_moved` - File moved/renamed
- ✅ `file_copied` - File copied (if detectable)
- ❌ `file_downloaded` - NOT available (limitation)

## Hybrid Modification Detection (December 25, 2025)

**Problem:** Microsoft Graph API delta queries sometimes report file modifications as "created" + "deleted" events instead of a single "updated" event.

**Solution:** Hybrid approach implemented:
- **Delta API for Deletions & Creations:** Uses delta API as-is (reliable)
- **Metadata Comparison for Modifications:** 
  - Stores file state (ETag, version, lastModifiedDateTime) in Redis
  - When delta reports "updated" or suspected modification, verifies by comparing current ETag with stored state
  - Accurately detects real file content modifications vs. metadata-only changes
  - Prevents false create+delete pairs when users modify file content

**Implementation:**
- Redis file state storage: `onedrive:file_state:{connection_id}:{file_id}` (90-day TTL)
- `_get_file_state()` and `_store_file_state()` methods for Redis operations
- `_fetch_file_metadata()` method to get current file ETag/version from Graph API
- `_detect_file_modification()` method to verify modifications via ETag comparison
- Enhanced delta processing to detect suspected modifications (created but file_id exists in Redis)
- Graceful fallback to delta-only mode if Redis is unavailable

**Files Modified:**
- `server/app/services/onedrive_polling.py` - Added Redis helpers, metadata fetching, modification detection
- `server/app/services/onedrive_event_normalizer.py` - Added ETag/version extraction

## Estimated Effort

- Backend: ~1,500 lines of code, 8 files
- Frontend: ~600 lines of code, 3 files
- Total: ~2,100 lines, 11 files
- Time: 4-5 days
