# Current Task Plan - Installer Automation (Windows & Linux)

- [ ] Define installer requirements (auto-clone/download, config handling, service management per OS)
- [ ] Draft Windows installer approach (PowerShell): clone/sparse-checkout windows agent, install deps/venv or bundled exe, configure `agent_config.json`, register as service (NSSM or native), start and verify
- [ ] Draft Linux installer approach (bash): clone/sparse-checkout linux agent, install deps/venv, set config, create systemd service, start and verify
- [ ] Implement scripts and doc updates as needed
- [ ] Smoke test both flows (local paths/ports)
- [ ] Summarize changes and remaining risks

---

# Comprehensive Manual Testing Plan - CyberSentinel DLP

## Testing Overview

This plan covers all features, policy types, actions, and detection patterns in the CyberSentinel DLP application. Each test should be executed manually and results documented.

## Pre-Testing Setup

### 1. Environment Verification
- [ ] Verify all Docker containers are running: `docker compose ps`
- [ ] Check service health: `curl http://localhost:55000/health`
- [ ] Verify dashboard is accessible: http://localhost:3000
- [ ] Login with admin credentials (admin/admin)
- [ ] Verify both agents are running (Windows and Linux)

### 2. Clean State
- [ ] Clear all existing events via UI or API
- [ ] Delete all existing policies (or document current state)
- [ ] Verify agent policy bundles are synced

### 3. Test Files Preparation
- [ ] Verify test files exist in `test_files/` directory:
  - `indian_identifiers.txt` - Indian identifiers (Aadhaar, PAN, IFSC, UPI, etc.)
  - `source_code_patterns.txt` - Source code and API keys in code
  - `api_keys_only.txt` - Various API keys
  - `database_connections.txt` - Database connection strings
  - `mixed_sensitive_data.txt` - Mix of all sensitive data types
  - `PII_sample.txt` - Original PII (SSN, Credit Cards)
- [ ] Create test directories if needed:
  - Windows: `C:\Test`, `C:\Quarantine`, `C:\Sensitive`
  - Linux: `/tmp/test`, `/quarantine`, `/tmp/sensitive`

---

## Part 1: Windows Agent Comprehensive Policy Validation

Goal: Create each policy group sequentially, validate every sub-condition with individual files, then run an “all-in-one” test, and finally clean up (disable/delete) before moving to the next group. Keep the Windows agent console open to capture logs.

### W1. Authentication & Baseline
- [ ] Login to dashboard (admin/admin) and keep session active.
- [ ] Hit `POST /api/v1/auth/login` to confirm token-based access still works.
- [ ] Confirm Windows agent appears as `Active` on Agents page.

### W2. Clipboard Policy – Indian + Source Code Focus
1. **Create Policy**
   - Type: Clipboard
   - Name: `WIN Clipboard – India`
   - Patterns: Aadhaar, PAN, IFSC, Bank Account, Indian Phone, UPI, MICR, DOB, Source Code, API Keys in Source Code
   - Action: Alert
2. **Test Individually (copy content, wait for event, screenshot/classification)**
   - Aadhaar → `indian_identifiers.txt`
   - PAN → same file different line
   - IFSC, Bank Account, Indian Phone, UPI, MICR, DOB → same file (one line at a time)
   - Source Code function → `source_code_patterns.txt`
   - API key in code → same file (“API Keys in Code” section)
3. **Test Legacy Patterns**
   - SSN, Credit Card, Email → `PII_sample.txt`
4. **All-in-one test**
   - Copy entire `mixed_sensitive_data.txt` and verify multi-classification event.
5. **Cleanup**
   - Disable policy, verify no new clipboard events arrive.
   - Delete policy.

### W3. File System Policy – Quarantine/Block
1. **Create Policy**
   - Type: File System
   - Name: `WIN FS – Quarantine`
   - Path: `C:\Test`
   - Extensions: `.txt`, `.pdf`
   - Events: Create/Modify/Delete enabled
   - Action: Quarantine
   - Quarantine Path: `C:\Quarantine`
2. **Test each event**
   - Create: copy `indian_identifiers.txt` into `C:\Test`
   - Modify: edit file, append new PAN line
   - Delete: remove `api_keys_only.txt`
   - Move: move `source_code_patterns.txt` inside a subfolder of `C:\Test`
   - Extension filter: place `.docx` file (should NOT trigger) then rename `database_connections.txt` to `.pdf` (should trigger)
3. **Quarantine verification**
   - Inspect events for `quarantined: true` and path metadata
4. **Block Action spot-check (optional)**
   - Switch action to Block, drop `source_code_patterns.txt`, confirm operation fails/blocked event logged
5. **Cleanup**
   - Delete policy + test files from `C:\Test`

### W4. USB Policies
1. **USB Device Monitoring**
   - Create policy `WIN USB Device`
   - Enable Connect + Disconnect events
   - Plug/unplug USB drive, verify logs
   - Delete policy
2. **USB Transfer – Quarantine**
   - Create policy `WIN USB Transfer`
   - Monitored path `C:\Sensitive`
   - Quarantine path `E:\Quarantine` (or chosen USB quarantine dir)
   - Copy `api_keys_only.txt` from `C:\Sensitive` to USB → should quarantine
   - Copy `database_connections.txt` to confirm second detection
   - Delete policy

### W5. Google Drive Local (Windows mirror)
1. **Create Policy** `WIN GDrive Local`
   - Base Path: `G:\My Drive`
   - Folder: `Sensitive`
   - Extensions: `.txt`, `.docx`
   - Events: Create + Modify
   - Action: Quarantine → path `C:\Quarantine\GDrive`
2. **Tests**
   - Copy `indian_identifiers.txt` into `G:\My Drive\Sensitive`
   - Modify file, verify events show Google Drive path
3. **Cleanup**
   - Delete test files from Drive mirror
   - Delete policy

### W6. Policy Bundle Refresh & Agent Sync
- [ ] Recreate a simple clipboard policy.
- [ ] Click `Refresh Bundles`.
- [ ] Confirm toast + `Last refresh triggered` timestamp.
- [ ] Check Windows agent logs for sync within 60s.
- [ ] Delete policy.

### W7. Windows Event Verification
- [ ] Use Events page filters (`agent.name:"Windows Agent"`).
- [ ] Open random clipboard, file, USB events; verify matched-policy badges & action summary.
- [ ] Clear events to prepare for Linux round (optional).

---

## Part 2: Linux Agent Comprehensive Policy Validation

Replicate Windows coverage, but target Linux paths and ensure Linux agent handles each scenario. Use `/tmp/test`, `/quarantine`, `/mnt/usb`, etc.

### L1. Authentication & Agent Baseline
- [ ] Confirm dashboard session still valid or log back in.
- [ ] Verify Linux agent shows `Active`.
- [ ] Tail Linux agent log (`/tmp/linux_agent.log`) to watch events live.

### L2. Clipboard Policy – Linux
1. **Create Policy** `LIN Clipboard – India`
   - Same patterns/actions as Windows version.
2. **Individual Tests**
   - Use `indian_identifiers.txt`, `source_code_patterns.txt`, `PII_sample.txt` exactly as before (content copy from VS Code/WSL).
3. **Aggregate Test**
   - Copy entire `mixed_sensitive_data.txt`.
4. **Cleanup**
   - Delete clipboard policy.

### L3. File System Policy – Linux
1. **Create Policy** `LIN FS – Quarantine`
   - Path: `/tmp/test`
   - Extensions: `.txt`, `.pdf`
   - Action: Quarantine → `/quarantine`
2. **Tests**
   - Create/Modify/Delete/Move steps identical to Windows but performed inside `/tmp/test`.
   - Extension filter using `.docx` negative case and `.pdf` positive case.
3. **Quarantine verification**
   - Check event metadata + Linux agent logs.
4. **Cleanup**
   - Delete policy and remove files.

### L4. USB Policies – Linux
1. **USB Device Monitoring**
   - Policy `LIN USB Device`
   - Connect/disconnect removable drive (or simulated mount) and verify events.
2. **USB Transfer Quarantine**
   - Policy `LIN USB Transfer`
   - Monitored path `/tmp/sensitive`
   - Quarantine path `/mnt/usb_quarantine`
   - Copy `api_keys_only.txt` & `database_connections.txt`, try moving to mounted USB.
3. **Cleanup**
   - Delete policies after validation.

### L5. Google Drive Local (if Linux-side mirror exists)
- If Linux agent monitors local Drive folders (e.g., `/mnt/GDrive`), repeat the Windows Drive-local steps. Otherwise, skip with note “not applicable on Linux”.

### L6. Linux Policy Refresh & Telemetry
- [ ] Create temp policy, click `Refresh Bundles`, ensure Linux agent syncs and logs `bundle up-to-date`.
- [ ] Delete temp policy.

### L7. Linux Event Review
- [ ] Filter Events page by `agent.name:"Linux Agent"`.
- [ ] Spot-check clipboard/file/USB events for Linux-specific metadata (paths).
- [ ] Clear events if desired.

---

## Part 3: Cross-Cutting Validation & Edge Cases
These steps apply after both agent test passes.

### C1. Event Management & Dashboard
- [ ] Verify dashboard overview cards (events, policies, agents, violations).
- [ ] Ensure Events page search/filter/manual refresh all behave.
- [ ] Use “Clear Logs” and confirm event count resets.

### C2. Quarantine Implementation Deep-Dive
- [ ] Review backend code (`action_executor.py`) to confirm `execute_quarantine`.
- [ ] For the last quarantined event, inspect MongoDB/OpenSearch (if accessible) to ensure `quarantined`, `quarantine_path`, `quarantine_timestamp` persisted.
- [ ] Note limitation: files aren’t physically moved yet.

### C3. Edge Cases
- Invalid policy config → ensure UI validation blocks save.
- Disable policy mid-test → verify no further matches.
- Multiple policies hitting same event → e.g., create duplicate clipboard policies and copy `mixed_sensitive_data.txt`; confirm both actions logged.
- Large clipboard paste (>1 MB) → confirm truncation behavior.
- Special characters/unicode content → verify safe handling.

### C4. Performance/Stress (Optional)
- Rapidly fire 50+ clipboard events (scripted copies) to watch throughput.
- Create many policies (if needed) to observe bundle size + agent sync.

### C5. Documentation Review
- Re-read `README.md`, `INSTALLATION_GUIDE.md`, `TESTING_COMMANDS.md`, `.cursorrules`, `AGENTS.md`, `CHANGELOG.md` to ensure instructions match newly validated behavior.

### C6. Final Cleanup
- [ ] Delete any temporary policies left behind.
- [ ] Clear events/db if desired.
- [ ] Summarize findings + attach logs/screenshots for any failures.

---


## Known Limitations

1. **Quarantine Validation**: Quarantine is implemented (Windows USB/files, Linux files) but still needs fresh end-to-end manual verification on real endpoints, especially USB paths.
2. **Agent Sync**: Policy bundle sync happens every 60 seconds, not instant
3. **Google Drive**: Requires OAuth setup and active Google account

---

## Priority Testing Order

1. **High Priority**: Policy creation, basic detection, alert/log actions
2. **Medium Priority**: File system monitoring, USB monitoring, basic quarantine spot-checks
3. **Low Priority**: Google Drive integration, performance testing, edge cases

---

## Future Work: Quarantine Validation

- [ ] Re-run focused Windows USB/file-system quarantine tests end-to-end:
  - Configure policies with `action: quarantine` and verify files move into `C:\Quarantine`.
  - Confirm events carry `quarantined`, `quarantine_path`, `quarantine_timestamp`, `quarantine_reason`.
- [ ] Validate Linux quarantine enforcement for file policies (and USB if available on the test host) with a dedicated quarantine folder excluded from monitoring.
- [ ] Add or refine automated/regression tests for quarantine metadata persistence and UI presentation.
- [ ] Document operational guidance (cleanup strategy for quarantine folders on Windows/Linux).
