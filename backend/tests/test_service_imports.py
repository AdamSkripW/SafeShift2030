"""
Quick test to verify service imports work correctly
Run this to ensure the new service structure is working
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

print("Testing service imports...")

try:
    # Test main import
    from app.services import (
        HospitalService,
        UserService,
        ShiftService,
        TimeOffService,
        BurnoutAlertService,
        SafeShiftService,
        AnomalyService,
        PredictionService,
        LLMService
    )
    print("✓ All services imported successfully from app.services")
    
    # Test individual imports
    from app.services.crud_service import UserService as US
    from app.services.safeshift_service import SafeShiftService as SSS
    from app.services.anomaly_service import AnomalyService as AS
    from app.services.prediction_service import PredictionService as PS
    from app.services.llm_service import LLMService as LS
    print("✓ Individual service imports working")
    
    # Test SafeShift calculation
    result = SafeShiftService.calculate_index(
        hours_slept=5,
        shift_type='night',
        shift_length=12,
        patients_count=10,
        stress_level=7
    )
    index, zone = result
    print(f"✓ SafeShift calculation working: Index={index}, Zone={zone}")
    
    # Test LLM initialization
    llm = LLMService()
    print(f"✓ LLM Service initialized: enabled={llm.enabled}")
    
    print("\n✅ All service imports and basic functionality verified!")
    print("\nService structure:")
    print("  - CRUD Services: Hospital, User, Shift, TimeOff, BurnoutAlert")
    print("  - SafeShift Index: Burnout risk calculation")
    print("  - Anomaly Detection: Pattern analysis")
    print("  - Prediction: Burnout forecasting")
    print("  - LLM: AI-powered insights (OpenAI)")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
