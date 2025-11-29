"""
SafeShift 2030 API Test Script - PUT Requests
Tests all PUT endpoints with sample data
"""

import requests
import json

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

def test_hospitals_put():
    """Test Hospital PUT operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING HOSPITALS - PUT{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    hospital_id = 1  # Update existing hospital with ID 1
    
    # PUT - Update hospital
    update_data = {
        "ContactEmail": "updated@hospital.sk",
        "PhoneNumber": "+421-2-9999-9999"
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(update_data, indent=2)}")
    response = requests.put(f"{BASE_URL}/hospitals/{hospital_id}", json=update_data)
    print_test(f"/hospitals/{hospital_id}", "PUT", response.status_code, response.json())

def test_users_put():
    """Test User PUT operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING USERS - PUT{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    user_id = 1  # Update existing user with ID 1
    
    # PUT - Update user
    update_data = {
        "Department": "ICU",
        "IsActive": True
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(update_data, indent=2)}")
    response = requests.put(f"{BASE_URL}/users/{user_id}", json=update_data)
    print_test(f"/users/{user_id}", "PUT", response.status_code, response.json())

def test_admins_put():
    """Test Hospital Admin PUT operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING HOSPITAL ADMINS - PUT{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    admin_id = 1  # Update existing admin with ID 1
    
    # PUT - Update admin
    update_data = {
        "PermissionsEditShifts": True,
        "PermissionsViewAll": True
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(update_data, indent=2)}")
    response = requests.put(f"{BASE_URL}/admins/{admin_id}", json=update_data)
    print_test(f"/admins/{admin_id}", "PUT", response.status_code, response.json())

def test_shifts_put():
    """Test Shift PUT operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING SHIFTS - PUT{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    shift_id = 1  # Update existing shift with ID 1
    
    # PUT - Update shift
    update_data = {
        "StressLevel": 6,
        "ShiftNote": "Updated via API PUT test"
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(update_data, indent=2)}")
    response = requests.put(f"{BASE_URL}/shifts/{shift_id}", json=update_data)
    print_test(f"/shifts/{shift_id}", "PUT", response.status_code, response.json())

def test_timeoff_put():
    """Test Time Off Request PUT operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING TIME OFF REQUESTS - PUT{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    timeoff_id = 2  # Update existing time off with ID 1
    
    # PUT - Update time off
    update_data = {
        "Status": "approved",
        "Notes": "Approved via API PUT test"
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(update_data, indent=2)}")
    response = requests.put(f"{BASE_URL}/timeoff/{timeoff_id}", json=update_data)
    print_test(f"/timeoff/{timeoff_id}", "PUT", response.status_code, response.json())

def test_alerts_put():
    """Test Burnout Alert PUT operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING BURNOUT ALERTS - PUT{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    alert_id = 2  # Update existing alert with ID 1
    
    # PUT - Update alert (resolve it)
    update_data = {
        "IsResolved": True,
        "Description": "Resolved via API PUT test"
    }
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(update_data, indent=2)}")
    response = requests.put(f"{BASE_URL}/alerts/{alert_id}", json=update_data)
    print_test(f"/alerts/{alert_id}", "PUT", response.status_code, response.json())

def test_sessions_put():
    """Test Session PUT operation (if implemented)"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING SESSIONS - PUT{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    print(f"{Colors.YELLOW}Note: Sessions typically don't have PUT endpoints{Colors.END}")
    print(f"{Colors.YELLOW}Sessions are usually created (POST) and deleted (DELETE) only{Colors.END}")

def main():
    """Run all PUT tests"""
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}SafeShift 2030 API Test Suite - PUT Requests{Colors.END}")
    print(f"{Colors.GREEN}Testing against: {BASE_URL}{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    
    try:
        test_hospitals_put()
        test_users_put()
        test_admins_put()
        test_shifts_put()
        test_timeoff_put()
        test_alerts_put()
        test_sessions_put()
        
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}All PUT tests completed!{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
        
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Could not connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.RED}Make sure the backend is running: python run.py{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {str(e)}{Colors.END}\n")

if __name__ == "__main__":
    main()
