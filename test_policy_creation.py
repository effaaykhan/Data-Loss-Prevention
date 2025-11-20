#!/usr/bin/env python3
"""
Test script to create a policy via API
"""
import requests
import json
import time

BASE_URL = "http://localhost:55000/api/v1"
USERNAME = "admin"
PASSWORD = "admin"
TIMEOUT = 10  # 10 second timeout

def get_auth_token(username, password):
    print(f"[DEBUG] Starting authentication...")
    login_url = f"{BASE_URL}/auth/login"
    print(f"[DEBUG] Login URL: {login_url}")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"username": username, "password": password}
    print(f"[DEBUG] Sending POST request to {login_url}...")
    start_time = time.time()
    try:
        response = requests.post(login_url, headers=headers, data=data, timeout=TIMEOUT)
        elapsed = time.time() - start_time
        print(f"[DEBUG] Login request completed in {elapsed:.2f}s")
        print(f"[DEBUG] Status Code: {response.status_code}")
        response.raise_for_status()
        token = response.json()["access_token"]
        print(f"[DEBUG] Token received: {token[:20]}...")
        return token
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timed out after {TIMEOUT}s")
        raise
    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        raise

def get_policies(token):
    print(f"[DEBUG] Fetching policies...")
    policies_url = f"{BASE_URL}/policies/"
    print(f"[DEBUG] Policies URL: {policies_url}")
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[DEBUG] Sending GET request...")
    start_time = time.time()
    try:
        response = requests.get(policies_url, headers=headers, timeout=TIMEOUT)
        elapsed = time.time() - start_time
        print(f"[DEBUG] GET request completed in {elapsed:.2f}s")
        print(f"[DEBUG] Status Code: {response.status_code}")
        response.raise_for_status()
        policies = response.json()
        print(f"[DEBUG] Received {len(policies)} policies")
        return policies
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timed out after {TIMEOUT}s")
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get policies: {e}")
        raise

def create_policy(token, policy_data):
    print(f"[DEBUG] Creating policy...")
    policies_url = f"{BASE_URL}/policies/"
    print(f"[DEBUG] Policies URL: {policies_url}")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print(f"[DEBUG] Request headers: {headers}")
    print(f"[DEBUG] Policy data: {json.dumps(policy_data, indent=2)}")
    print(f"[DEBUG] Sending POST request (timeout={TIMEOUT}s)...")
    start_time = time.time()
    try:
        response = requests.post(policies_url, headers=headers, json=policy_data, timeout=TIMEOUT)
        elapsed = time.time() - start_time
        print(f"[DEBUG] POST request completed in {elapsed:.2f}s")
        print(f"[DEBUG] Status Code: {response.status_code}")
        print(f"[DEBUG] Response Headers: {dict(response.headers)}")
        print(f"[DEBUG] Response Text (first 500 chars): {response.text[:500]}")
        response.raise_for_status()
        result = response.json()
        print(f"[DEBUG] Response JSON parsed successfully")
        return result
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timed out after {TIMEOUT}s")
        raise
    except Exception as e:
        print(f"[ERROR] Failed to create policy: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[ERROR] Response status: {e.response.status_code}")
            print(f"[ERROR] Response text: {e.response.text[:500]}")
        raise

def main():
    print("=" * 60)
    print("Policy Creation Test Script")
    print("=" * 60)
    
    try:
        # Authenticate
        print("\n1. Authenticating...")
        token = get_auth_token(USERNAME, PASSWORD)
        print(f"✅ Authentication successful (token: {token[:20]}...)")
        
        # Get existing policies
        print("\n2. Checking existing policies...")
        existing_policies = get_policies(token)
        print(f"✅ Found {len(existing_policies)} existing policies")
        for p in existing_policies:
            print(f"   - {p['name']} (ID: {p['id']})")
        
        # Create new policy
        print("\n3. Creating new policy...")
        test_policy_data = {
            "name": "Test USB Transfer Block Policy",
            "description": "Test policy to block file transfers from Documents folder to USB drives",
            "type": "usb_file_transfer_monitoring",
            "severity": "medium",
            "priority": 100,
            "enabled": True,
            "config": {
                "monitoredPaths": ["C:\\Users\\%USERNAME%\\Documents"],
                "action": "block"
            },
            "conditions": [],
            "actions": [],
            "compliance_tags": []
        }
        
        print(f"Creating policy: {test_policy_data['name']}")
        print(f"Policy data: {json.dumps(test_policy_data, indent=2)}")
        
        created_policy = create_policy(token, test_policy_data)
        print(f"\n✅ Policy created successfully!")
        print(f"   ID: {created_policy.get('id')}")
        print(f"   Name: {created_policy.get('name')}")
        print(f"   Type: {created_policy.get('type')}")
        print(f"   Severity: {created_policy.get('severity')}")
        print(f"   Enabled: {created_policy.get('enabled')}")
        
        # Verify policy creation
        print("\n4. Verifying policy creation...")
        all_policies = get_policies(token)
        print(f"✅ Total policies now: {len(all_policies)}")
        found = any(p['id'] == created_policy['id'] for p in all_policies)
        if found:
            print(f"✅ Policy '{created_policy['name']}' found in the list!")
        else:
            print(f"❌ Policy '{created_policy['name']}' NOT found in the list!")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text[:500]}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

