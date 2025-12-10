# Future TODOs - CyberSentinel DLP

## Quarantine Implementation (Agents + Backend)

- **Current state**: Backend and dashboard handle quarantine metadata; Windows agent supports quarantine moves for USB/file paths; Linux agent now supports quarantine for file policies with a configurable folder (excluded from monitoring).
- **Remaining gaps**:
  - End-to-end validation on real endpoints (Windows USB/files; Linux files, USB if available) to confirm files are relocated and events carry quarantine metadata.
  - Additional regression/automation coverage for quarantine fields.
  - Operational guidance for cleaning/rotating quarantine folders.
  - Google Drive cloud/local flows still metadata-only (no physical move).












