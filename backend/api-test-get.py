"""
SafeShift 2030 API Test Script - GET Requests
Tests all GET endpoints
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

def test_health():
    """Test health check endpoint"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING HEALTH CHECK{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    response = requests.get(f"{BASE_URL}/health")
    print_test("/health", "GET", response.status_code, response.json())

def test_hospitals_get():
    """Test Hospital GET operations"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING HOSPITALS - GET{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # GET all hospitals
    response = requests.get(f"{BASE_URL}/hospitals")
    print_test("/hospitals", "GET", response.status_code, response.json())
    
    # GET specific hospital (ID 1)
    response = requests.get(f"{BASE_URL}/hospitals/1")
    print_test("/hospitals/1", "GET", response.status_code, response.json())

def test_users_get():
    """Test User GET operations"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING USERS - GET{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # GET all users
    response = requests.get(f"{BASE_URL}/users")
    print_test("/users", "GET", response.status_code, response.json())
    
    # GET specific user (ID 1)
    response = requests.get(f"{BASE_URL}/users/1")
    print_test("/users/1", "GET", response.status_code, response.json())

def test_admins_get():
    """Test Hospital Admin GET operations"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING HOSPITAL ADMINS - GET{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # GET all admins
    response = requests.get(f"{BASE_URL}/admins")
    print_test("/admins", "GET", response.status_code, response.json())
    
    # GET specific admin (ID 1)
    response = requests.get(f"{BASE_URL}/admins/1")
    print_test("/admins/1", "GET", response.status_code, response.json())

def test_shifts_get():
    """Test Shift GET operations"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING SHIFTS - GET{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # GET all shifts
    response = requests.get(f"{BASE_URL}/shifts")
    print_test("/shifts", "GET", response.status_code, response.json())
    
    # GET shifts for specific user
    response = requests.get(f"{BASE_URL}/shifts?user_id=1")
    print_test("/shifts?user_id=1", "GET", response.status_code, response.json())
    
    # GET specific shift (ID 1)
    response = requests.get(f"{BASE_URL}/shifts/1")
    print_test("/shifts/1", "GET", response.status_code, response.json())

def test_timeoff_get():
    """Test Time Off Request GET operations"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING TIME OFF REQUESTS - GET{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # GET all time off requests
    response = requests.get(f"{BASE_URL}/timeoff")
    print_test("/timeoff", "GET", response.status_code, response.json())
    
    # GET time off for specific user
    response = requests.get(f"{BASE_URL}/timeoff?user_id=1")
    print_test("/timeoff?user_id=1", "GET", response.status_code, response.json())
    
    # GET specific time off (ID 1)
    response = requests.get(f"{BASE_URL}/timeoff/1")
    print_test("/timeoff/1", "GET", response.status_code, response.json())

def test_alerts_get():
    """Test Burnout Alert GET operations"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING BURNOUT ALERTS - GET{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # GET all alerts
    response = requests.get(f"{BASE_URL}/alerts")
    print_test("/alerts", "GET", response.status_code, response.json())
    
    # GET unresolved alerts
    response = requests.get(f"{BASE_URL}/alerts?unresolved=true")
    print_test("/alerts?unresolved=true", "GET", response.status_code, response.json())
    
    # GET alerts for specific user
    response = requests.get(f"{BASE_URL}/alerts?user_id=1")
    print_test("/alerts?user_id=1", "GET", response.status_code, response.json())
    
    # GET specific alert (ID 1)
    response = requests.get(f"{BASE_URL}/alerts/1")
    print_test("/alerts/1", "GET", response.status_code, response.json())

def test_sessions_get():
    """Test Session GET operations"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING SESSIONS - GET{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    # GET all sessions
    response = requests.get(f"{BASE_URL}/sessions")
    print_test("/sessions", "GET", response.status_code, response.json())
    
    # GET sessions for specific user
    response = requests.get(f"{BASE_URL}/sessions?user_id=1")
    print_test("/sessions?user_id=1", "GET", response.status_code, response.json())
    
    # GET specific session (ID 1)
    response = requests.get(f"{BASE_URL}/sessions/1")
    print_test("/sessions/1", "GET", response.status_code, response.json())

def main():
    """Run all GET tests"""
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}SafeShift 2030 API Test Suite - GET Requests{Colors.END}")
    print(f"{Colors.GREEN}Testing against: {BASE_URL}{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    
    try:
        test_health()
        test_hospitals_get()
        test_users_get()
        test_admins_get()
        test_shifts_get()
        test_timeoff_get()
        test_alerts_get()
        test_sessions_get()
        
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}All GET tests completed!{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
        
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Could not connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.RED}Make sure the backend is running: python run.py{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {str(e)}{Colors.END}\n")

if __name__ == "__main__":
    main()
