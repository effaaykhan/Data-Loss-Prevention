# Clipboard Testing Guide - Indian Identifiers & Source Code Detection

## Current Status

### ✅ Agents Running
- **Windows Agent**: `windows-agent-001` (Active)
- **Linux Agent**: `097bec38-8710-4252-b2f8-b6d816e2a599` (Active)

### ✅ Policies Created
1. **Test Indian Aadhaar Policy** - Clipboard Monitoring (aadhaar pattern)
2. **Test PAN Detection Policy** - Clipboard Monitoring (pan pattern)
3. **Test Source Code Detection Policy** - Clipboard Monitoring (source_code_content, api_key_in_code)
4. **Test IFSC Detection Policy** - Clipboard Monitoring (ifsc pattern)

## PowerShell Commands for Windows Clipboard Testing

### Test Aadhaar Detection
```powershell
# Copy Aadhaar number to clipboard
Set-Clipboard -Value "My Aadhaar number is 1234 5678 9012"

# Alternative method
"1234 5678 9012" | Set-Clipboard
```

### Test PAN Detection
```powershell
# Copy PAN number to clipboard
Set-Clipboard -Value "PAN Number: ABCDE1234F"

# Alternative method
"ABCDE1234F" | Set-Clipboard
```

### Test IFSC Detection
```powershell
# Copy IFSC code to clipboard
Set-Clipboard -Value "Bank IFSC: SBIN0001234"
```

### Test UPI ID Detection
```powershell
# Copy UPI ID to clipboard
Set-Clipboard -Value "UPI ID: user@paytm"
```

### Test Source Code Detection
```powershell
# Copy source code to clipboard
Set-Clipboard -Value "function connectDB() { const conn = 'jdbc:mysql://localhost:3306/mydb'; }"
```

### Test API Key in Code Detection
```powershell
# Copy API key in code to clipboard
Set-Clipboard -Value "api_key: 'AKIAIOSFODNN7EXAMPLE'"
```

### Test Database Connection String Detection
```powershell
# Copy database connection string to clipboard
Set-Clipboard -Value "jdbc:mysql://localhost:3306/mydb?user=root&password=secret"
```

### Test Multiple Patterns
```powershell
# Copy content with multiple patterns
Set-Clipboard -Value "Aadhaar: 1234 5678 9012, PAN: ABCDE1234F, IFSC: SBIN0001234"
```

## Linux Clipboard Testing Commands

### Test Aadhaar Detection
```bash
# Using xclip (if installed)
echo "My Aadhaar number is 1234 5678 9012" | xclip -selection clipboard

# Using xsel (if installed)
echo "1234 5678 9012" | xsel --clipboard
```

### Test PAN Detection
```bash
echo "PAN Number: ABCDE1234F" | xclip -selection clipboard
```

### Test IFSC Detection
```bash
echo "Bank IFSC: SBIN0001234" | xclip -selection clipboard
```

### Test Source Code Detection
```bash
echo "function connectDB() { const conn = 'jdbc:mysql://localhost:3306/mydb'; }" | xclip -selection clipboard
```

## Verification Steps

### 1. Check Events in Dashboard
- Navigate to: http://localhost:3000/events
- Search for: `event.type:"clipboard"`
- Look for events with classification labels: `AADHAAR`, `PAN`, `IFSC`, `UPI_ID`, `SOURCE_CODE`, `API_KEY_IN_CODE`, `DATABASE_CONNECTION`

### 2. Check Policies
- Navigate to: http://localhost:3000/policies
- Verify all 4 policies are active
- Check violation counts

### 3. Check Agent Logs

**Windows Agent:**
- Check agent terminal output for clipboard events
- Look for: "Clipboard event detected" or similar messages

**Linux Agent:**
```bash
tail -f /tmp/linux_agent.log | grep -i clipboard
```

### 4. Check Backend Logs
```bash
docker compose logs manager --tail 50 | grep -E "(AADHAAR|PAN|IFSC|UPI|SOURCE_CODE|API_KEY|DATABASE)"
```

## Expected Behavior

1. **Agent Detection**: When clipboard content matches a pattern, the agent should:
   - Detect the pattern
   - Send event to backend API
   - Log the detection

2. **Backend Processing**: The backend should:
   - Classify the event (add classification labels)
   - Match against active policies
   - Execute policy actions (alert/log/block/quarantine)
   - Store event in MongoDB

3. **UI Display**: Events should appear in:
   - Events page with correct classification badges
   - Policy violation counts updated
   - Event details showing matched patterns

## Test Scenarios

### Scenario 1: Aadhaar Detection
1. Copy "1234 5678 9012" to clipboard
2. Agent detects Aadhaar pattern
3. Event created with `AADHAAR` classification
4. "Test Indian Aadhaar Policy" matches
5. Alert action triggered

### Scenario 2: PAN Detection
1. Copy "ABCDE1234F" to clipboard
2. Agent detects PAN pattern
3. Event created with `PAN` classification
4. "Test PAN Detection Policy" matches
5. Alert action triggered

### Scenario 3: Source Code Detection
1. Copy "function myFunction()" to clipboard
2. Agent detects source code pattern
3. Event created with `SOURCE_CODE` classification
4. "Test Source Code Detection Policy" matches
5. Alert action triggered

### Scenario 4: Multiple Patterns
1. Copy content with multiple patterns (e.g., Aadhaar + PAN)
2. Agent detects all patterns
3. Event created with multiple classification labels
4. Multiple policies match
5. All actions triggered

## Troubleshooting

### Events Not Appearing
1. Check agent is running: `docker compose ps` or check agent terminal
2. Check agent logs for errors
3. Verify policies are enabled in dashboard
4. Check backend logs: `docker compose logs manager --tail 50`

### Patterns Not Detected
1. Verify pattern regex in `server/app/services/event_processor.py`
2. Check pattern is in `dashboard/src/utils/policyUtils.ts`
3. Verify policy has pattern selected in UI
4. Test pattern directly with regex tester

### Agent Not Sending Events
1. Check agent configuration: `agent_config.json`
2. Verify API endpoint is correct
3. Check network connectivity
4. Review agent logs for connection errors




