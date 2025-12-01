Test Files Directory
====================

This folder contains sample files for testing DLP policies.

Files:
- `indian_identifiers.txt` - Contains Indian identifiers (Aadhaar, PAN, IFSC, UPI, etc.)
- `source_code_patterns.txt` - Contains source code patterns and API keys in code
- `mixed_sensitive_data.txt` - Contains mix of all sensitive data types
- `api_keys_only.txt` - Contains various API keys
- `database_connections.txt` - Contains database connection strings
- `PII_sample.txt` - Original PII sample file (SSN, Credit Cards)

Usage:
1. For File System Monitoring: Copy files to monitored directory (e.g., C:\Test or /tmp/test)
2. For Google Drive Local: Copy files to G:\My Drive\test_files
3. For Clipboard Testing: Open files and copy content to clipboard
4. For USB Transfer: Copy files to USB drive

Each file is designed to trigger specific classification patterns when processed by DLP policies.
