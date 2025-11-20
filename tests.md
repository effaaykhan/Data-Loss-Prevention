# CyberSentinel DLP – Verification Checklist

Use this cheat-sheet alongside `TESTING_COMMANDS.md` when you run the final pass. Each block lists the commands or UI actions that must succeed.

## 1. Environment & Health
- Fresh build/start: `docker compose build --no-cache && docker compose up -d`
- `curl http://localhost:55000/health` → 200 with JSON payload
- Login API (`/api/v1/auth/login`) returns access + refresh tokens

## 2. Policy & Event API Smoke Tests
1. `GET /api/v1/policies/` and `/api/v1/policies/stats/summary` with `Authorization: Bearer $TOKEN`
2. Policy CRUD cycle (temporary policy):
   - `POST /api/v1/policies/` (clipboard or file type)
   - `PUT /api/v1/policies/{id}`
   - `POST .../{id}/enable` and `/disable`
   - `DELETE .../{id}`
3. Synthetic event submission:
   ```bash
   curl -i -X POST http://localhost:55000/api/v1/events/ \
     -H "Content-Type: application/json" \
     -d '{ "event_id": "qa-cli-001", ... }'
   ```
4. `GET /api/v1/events/?limit=5` → verify `matched_policies` and `policy_action_summaries`

## 3. UI Regression Pass
1. Login at `http://localhost:3000` (admin/admin)
2. Dashboard cards + charts populate without errors
3. Agents page shows Linux + Windows entries once agents are running
4. Policies page:
   - Stats cards: total/active/inactive/violations
   - Full list rendered
   - Run through “Create Policy” wizard, ensure creation succeeds, then delete via API afterward
5. Events page:
   - Use `*` query to load events
   - Open row drawer to view policy + action details

## 4. Agent Runtime Tests
1. Linux agent (`agents/endpoint/linux/agent.py`)
   - Config pointed to `http://localhost:55000/api/v1`
   - Start agent, ensure registration + policy sync succeed (heartbeat logs)
   - Trigger file event in `tmp_linux_policy/` and verify event appears in UI/API
2. Windows agent (`/mnt/d/CyberSentinelAgent/agent.py`)
   - Copy updated code/config before running
   - Confirm file, clipboard, USB monitoring all generate events + action outcomes
3. Policy bundle endpoint check:
   ```
   curl -i -X POST http://localhost:55000/api/v1/agents/{agent_id}/policies/sync \
     -H "Content-Type: application/json" \
     -d '{"platform":"windows","capabilities":{"file_monitoring":true}}'
   ```
   → Should return bundle with `status` (`updated` or `up_to_date`)

## 5. Activate / Deactivate Behavior
1. Create temporary file-system policy targeting `tmp_linux_policy`
2. Send event → ensure `matched_policies` contains the new policy
3. `POST /policies/{id}/disable`
4. Send identical event → confirm only legacy policy matches; disabled policy no longer appears
5. Delete the temporary policy

## 6. Shutdown & Cleanup
- Stop agents (`Ctrl+C` in each terminal / PowerShell)
- `docker compose down`
- Remove any temp policies/events created purely for testing

> Tip: keep a terminal window open with `docker compose logs -f manager` when running the suite to catch stack traces immediately. 


