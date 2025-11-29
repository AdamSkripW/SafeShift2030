"""
SafeShift 2030 API Test Script - DELETE Requests
Tests all DELETE endpoints
WARNING: This will delete test data from your database!
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

def test_hospitals_delete():
    """Test Hospital DELETE operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING HOSPITALS - DELETE{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    hospital_id = input(f"{Colors.YELLOW}Enter Hospital ID to delete (or press Enter to skip): {Colors.END}")
    
    if hospital_id:
        response = requests.delete(f"{BASE_URL}/hospitals/{hospital_id}")
        print_test(f"/hospitals/{hospital_id}", "DELETE", response.status_code, response.json())
    else:
        print(f"{Colors.YELLOW}Skipped{Colors.END}")

def test_users_delete():
    """Test User DELETE operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING USERS - DELETE{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    user_id = input(f"{Colors.YELLOW}Enter User ID to delete (or press Enter to skip): {Colors.END}")
    
    if user_id:
        response = requests.delete(f"{BASE_URL}/users/{user_id}")
        print_test(f"/users/{user_id}", "DELETE", response.status_code, response.json())
    else:
        print(f"{Colors.YELLOW}Skipped{Colors.END}")

def test_admins_delete():
    """Test Hospital Admin DELETE operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING HOSPITAL ADMINS - DELETE{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    admin_id = input(f"{Colors.YELLOW}Enter Admin ID to delete (or press Enter to skip): {Colors.END}")
    
    if admin_id:
        response = requests.delete(f"{BASE_URL}/admins/{admin_id}")
        print_test(f"/admins/{admin_id}", "DELETE", response.status_code, response.json())
    else:
        print(f"{Colors.YELLOW}Skipped{Colors.END}")

def test_shifts_delete():
    """Test Shift DELETE operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING SHIFTS - DELETE{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    shift_id = input(f"{Colors.YELLOW}Enter Shift ID to delete (or press Enter to skip): {Colors.END}")
    
    if shift_id:
        response = requests.delete(f"{BASE_URL}/shifts/{shift_id}")
        print_test(f"/shifts/{shift_id}", "DELETE", response.status_code, response.json())
    else:
        print(f"{Colors.YELLOW}Skipped{Colors.END}")

def test_timeoff_delete():
    """Test Time Off Request DELETE operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING TIME OFF REQUESTS - DELETE{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    timeoff_id = input(f"{Colors.YELLOW}Enter TimeOff ID to delete (or press Enter to skip): {Colors.END}")
    
    if timeoff_id:
        response = requests.delete(f"{BASE_URL}/timeoff/{timeoff_id}")
        print_test(f"/timeoff/{timeoff_id}", "DELETE", response.status_code, response.json())
    else:
        print(f"{Colors.YELLOW}Skipped{Colors.END}")

def test_alerts_delete():
    """Test Burnout Alert DELETE operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING BURNOUT ALERTS - DELETE{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    alert_id = input(f"{Colors.YELLOW}Enter Alert ID to delete (or press Enter to skip): {Colors.END}")
    
    if alert_id:
        response = requests.delete(f"{BASE_URL}/alerts/{alert_id}")
        print_test(f"/alerts/{alert_id}", "DELETE", response.status_code, response.json())
    else:
        print(f"{Colors.YELLOW}Skipped{Colors.END}")

def test_sessions_delete():
    """Test Session DELETE operation"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING SESSIONS - DELETE{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    session_id = input(f"{Colors.YELLOW}Enter Session ID to delete (or press Enter to skip): {Colors.END}")
    
    if session_id:
        response = requests.delete(f"{BASE_URL}/sessions/{session_id}")
        print_test(f"/sessions/{session_id}", "DELETE", response.status_code, response.json())
    else:
        print(f"{Colors.YELLOW}Skipped{Colors.END}")

def main():
    """Run all DELETE tests"""
    print(f"\n{Colors.RED}{'='*60}{Colors.END}")
    print(f"{Colors.RED}WARNING: This script will DELETE data from your database!{Colors.END}")
    print(f"{Colors.RED}{'='*60}{Colors.END}")
    
    confirm = input(f"\n{Colors.YELLOW}Are you sure you want to continue? (yes/no): {Colors.END}")
    if confirm.lower() != 'yes':
        print(f"{Colors.YELLOW}Test cancelled.{Colors.END}")
        return
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}SafeShift 2030 API Test Suite - DELETE Requests{Colors.END}")
    print(f"{Colors.GREEN}Testing against: {BASE_URL}{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    
    try:
        test_sessions_delete()
        test_alerts_delete()
        test_timeoff_delete()
        test_shifts_delete()
        test_admins_delete()
        test_users_delete()
        test_hospitals_delete()
        
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}All DELETE tests completed!{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
        
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Could not connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.RED}Make sure the backend is running: python run.py{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {str(e)}{Colors.END}\n")

if __name__ == "__main__":
    main()
