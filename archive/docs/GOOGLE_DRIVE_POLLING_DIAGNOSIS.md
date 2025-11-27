# Google Drive Polling Diagnosis (26 Nov 2025)

## 1. What Events Are Showing Up Right Now?

- Checked the dashboard (`/events`) after rebuilding the frontend with a clean Docker image.
- Recent entries are **all `File` events targeting the same protected folder (`My Drive/Projects/test_files`)** regardless of whether any new file activity occurred.
- Opening the newest event modal shows:
  - **Event Type:** File (no subtype shown in older entries)
  - **User:** `people/105239300797650028719`
  - **Agent:** `gdrive-ecf98f5d-2d93-46f2-8671-7a2df080d1c6`
  - **Description:** `N/A` for older documents (new ones picked up after today will include the action text we added).

## 2. Raw Data Retrieved from Google

MongoDB document example (latest event):

```mongo
{
  "timestamp": ISODate("2025-11-26T07:12:54.867Z"),
  "event_subtype": "file_created",
  "description": "File created: test_files",
  "details.raw_activity": {
    "primaryActionDetail": { "create": { "new": {} } },
    "actions": [{ "detail": { "create": { "new": {} } } }, ...],
    "targets": [{
      "driveItem": {
        "name": "items/1L2E...jxKz",
        "title": "test_files",
        "folder": { "type": "STANDARD_FOLDER" },
        "owner": { "user": { "knownUser": { "personName": "people/..." } } }
      }
    }],
    "timestamp": "2025-11-24T07:29:37.934Z"
  },
  "matched_policies": [
    {
      "policy_name": "testGcloud",
      "matched_rules": [
        { "field": "source", "value": "google_drive_cloud" },
        { "field": "connection_id", "value": "ecf98f5d-..." },
        { "field": "folder_id", "value": ["1L2E...jxKz"] }
      ]
    }
  ]
}
```

**Observations:**
- `google_event_id` is `null`, so our normalizer falls back to a random UUID each time (`event_id = "gdrive-" + uuid4`). This prevents `_is_duplicate` from filtering historic actions—every poll creates fresh IDs.
- The raw `timestamp` embedded in the Google payload is **24 Nov** while the Mongo `timestamp` reflects **the poll time (26 Nov)**; we re-ingest the same historic action each run.

## 3. Current Polling Logic (code references)

1. **Query** (`server/app/services/google_drive_polling.py::_fetch_folder_events`)
   - Body sent to Google:
     ```json
     { "ancestorName": "items/<folder_id>", "pageSize": 50 }
     ```
   - No filter, no time range, no state kept between runs.
   - `nextPageToken` is only for pagination; we treat it as a cursor, but when the response fits in one page there is no token, so we **never advance `last_activity_cursor`**.

2. **Normalization** (`server/app/services/google_drive_event_normalizer.py`)
   - Generates action subtype + severity from `primaryActionDetail`.
   - Builds description string and copies Google folder ID into `folder_id`; protected-folder UUID is stored separately.
   - Event ID fallback is random if Google omits `activity.id`.

3. **Persistence** (`_persist_event`)
   - Processes event through the shared `EventProcessor`.
   - Drops events with no policy match.
   - Inserts the document directly into MongoDB; no time/state stored per folder.

## 4. Why You See Notifications Every Poll

| Root Cause | Effect |
|------------|--------|
| **No time-based filter** – every `query()` call returns the entire activity history for the protected folder. | Each poll replays all historical actions, not just new changes. |
| **`google_event_id` is null** and we substitute a random UUID. | `_is_duplicate` can’t detect repeats; the same historical activity is treated as brand new. |
| **Stored cursor logic expects `nextPageToken`.** For single-page responses it keeps writing `None`, so we never “advance” the cursor. | Even if we attempted to reuse the token, it’s only valid for pagination, not for future delta queries. |

Net effect: **every poll re-ingests the same folder creation/move events from November 24th and generates a new Mongo record**, so the dashboard shows a flood of “File” violations despite no recent changes.

## 5. What We Actually Need

1. **Real cursor = timestamp**  
   - Store the most recent activity timestamp processed (e.g., ISO string) in `GoogleDriveConnection.last_activity_cursor`.
   - Add a `filter` clause before querying: `body["filter"] = f"time >= \"{cursor}\""` or use `timeRange` to limit results.
2. **Deterministic event IDs**  
   - When Google omits `activity.id`, build one from stable fields, e.g. `uuid5(NAMESPACE_DNS, f"{actor}|{target}|{timestamp}|{subtype}")`.
   - That allows `_is_duplicate` to drop repeats even if the API echo occurs.
3. **Optional**: record per-folder checkpoints if different folders are polled independently.

With those changes, we would only notify on *new* file/folder additions, deletions, or modifications occurring inside the protected directories.

## Implemented Fixes – 26 Nov 2025
- Poller now stores the **latest activity timestamp per protected folder** (`last_seen_timestamp`) and queries Drive Activity with `time > "<timestamp>"`, ensuring only new changes are retrieved.
- Event IDs are **deterministic** (Google's `activity.id` or a UUID5 hash of actor+file+timestamp), so duplicate API responses are ignored by `_is_duplicate`.
- `_fetch_folder_events` **filters to actionable subtypes** (`file_created`, `file_modified`, `file_deleted`, `file_moved`, `file_copied`, `file_downloaded`, etc.), preventing noise from comments/shares.
- The dashboard now reflects only policy-matched events; historical Google Drive actions no longer reappear every polling cycle.

