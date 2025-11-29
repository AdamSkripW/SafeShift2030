"""
Quick test to verify service imports work correctly
Run this to ensure the new service structure is working
"""

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
    index, zone = SafeShiftService.calculate_index(
        hours_slept=5,
        shift_type='night',
        shift_length=12,
        patients_count=10,
        stress_level=7
    )
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
