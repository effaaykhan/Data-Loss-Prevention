#!/usr/bin/env python3
"""
Test script to check for duplicate events
"""
import requests
import json
import time
from datetime import datetime, timedelta

API_URL = "http://localhost:55000/api/v1"

def get_token():
    """Get authentication token"""
    response = requests.post(
        f"{API_URL}/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="username=admin&password=admin"
    )
    return response.json()["access_token"]

def get_recent_events(token, limit=50):
    """Get recent events"""
    response = requests.get(
        f"{API_URL}/events?limit={limit}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def analyze_duplicates(events):
    """Analyze events for duplicates"""
    print(f"\n=== Analyzing {len(events)} events for duplicates ===\n")
    
    # Group by file_path and event_subtype
    event_groups = {}
    for event in events:
        key = (
            event.get("file_path"),
            event.get("event_subtype"),
            event.get("agent_id")
        )
        if key not in event_groups:
            event_groups[key] = []
        event_groups[key].append(event)
    
    duplicates_found = False
    for key, group in event_groups.items():
        if len(group) > 1:
            duplicates_found = True
            file_path, event_subtype, agent_id = key
            print(f"⚠️  DUPLICATE FOUND:")
            print(f"   File: {file_path}")
            print(f"   Type: {event_subtype}")
            print(f"   Agent: {agent_id}")
            print(f"   Count: {len(group)}")
            print(f"   Event IDs:")
            for e in group:
                print(f"     - {e.get('id')} at {e.get('timestamp')}")
            print()
    
    if not duplicates_found:
        print("✅ No duplicates found")
    
    return duplicates_found

if __name__ == "__main__":
    print("Testing for duplicate events...")
    token = get_token()
    data = get_recent_events(token, limit=100)
    events = data.get("events", [])
    
    print(f"Total events: {data.get('total', 0)}")
    print(f"Retrieved: {len(events)}")
    
    analyze_duplicates(events)

