"""
Quick Test Script for Agent Metrics Endpoints

This script tests all agent metrics endpoints with sample data.
Run this AFTER you've created the database and have some shifts with notes.
"""

import requests
import json

API_BASE = "http://localhost:5000/api"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_endpoint(method, endpoint, params=None, json_data=None):
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=json_data)
        
        print(f"\n{method} {endpoint}")
        if params:
            print(f"Params: {params}")
        if json_data:
            print(f"Body: {json.dumps(json_data, indent=2)}")
        
        print(f"\nStatus: {response.status_code}")
        
        result = response.json()
        print("\nResponse:")
        print(json.dumps(result, indent=2))
        
        return result
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to {API_BASE}")
        print("Make sure the backend is running: python run.py")
        return None
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None

def main():
    print("\n🚀 Agent Metrics Endpoints - Quick Test")
    print("="*70)
    
    # Test 1: Create a shift with crisis detection
    print_section("TEST 1: Create Shift with Critical Crisis Note")
    
    shift_data = {
        "UserId": 1,  # Adjust to a valid user ID in your database
        "ShiftDate": "2024-01-15",
        "HoursSleptBefore": 4,
        "ShiftType": "Night",
        "ShiftLengthHours": 12,
        "PatientsCount": 10,
        "StressLevel": 9,
        "ShiftNote": "I can't do this anymore. What's the point. Everyone would be better off without me."
    }
    
    result = test_endpoint("POST", "/shifts", json_data=shift_data)
    
    if result and result.get('success'):
        if 'ai' in result and 'crisis' in result['ai']:
            crisis = result['ai']['crisis']
            print(f"\n🚨 CRISIS DETECTED!")
            print(f"   Severity: {crisis.get('severity', 'N/A').upper()}")
            print(f"   Confidence: {crisis.get('confidence_score', 0):.0%}")
            print(f"   Primary Concern: {crisis.get('primary_concern', 'N/A')}")
    
    input("\nPress Enter to continue...")
    
    # Test 2: Get agent statistics
    print_section("TEST 2: Get Agent Performance Statistics")
    test_endpoint("GET", "/agents/metrics", params={"agent": "crisis_detection", "days": 7})
    
    input("\nPress Enter to continue...")
    
    # Test 3: Daily crisis rate
    print_section("TEST 3: Get Daily Crisis Detection Rate")
    test_endpoint("GET", "/agents/metrics/crisis-rate", params={"days": 7})
    
    input("\nPress Enter to continue...")
    
    # Test 4: User crisis history
    print_section("TEST 4: Get User Crisis History")
    user_id = input("\nEnter user ID to check (default: 1): ").strip() or "1"
    test_endpoint("GET", f"/agents/metrics/user/{user_id}", params={"days": 30})
    
    input("\nPress Enter to continue...")
    
    # Test 5: Performance issues
    print_section("TEST 5: Get Performance Issues")
    test_endpoint("GET", "/agents/metrics/performance-issues", params={"threshold_ms": 5000})
    
    input("\nPress Enter to continue...")
    
    # Test 6: High-risk users
    print_section("TEST 6: Get High-Risk Users")
    test_endpoint("GET", "/agents/metrics/high-risk-users", params={"days": 7, "min_alerts": 2})
    
    print("\n" + "="*70)
    print("✅ All tests completed!")
    print("="*70)

if __name__ == "__main__":
    main()
