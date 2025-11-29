"""
SafeShift 2030 Services Test Script
Tests SafeShift Index calculation, Anomaly Detection, Predictions, and LLM integration
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API Base URL
BASE_URL = "http://localhost:5000/api"

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_header(title):
    """Print section header"""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.CYAN}{title}{Colors.END}")
    print(f"{Colors.CYAN}{'='*70}{Colors.END}")

def print_result(message, success=True):
    """Print test result"""
    symbol = f"{Colors.GREEN}✓{Colors.END}" if success else f"{Colors.RED}✗{Colors.END}"
    print(f"{symbol} {message}")

def print_data(label, data):
    """Print formatted data"""
    print(f"{Colors.BLUE}{label}:{Colors.END}")
    print(json.dumps(data, indent=2))


# ============================================
# Test 1: SafeShift Index Calculation
# ============================================

def test_safeshift_index_calculation():
    """Test SafeShift Index calculation with different scenarios"""
    
    print_header("TEST 1: SafeShift Index Calculation")
    
    # Scenario 1: Green Zone - Good conditions
    print(f"\n{Colors.YELLOW}Scenario 1: Green Zone (Low Risk){Colors.END}")
    green_shift = {
        "UserId": 1,
        "ShiftDate": datetime.now().strftime('%Y-%m-%d'),
        "HoursSleptBefore": 8,
        "ShiftType": "day",
        "ShiftLengthHours": 8,
        "PatientsCount": 5,
        "StressLevel": 3,
        "ShiftNote": "Normal day shift, well rested"
    }
    
    response = requests.post(f"{BASE_URL}/shifts", json=green_shift)
    if response.status_code == 201:
        shift_data = response.json()['data']
        index = shift_data.get('SafeShiftIndex', 0)
        zone = shift_data.get('Zone', 'unknown')
        print_result(f"Index: {index}, Zone: {zone}", zone == 'green')
        print_data("Shift Data", shift_data)
    else:
        print_result(f"Failed to create green zone shift - Status: {response.status_code}", False)
        print(f"{Colors.RED}Error: {response.text}{Colors.END}")
    
    # Scenario 2: Yellow Zone - Moderate risk
    print(f"\n{Colors.YELLOW}Scenario 2: Yellow Zone (Moderate Risk){Colors.END}")
    yellow_shift = {
        "UserId": 1,
        "ShiftDate": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        "HoursSleptBefore": 6,  # Changed from 5 to 6 (20 → 10 points)
        "ShiftType": "day",      # Changed from night to day (25 → 10 points)
        "ShiftLengthHours": 12,
        "PatientsCount": 10,
        "StressLevel": 6,
        "ShiftNote": "Long day shift, moderately tired"
    }
    
    response = requests.post(f"{BASE_URL}/shifts", json=yellow_shift)
    if response.status_code == 201:
        shift_data = response.json()['data']
        index = shift_data.get('SafeShiftIndex', 0)
        zone = shift_data.get('Zone', 'unknown')
        print_result(f"Index: {index}, Zone: {zone}", zone == 'yellow')
        print_data("Shift Data", shift_data)
    else:
        print_result("Failed to create yellow zone shift", False)
    
    # Scenario 3: Red Zone - High risk
    print(f"\n{Colors.YELLOW}Scenario 3: Red Zone (High Risk){Colors.END}")
    red_shift = {
        "UserId": 1,
        "ShiftDate": (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
        "HoursSleptBefore": 3,
        "ShiftType": "night",
        "ShiftLengthHours": 16,
        "PatientsCount": 15,
        "StressLevel": 9,
        "ShiftNote": "Extremely exhausting night shift"
    }
    
    response = requests.post(f"{BASE_URL}/shifts", json=red_shift)
    if response.status_code == 201:
        shift_data = response.json()['data']
        index = shift_data.get('SafeShiftIndex', 0)
        zone = shift_data.get('Zone', 'unknown')
        print_result(f"Index: {index}, Zone: {zone}", zone == 'red')
        print_data("Shift Data", shift_data)
        
        # Check AI explanation and tips if present
        if 'AiExplanation' in shift_data:
            print(f"\n{Colors.BLUE}AI Explanation:{Colors.END}")
            print(shift_data['AiExplanation'])
        if 'AiTips' in shift_data:
            print(f"\n{Colors.BLUE}AI Tips:{Colors.END}")
            print(shift_data['AiTips'])
    else:
        print_result("Failed to create red zone shift", False)


# ============================================
# Test 2: Anomaly Detection Patterns
# ============================================

def test_anomaly_detection():
    """Test anomaly detection by creating patterns"""
    
    print_header("TEST 2: Anomaly Detection")
    
    print(f"\n{Colors.YELLOW}Creating pattern: Consecutive Night Shifts{Colors.END}")
    
    # Create 5 consecutive night shifts with low sleep
    base_date = datetime.now() + timedelta(days=3)
    for i in range(5):
        night_shift = {
            "UserId": 1,
            "ShiftDate": (base_date + timedelta(days=i)).strftime('%Y-%m-%d'),
            "HoursSleptBefore": 4,
            "ShiftType": "night",
            "ShiftLengthHours": 12,
            "PatientsCount": 8,
            "StressLevel": 7,
            "ShiftNote": f"Consecutive night shift {i+1}/5"
        }
        
        response = requests.post(f"{BASE_URL}/shifts", json=night_shift)
        if response.status_code == 201:
            print_result(f"Created night shift {i+1}/5")
        else:
            print_result(f"Failed to create night shift {i+1}/5", False)
    
    # Check for burnout alerts
    print(f"\n{Colors.YELLOW}Checking for generated alerts...{Colors.END}")
    response = requests.get(f"{BASE_URL}/alerts?user_id=1&unresolved=true")
    if response.status_code == 200:
        alerts = response.json()['data']
        print_result(f"Found {len(alerts)} unresolved alerts")
        for alert in alerts:
            print_data(f"Alert: {alert['AlertType']}", alert)
    else:
        print_result("Failed to fetch alerts", False)


# ============================================
# Test 3: Burnout Risk Prediction
# ============================================

def test_burnout_prediction():
    """Test burnout prediction with trend data"""
    
    print_header("TEST 3: Burnout Risk Prediction")
    
    print(f"\n{Colors.YELLOW}Getting user's shifts for prediction...{Colors.END}")
    
    response = requests.get(f"{BASE_URL}/shifts?user_id=1")
    if response.status_code == 200:
        shifts = response.json()['data']
        print_result(f"Retrieved {len(shifts)} shifts for analysis")
        
        # Display trend
        if len(shifts) >= 3:
            indices = [s.get('SafeShiftIndex', 0) for s in shifts[-7:]]
            print(f"\n{Colors.BLUE}Last 7 shifts indices:{Colors.END} {indices}")
            
            # Calculate simple trend
            if len(indices) > 1:
                trend = "increasing" if indices[-1] > indices[0] else "decreasing"
                print_result(f"Trend: {trend} (from {indices[0]} to {indices[-1]})")
        else:
            print_result("Not enough shift data for trend analysis", False)
    else:
        print_result("Failed to fetch shifts", False)


# ============================================
# Test 4: LLM Integration (if enabled)
# ============================================

def test_llm_integration():
    """Test LLM-generated content in shifts"""
    
    print_header("TEST 4: LLM Integration")
    
    print(f"\n{Colors.YELLOW}Creating shift with emotional note for LLM analysis...{Colors.END}")
    
    emotional_shift = {
        "UserId": 1,
        "ShiftDate": (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
        "HoursSleptBefore": 4,
        "ShiftType": "night",
        "ShiftLengthHours": 14,
        "PatientsCount": 12,
        "StressLevel": 8,
        "ShiftNote": "Very difficult night. Lost a patient despite our best efforts. Feeling emotionally drained and questioning if I could have done more."
    }
    
    response = requests.post(f"{BASE_URL}/shifts", json=emotional_shift)
    if response.status_code == 201:
        shift_data = response.json()['data']
        print_result("Created shift with emotional note")
        
        # Check if AI analysis is present
        if shift_data.get('AiExplanation'):
            print(f"\n{Colors.BLUE}AI Explanation:{Colors.END}")
            print(shift_data['AiExplanation'])
            print_result("LLM explanation generated", True)
        else:
            print_result("No LLM explanation (API key may not be configured)", False)
        
        if shift_data.get('AiTips'):
            print(f"\n{Colors.BLUE}AI Tips:{Colors.END}")
            print(shift_data['AiTips'])
            print_result("LLM tips generated", True)
        else:
            print_result("No LLM tips (API key may not be configured)", False)
    else:
        print_result("Failed to create shift", False)


# ============================================
# Test 5: Time Off Request Integration
# ============================================

def test_timeoff_integration():
    """Test time off request creation and approval"""
    
    print_header("TEST 5: Time Off Request Integration")
    
    print(f"\n{Colors.YELLOW}Creating time off request...{Colors.END}")
    
    timeoff_data = {
        "UserId": 1,
        "StartDate": (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
        "EndDate": (datetime.now() + timedelta(days=17)).strftime('%Y-%m-%d'),
        "Reason": "burnout_risk",
        "Status": "pending",
        "Notes": "Need recovery time after consecutive night shifts"
    }
    
    response = requests.post(f"{BASE_URL}/timeoff", json=timeoff_data)
    if response.status_code == 201:
        timeoff = response.json()['data']
        print_result("Time off request created")
        print_data("Time Off Request", timeoff)
        
        # Update status to approved
        timeoff_id = timeoff['TimeOffId']
        update_data = {
            "Status": "approved",
            "Notes": "Approved for recovery - automated test"
        }
        
        response = requests.put(f"{BASE_URL}/timeoff/{timeoff_id}", json=update_data)
        if response.status_code == 200:
            print_result("Time off request approved")
        else:
            print_result("Failed to approve time off", False)
    else:
        print_result("Failed to create time off request", False)


# ============================================
# Main Test Runner
# ============================================

def main():
    """Run all service tests"""
    
    print(f"\n{Colors.GREEN}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}SafeShift 2030 Services Test Suite{Colors.END}")
    print(f"{Colors.GREEN}Testing against: {BASE_URL}{Colors.END}")
    print(f"{Colors.GREEN}{'='*70}{Colors.END}")
    
    try:
        # Run all tests
        test_safeshift_index_calculation()
        test_anomaly_detection()
        test_burnout_prediction()
        test_llm_integration()
        test_timeoff_integration()
        
        print(f"\n{Colors.GREEN}{'='*70}{Colors.END}")
        print(f"{Colors.GREEN}All service tests completed!{Colors.END}")
        print(f"{Colors.GREEN}{'='*70}{Colors.END}\n")
        
        print(f"{Colors.YELLOW}Note:{Colors.END} LLM features require OPENAI_API_KEY in .env file")
        print(f"{Colors.YELLOW}Note:{Colors.END} Some tests create data in your database for user_id=1")
        
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Could not connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.RED}Make sure the backend is running: python run.py{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {str(e)}{Colors.END}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
