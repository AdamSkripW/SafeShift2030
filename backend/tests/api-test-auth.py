"""
SafeShift 2030 API Test Script - Authentication Endpoints
Tests register, login, logout, refresh, and me endpoints
"""

import requests
import json

# API Base URL
BASE_URL = "http://localhost:5000/api/auth"

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

def test_register():
    """Test user registration"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING REGISTRATION{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    register_data = {
        "email": "test.auth@hospital.sk",
        "password": "SecurePass123!",
        "firstName": "Auth",
        "lastName": "Tester",
        "role": "nurse",
        "department": "Emergency",
        "hospital": "Test Hospital",
        "hospitalId": 1
    }
    
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(register_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/register", json=register_data)
    print_test("/auth/register", "POST", response.status_code, response.json())
    
    return response.json() if response.status_code == 201 else None

def test_login(email="test.auth@hospital.sk", password="SecurePass123!"):
    """Test user login"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING LOGIN{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(login_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print_test("/auth/login", "POST", response.status_code, response.json())
    
    if response.status_code == 200:
        return response.json().get('token')
    return None

def test_get_me(token):
    """Test getting current user info"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING GET CURRENT USER{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/me", headers=headers)
    print_test("/auth/me", "GET", response.status_code, response.json())

def test_refresh(token):
    """Test token refresh"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING TOKEN REFRESH{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(f"{BASE_URL}/refresh", headers=headers)
    print_test("/auth/refresh", "POST", response.status_code, response.json())
    
    if response.status_code == 200:
        return response.json().get('token')
    return None

def test_logout():
    """Test user logout"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING LOGOUT{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    response = requests.post(f"{BASE_URL}/logout")
    print_test("/auth/logout", "POST", response.status_code, response.json())

def test_login_invalid():
    """Test login with invalid credentials"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}TESTING INVALID LOGIN{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    login_data = {
        "email": "nonexistent@hospital.sk",
        "password": "WrongPassword"
    }
    
    print(f"{Colors.BLUE}Request Data:{Colors.END} {json.dumps(login_data, indent=2)}")
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print_test("/auth/login (invalid)", "POST", response.status_code, response.json())

def main():
    """Run all auth tests"""
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}SafeShift 2030 API Test Suite - Authentication{Colors.END}")
    print(f"{Colors.GREEN}Testing against: {BASE_URL}{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    
    try:
        # Test registration
        user = test_register()
        
        # Test login
        token = test_login()
        
        if token:
            print(f"\n{Colors.GREEN}Token received: {token[:20]}...{Colors.END}")
            
            # Test getting current user
            test_get_me(token)
            
            # Test token refresh
            new_token = test_refresh(token)
            if new_token:
                print(f"\n{Colors.GREEN}New token received: {new_token[:20]}...{Colors.END}")
        
        # Test logout
        test_logout()
        
        # Test invalid login
        test_login_invalid()
        
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}All authentication tests completed!{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
        
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Could not connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.RED}Make sure the backend is running: python run.py{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {str(e)}{Colors.END}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
