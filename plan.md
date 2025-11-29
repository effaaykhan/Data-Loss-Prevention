## Current Task: Fix Policies UI “Refresh Bundles” button

- [x] Reproduce dashboard issue (inspect React query + button handler).
- [x] Identify missing user feedback (no toast/inline status) causing button to appear broken.
- [x] Implement frontend fix (global Toaster + inline “last refresh” timestamp) and rebuild dashboard.
- [x] Verify via browser that clicking the button shows success messaging and triggers backend invalidation (events observed in manager logs).
