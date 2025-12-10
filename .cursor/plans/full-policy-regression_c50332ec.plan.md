---
name: full-policy-regression
overview: Iteratively recreate and E2E test all non-GDrive policy types on Linux then Windows, deleting after each test.
todos:
  - id: prep-clean
    content: Delete all policies; note agent IDs
    status: completed
  - id: linux-fs
    content: Create/test/delete Linux FS quarantine policy
    status: completed
    dependencies:
      - prep-clean
  - id: linux-usb-transfer
    content: Create/test/delete Linux USB transfer policy
    status: completed
    dependencies:
      - linux-fs
  - id: linux-usb-device
    content: Create/test/delete Linux USB device policy
    status: completed
    dependencies:
      - linux-usb-transfer
  - id: linux-clipboard
    content: Create/test/delete Linux clipboard policy
    status: completed
    dependencies:
      - linux-usb-device
  - id: windows-fs
    content: Create/test/delete Windows FS quarantine policy
    status: in_progress
    dependencies:
      - linux-clipboard
  - id: windows-usb-transfer
    content: Create/test/delete Windows USB transfer policy
    status: pending
    dependencies:
      - windows-fs
  - id: windows-usb-device
    content: Create/test/delete Windows USB device policy
    status: pending
    dependencies:
      - windows-usb-transfer
  - id: windows-clipboard
    content: Create/test/delete Windows clipboard policy
    status: pending
    dependencies:
      - windows-usb-device
  - id: validate-report
    content: Validate bundles/events; report results
    status: pending
    dependencies:
      - windows-clipboard
---

# Full Policy Regression (non-GDrive)

1) Prep & cleanup

- Delete all existing policies. Note agent IDs for Linux (current running) and Windows (`windows-agent-001`).

2) Linux policy round (create → test → delete per type)

- File System Monitoring (quarantine): monitor `/home/vansh/Documents`; action quarantine to `/home/vansh/quarantine`; verify file moved and event `quarantined:true`.
- USB File Transfer (block): monitor `/tmp/sensitive`; copy to USB path (if available); expect block/quarantine per action; verify event.
- USB Device Monitoring (alert/log): plug/unplug detection if available; otherwise simulate via API/log; verify event recorded.
- Clipboard Monitoring: copy sample sensitive text; verify event captured with content snippet.
- For each: validate events API fields (matched_policies, action summaries, no errors), then delete the policy.

3) Windows policy round (create → test → delete per type)

- File System Monitoring (quarantine): monitor `C:\Users\Public\Documents`; action quarantine to `C:\Quarantine`; verify move + event metadata.
- USB File Transfer (quarantine): monitor `C:\Users\Public\Documents`; copy to E:\; verify destination removed, file in quarantine, event `quarantined:true`.
- USB Device Monitoring (alert/log): connect/disconnect USB; verify events.
- Clipboard Monitoring: copy sensitive text; verify event content.
- For each: validate via events API and dashboard badges (if time), then delete the policy.

4) Regression/validation

- After each OS round, confirm no residual policies; bundles sync (version change) on next sync per agent.
- Ensure action summaries show success (no `/quarantine` errors), and quarantine paths match policy.

5) Report

- Summarize pass/fail per policy type (Linux, Windows) with any issues to follow up.