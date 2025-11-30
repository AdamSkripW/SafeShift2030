"""
Quick Test for MicroBreakCoachAgent
Tests the agent directly and via API endpoint
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:5000/api"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_direct_agent():
    """Test agent directly"""
    print_section("TEST 1: Direct Agent Test (OpenAI API)")
    
    try:
        # Import Flask app for database context
        from app import create_app
        from app.services.agents import MicroBreakCoachAgent
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            agent = MicroBreakCoachAgent()
            print(f"✅ Agent loaded: {agent.agent_name}")
            
            # Test high stress scenario (without user_id to skip metrics logging)
            print("\n📋 Scenario: High stress (8/10), 3 minutes, hallway, night shift")
            print("   Note: Running without user_id (metrics won't be logged to database)")
            result = agent.generate_break(
                stress_level=8,
                minutes_available=3,
                location="hallway",
                shift_type="night"
                # user_id and shift_id omitted - metrics logging will be skipped
            )
            
            print("\n📤 Result:")
            print(json.dumps(result, indent=2))
            
            if result.get('_fallback'):
                print("\n⚠️  Warning: Fallback response used")
            else:
                print(f"\n✅ Break generated: {result.get('name')}")
                print(f"   Steps: {len(result.get('steps', []))}")
                print(f"   Expected reduction: {result.get('expected_stress_reduction')}/3")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoint():
    """Test via API endpoint"""
    print_section("TEST 2: API Endpoint Test (POST /agents/micro-break)")
    
    test_scenarios = [
        {
            "name": "High stress, 2 minutes, bathroom",
            "payload": {
                "stress_level": 9,
                "minutes_available": 2,
                "location": "bathroom",
                "shift_type": "night"
            }
        },
        {
            "name": "Moderate stress, 5 minutes, break room",
            "payload": {
                "stress_level": 5,
                "minutes_available": 5,
                "location": "break_room",
                "shift_type": "day"
            }
        },
        {
            "name": "Low stress, 3 minutes, outside",
            "payload": {
                "stress_level": 3,
                "minutes_available": 3,
                "location": "outside"
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n{'─'*70}")
        print(f"📋 {scenario['name']}")
        print(f"{'─'*70}")
        
        try:
            url = f"{API_BASE}/agents/micro-break"
            print(f"\nPOST {url}")
            print(f"Payload: {json.dumps(scenario['payload'], indent=2)}")
            
            response = requests.post(url, json=scenario['payload'])
            
            print(f"\nStatus: {response.status_code}")
            result = response.json()
            
            if result.get('success'):
                data = result['data']
                print(f"\n✅ {data.get('name')}")
                print(f"   Duration: {data.get('duration_minutes')} min")
                print(f"   Location: {data.get('location_fit')}")
                print(f"   Stress reduction: {data.get('expected_stress_reduction')}/3")
                print(f"\n   Steps:")
                for i, step in enumerate(data.get('steps', []), 1):
                    print(f"      {i}. {step}")
                print(f"\n   Why: {data.get('why')}")
                
                if data.get('_fallback'):
                    print("\n   ⚠️  Fallback response")
            else:
                print(f"\n❌ Error: {result.get('error')}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n❌ Cannot connect to {API_BASE}")
            print("   Make sure backend is running: python run.py")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        if scenario != test_scenarios[-1]:
            input("\nPress Enter to continue...")

def test_validation():
    """Test input validation"""
    print_section("TEST 3: Input Validation")
    
    test_cases = [
        {
            "name": "Invalid stress level (15)",
            "payload": {"stress_level": 15, "minutes_available": 3, "location": "hallway"},
            "should_work": True  # Should clamp to 10
        },
        {
            "name": "Invalid minutes (7)",
            "payload": {"stress_level": 5, "minutes_available": 7, "location": "break_room"},
            "should_work": True  # Should default to closest (5)
        },
        {
            "name": "Missing required field",
            "payload": {"stress_level": 5, "minutes_available": 3},
            "should_work": False
        },
        {
            "name": "Invalid location",
            "payload": {"stress_level": 5, "minutes_available": 3, "location": "cafeteria"},
            "should_work": True  # Should default to break_room
        }
    ]
    
    for tc in test_cases:
        print(f"\n📋 {tc['name']}")
        print(f"   Payload: {json.dumps(tc['payload'])}")
        
        try:
            response = requests.post(f"{API_BASE}/agents/micro-break", json=tc['payload'])
            result = response.json()
            
            if result.get('success'):
                print(f"   ✅ Accepted (status: {response.status_code})")
                if not tc['should_work']:
                    print(f"   ⚠️  Expected to fail but succeeded")
            else:
                print(f"   ❌ Rejected: {result.get('error')}")
                if tc['should_work']:
                    print(f"   ⚠️  Expected to work but failed")
                    
        except requests.exceptions.ConnectionError:
            print("   ❌ Backend not running")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    print("\n🚀 MicroBreakCoachAgent - Quick Test Suite")
    print("="*70)
    
    print("\nSelect test:")
    print("  1. Test agent directly (requires OpenAI API key)")
    print("  2. Test API endpoint (requires backend running)")
    print("  3. Test input validation (requires backend running)")
    print("  4. Run all tests")
    
    choice = input("\nSelect (1-4): ").strip()
    
    if choice == "1":
        test_direct_agent()
    elif choice == "2":
        test_api_endpoint()
    elif choice == "3":
        test_validation()
    elif choice == "4":
        test_direct_agent()
        input("\nPress Enter to continue to API tests...")
        test_api_endpoint()
        input("\nPress Enter to continue to validation tests...")
        test_validation()
    else:
        print("Invalid selection")
        return
    
    print("\n" + "="*70)
    print("✅ Tests completed!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
