"""
Quick admin test - assumes backend is already running
"""
import requests
import time
import json

BASE_URL = "http://localhost:5000"

def wait_for_backend(max_wait=10):
    """Wait for backend to be ready"""
    print("⏳ Waiting for backend...")
    for i in range(max_wait):
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=1)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except:
            time.sleep(1)
            print(f"   Attempt {i+1}/{max_wait}...")
    print("❌ Backend not responding!")
    return False

def test_quick():
    if not wait_for_backend():
        print("\n⚠️  BACKEND IS NOT RUNNING!")
        print("   Please start backend first:")
        print("   cd backend")
        print("   python run.py")
        return
    
    print("\n" + "="*60)
    print("  🏥 QUICK ADMIN TEST")
    print("="*60)
    
    # Register
    print("\n1️⃣  Registering admin...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "admin@hospital.sk",
            "password": "AdminPass123!",
            "firstName": "Mária",
            "lastName": "Šimová",
            "role": "admin",
            "department": "Management",
            "hospital": "University Hospital Košice"
        }, timeout=5)
        
        if response.status_code in [200, 201]:
            print(f"✅ Admin registered: {response.status_code}")
        elif "already exists" in response.text.lower():
            print("✅ Admin already exists")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Login
    print("\n2️⃣  Logging in...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@hospital.sk",
            "password": "AdminPass123!"
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token') or data.get('access_token')
            print(f"✅ Login successful!")
            print(f"   Token: {token[:30]}..." if token else "No token")
            
            # Test one endpoint
            print("\n3️⃣  Testing staff overview...")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{BASE_URL}/api/admin/staff-overview?department=ICU",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Staff overview works!")
                print(f"   Staff count: {len(data.get('staff', []))}")
            else:
                print(f"❌ Failed: {response.status_code}")
                print(response.text)
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_quick()
