"""
🏥 SAFESHIFT 2030 - ADMIN ENDPOINTS FULL TEST
Comprehensive test suite for admin dashboard
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"
TOKEN = None

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_result(status, message):
    emoji = "✅" if status else "❌"
    print(f"{emoji} {message}")

def print_data(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))

# TEST 1: Register Admin Account
def test_register_admin():
    print_header("1️⃣  REGISTERING ADMIN ACCOUNT")
    
    payload = {
        "email": "admin@hospital.sk",
        "password": "AdminPass123!",
        "firstName": "Mária",
        "lastName": "Šimová",
        "role": "doctor",  # Must be doctor/nurse/student in Users table
        "department": "Management",
        "hospital": "University Hospital Košice"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print_result(True, "Admin account created successfully!")
            print_data(response.json())
            return True
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print_result(True, "Admin account already exists (OK)")
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

# TEST 2: Login and Get Token
def test_login():
    global TOKEN
    print_header("2️⃣  LOGIN AS ADMIN")
    
    payload = {
        "email": "admin@hospital.sk",
        "password": "AdminPass123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            TOKEN = data.get('token') or data.get('access_token')
            print_result(True, "Login successful!")
            print(f"Token: {TOKEN[:50]}..." if TOKEN else "No token received")
            print_data(data)
            return TOKEN is not None
        else:
            print_result(False, f"Login failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

# TEST 3: Staff Overview
def test_staff_overview():
    print_header("3️⃣  STAFF OVERVIEW (Department: ICU)")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/staff-overview?department=ICU",
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Retrieved {len(data.get('staff', []))} staff members")
            print_data(data)
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            print_data(response.json() if response.text else {})
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

# TEST 4: Alerts
def test_alerts():
    print_header("4️⃣  CRITICAL ALERTS")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/admin/alerts", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            alerts_count = len(data.get('alerts', []))
            print_result(True, f"Retrieved {alerts_count} alerts")
            print_data(data)
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

# TEST 5: Staff Detail
def test_staff_detail():
    print_header("5️⃣  STAFF DETAIL (ID: 1)")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/admin/staff/1", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Retrieved staff details for {data.get('name', 'Unknown')}")
            print_data(data)
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

# TEST 6: Intervention Suggestion
def test_intervention():
    print_header("6️⃣  AI INTERVENTION SUGGESTION (ID: 1)")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/intervention-suggestion/1",
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "AI intervention generated!")
            print_data(data)
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

# TEST 7: Time-Off Assignment
def test_timeoff():
    print_header("7️⃣  ASSIGN TIME-OFF")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    payload = {
        "user_id": 1,
        "days": 3,
        "reason": "Burnout prevention - high stress detected"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/timeoff",
            json=payload,
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print_result(True, "Time-off assigned successfully!")
            print_data(data)
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

# TEST 8: Department Health
def test_department_health():
    print_header("8️⃣  DEPARTMENT HEALTH (ICU)")
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/department-health?department=ICU",
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Department health retrieved!")
            print_data(data)
            return True
        else:
            print_result(False, f"Failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

# MAIN TEST RUNNER
def run_all_tests():
    print("\n🏥 SAFESHIFT 2030 - ADMIN DASHBOARD TEST SUITE")
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"🌐 Backend URL: {BASE_URL}")
    
    results = {
        "Register Admin": test_register_admin(),
        "Login": test_login(),
    }
    
    if not TOKEN:
        print("\n❌ CRITICAL: Cannot proceed without token!")
        return
    
    results.update({
        "Staff Overview": test_staff_overview(),
        "Alerts": test_alerts(),
        "Staff Detail": test_staff_detail(),
        "AI Intervention": test_intervention(),
        "Department Health": test_department_health(),
    })
    
    # FINAL REPORT
    print_header("📊 FINAL TEST REPORT")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📈 SCORE: {passed}/{total} tests passed")
    percentage = (passed/total) * 100
    
    if percentage == 100:
        print("🎉 ALL TESTS PASSED! Ready for presentation! 🎤")
    elif percentage >= 75:
        print("⚠️  Most features work, minor issues detected")
    else:
        print("🐛 Critical issues found - needs debugging")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    run_all_tests()
