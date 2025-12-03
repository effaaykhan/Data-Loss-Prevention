# Future TODOs - CyberSentinel DLP

## Quarantine Implementation (Agents + Backend)

- **Problem**: `execute_quarantine` in `server/app/actions/action_executor.py` only records metadata (`quarantined`, `quarantine_path`, `quarantine_timestamp`) and explicitly does **not** move or encrypt files yet. Windows/Linux endpoint agents also do not physically relocate files for policies with `action: "quarantine"`.
- **Impact**:
  - UI suggests that files will be “moved to quarantine”, but the actual behavior is logical tagging only.
  - To avoid misleading behavior, quarantine has been temporarily removed as a selectable action from:
    - File System policies
    - USB File Transfer policies
    - Google Drive (Local) policies
- **Target Behavior**:
  - For agent-managed paths (Windows/Linux):
    - Safely move matching files into a configured quarantine directory (per-policy or global), with optional encryption.
    - Record original path, quarantined path, and reason in the event.
  - For backend-only flows (e.g., Google Drive cloud):
    - Optionally copy/move files into a restricted bucket/folder instead of only tagging.
  - Ensure robust error handling (permissions, locked files, partial moves) and audit logging.
- **Follow-ups**:
  - Re-enable `quarantine` in `dashboard/src/types/policy.ts` and policy forms.
  - Update `TESTING_COMMANDS.md` and `plan.md` with end-to-end quarantine test cases once implemented.





