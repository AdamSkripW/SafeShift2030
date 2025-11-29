"""Test LLM service initialization"""
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Check if API key is loaded
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL')

print("=" * 60)
print("LLM Configuration Test")
print("=" * 60)
print(f"OPENAI_API_KEY loaded: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"Key starts with: {api_key[:20]}...")
    print(f"Key length: {len(api_key)} characters")
print(f"OPENAI_MODEL: {model}")
print()

# Test LLM service import
print("Testing LLM Service import...")
try:
    from app.services.llm_service import LLMService
    
    llm = LLMService()
    print(f"LLM Service initialized: {'Enabled' if llm.enabled else 'Disabled'}")
    print(f"Model: {llm.model}")
    
    if llm.enabled:
        print("\n✅ LLM Service is working!")
        
        # Test a simple call
        print("\nTesting generate_insights...")
        result = llm.generate_insights(
            shift_data={
                'hours_slept': 5,
                'shift_type': 'night',
                'shift_length': 12,
                'patients_count': 10,
                'stress_level': 7,
                'shift_note': 'Very tired, stressful shift'
            },
            index=72,
            zone='red'
        )
        print(f"Explanation length: {len(result.get('explanation', ''))} chars")
        print(f"Tips length: {len(result.get('tips', ''))} chars")
        print("\nExplanation preview:")
        print(result.get('explanation', 'None')[:200])
    else:
        print("\n❌ LLM Service is disabled - API key not detected")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
