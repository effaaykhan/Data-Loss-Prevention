# Future Improvements & Fixes

## Local Google Drive Policy
- [ ] **Enhance USB Blocking:** Update the "USB File Transfer Policy" to explicitly support selecting Google Drive paths (e.g., `G:\My Drive`) as "Protected Directories". This will enable the agent to block files copied *from* the local Google Drive *to* a USB stick, fulfilling the "prevention" aspect of the user's request.

## Google Drive Cloud Polling
- [ ] **Celery lazy-load bug:** Occasional `sqlalchemy.exc.MissingGreenlet` thrown when `google_drive_polling` accesses `connection.folders` right after baseline resets. Needs eager loading or async-safe pattern to avoid transient task failures.

## OAuth Flow
- [ ] **Callback error handling:** `/api/v1/google-drive/callback` returns 500 when Google rejects the auth code (valid state + invalid code). Should surface a 4xx with descriptive error instead of internal server error.
