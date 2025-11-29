"""
SafeShift 2030 API Test Script - POST Requests
Tests all POST endpoints with sample data
"""

import requests
import json
from datetime import datetime, timedelta

# API Base URL
BASE_URL = "http://localhost:5000/api"

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(endpoint, method, status_code, response):
    """Print formatted test results"""
    status_symbol = f"{Colors.GREEN}✓{Colors.END}" if 200 <= status_code < 300 else f"{Colors.RED}✗{Colors.END}"
    print(f"\n{status_symbol} {method} {endpoint} - Status: {status_code}")
    print(f"{Colors.BLUE}Response:{Colors.END} {json.dumps(response, indent=2)}")

def test_hospitals_post():
    """Test Hospital POST operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING HOSPITALS - POST{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # POST - Create hospital
    hospital_data = {
        "Name": "Test Hospital API",
        "City": "Bratislava",
        "Country": "Slovakia",
        "ContactEmail": "contact@testhospital.sk",
        "PhoneNumber": "+421-2-1234-5678"
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(hospital_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/hospitals", json=hospital_data)
    print_test("/hospitals", "POST", response.status_code, response.json())
    
    if response.status_code == 201:
        return response.json()['data']['HospitalId']
    return None

def test_users_post():
    """Test User POST operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING USERS - POST{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # POST - Create user
    user_data = {
        "Email": "test.user@hospital.sk",
        "Password": "TestPassword123!",
        "FirstName": "Test",
        "LastName": "User",
        "Role": "nurse",
        "Department": "Emergency",
        "Hospital": "Test Hospital",
        "HospitalId": 1,
        "IsActive": True
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(user_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/users", json=user_data)
    print_test("/users", "POST", response.status_code, response.json())
    
    if response.status_code == 201:
        return response.json()['data']['UserId']
    return None

def test_admins_post():
    """Test Hospital Admin POST operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING HOSPITAL ADMINS - POST{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # POST - Create admin (requires existing user and hospital)
    admin_data = {
        "UserId": 1,
        "HospitalId": 1,
        "Role": "wellness_manager",
        "PermissionsViewAll": True,
        "PermissionsEditShifts": False,
        "PermissionsAssignTimeOff": True
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(admin_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/admins", json=admin_data)
    print_test("/admins", "POST", response.status_code, response.json())
    
    if response.status_code == 201:
        return response.json()['data']['AdminId']
    return None

def test_shifts_post():
    """Test Shift POST operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING SHIFTS - POST{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # POST - Create shift
    today = datetime.now().strftime('%Y-%m-%d')
    shift_data = {
        "UserId": 1,
        "ShiftDate": today,
        "HoursSleptBefore": 7,
        "ShiftType": "day",
        "ShiftLengthHours": 8,
        "PatientsCount": 6,
        "StressLevel": 5,
        "ShiftNote": "API test shift",
        "SafeShiftIndex": 75,
        "Zone": "green",
        "AiExplanation": "Good parameters",
        "AiTips": "Maintain current sleep schedule"
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(shift_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/shifts", json=shift_data)
    print_test("/shifts", "POST", response.status_code, response.json())
    
    if response.status_code == 201:
        return response.json()['data']['ShiftId']
    return None

def test_timeoff_post():
    """Test Time Off Request POST operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING TIME OFF REQUESTS - POST{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # POST - Create time off request
    start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d')
    
    timeoff_data = {
        "UserId": 1,
        "StartDate": start_date,
        "EndDate": end_date,
        "Reason": "rest_recovery",
        "Status": "pending",
        "Notes": "API test time off request"
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(timeoff_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/timeoff", json=timeoff_data)
    print_test("/timeoff", "POST", response.status_code, response.json())
    
    if response.status_code == 201:
        return response.json()['data']['TimeOffId']
    return None

def test_alerts_post():
    """Test Burnout Alert POST operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING BURNOUT ALERTS - POST{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # POST - Create alert
    alert_data = {
        "UserId": 1,
        "AlertType": "chronic_low_sleep",
        "Severity": "medium",
        "Description": "API test: User averaging less than 6 hours sleep for 3 days",
        "IsResolved": False
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(alert_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/alerts", json=alert_data)
    print_test("/alerts", "POST", response.status_code, response.json())
    
    if response.status_code == 201:
        return response.json()['data']['AlertId']
    return None

def test_sessions_post():
    """Test Session POST operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING SESSIONS - POST{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # POST - Create session
    session_data = {
        "UserId": 1,
        "IpAddress": "192.168.1.100",
        "UserAgent": "SafeShift API Test Client"
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(session_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/sessions", json=session_data)
    print_test("/sessions", "POST", response.status_code, response.json())
    
    if response.status_code == 201:
        return response.json()['data']['SessionId']
    return None

def main():
    """Run all POST tests"""
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}SafeShift 2030 API Test Suite - POST Requests{Colors.END}")
    print(f"{Colors.GREEN}Testing against: {BASE_URL}{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    
    created_ids = {}
    
    try:
        created_ids['hospital'] = test_hospitals_post()
        created_ids['user'] = test_users_post()
        created_ids['admin'] = test_admins_post()
        created_ids['shift'] = test_shifts_post()
        created_ids['timeoff'] = test_timeoff_post()
        created_ids['alert'] = test_alerts_post()
        created_ids['session'] = test_sessions_post()
        
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}All POST tests completed!{Colors.END}")
        print(f"{Colors.YELLOW}Created IDs:{Colors.END}")
        for key, value in created_ids.items():
            if value:
                print(f"  {key}: {value}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
        
        return created_ids
        
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Could not connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.RED}Make sure the backend is running: python run.py{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {str(e)}{Colors.END}\n")

if __name__ == "__main__":
    main()
