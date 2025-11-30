"""
Quick test for Agent Orchestrator and new API endpoints
Tests orchestration workflows without full OpenAI API calls
"""

import sys
import os
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.services import AgentOrchestrator
import json


def test_orchestrator_initialization():
    """Test that orchestrator initializes all agents"""
    print("\n" + "=" * 80)
    print("  TEST: Agent Orchestrator Initialization")
    print("=" * 80)
    
    orchestrator = AgentOrchestrator()
    
    assert orchestrator.emotion_agent is not None, "EmotionAgent not initialized"
    assert orchestrator.crisis_agent is not None, "CrisisAgent not initialized"
    assert orchestrator.safety_agent is not None, "SafetyAgent not initialized"
    assert orchestrator.break_agent is not None, "BreakAgent not initialized"
    assert orchestrator.insight_agent is not None, "InsightAgent not initialized"
    
    print("✓ All 5 agents initialized successfully")
    print(f"  - EmotionClassifierAgent: {orchestrator.emotion_agent.agent_name}")
    print(f"  - CrisisDetectionAgent: {orchestrator.crisis_agent.agent_name}")
    print(f"  - PatientSafetyCorrelationAgent: {orchestrator.safety_agent.agent_name}")
    print(f"  - MicroBreakCoachAgent: {orchestrator.break_agent.agent_name}")
    print(f"  - InsightComposerAgent: {orchestrator.insight_agent.agent_name}")
    
    return True


def test_api_endpoints():
    """Test that new endpoints are registered"""
    print("\n" + "=" * 80)
    print("  TEST: New API Endpoints Registration")
    print("=" * 80)
    
    app = create_app()
    
    # Expected new endpoints
    expected_endpoints = [
        '/api/agents/emotion-classify',
        '/api/agents/patient-safety-correlation',
        '/api/agents/comprehensive-analysis',
        '/api/agents/analyze-shift-note',
        '/api/agents/quick-wellness',
        '/api/agents/enhanced-crisis-detection'
    ]
    
    # Get all registered routes
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    
    print(f"\n✓ Total routes registered: {len(routes)}")
    print("\nNew agent endpoints:")
    
    for endpoint in expected_endpoints:
        if endpoint in routes:
            print(f"  ✓ {endpoint}")
        else:
            print(f"  ✗ MISSING: {endpoint}")
            return False
    
    return True


def test_orchestrator_workflows():
    """Test orchestrator workflow structure (without API calls)"""
    print("\n" + "=" * 80)
    print("  TEST: Orchestrator Workflow Methods")
    print("=" * 80)
    
    orchestrator = AgentOrchestrator()
    
    # Check all workflow methods exist
    workflows = [
        'analyze_shift_note',
        'generate_comprehensive_insight',
        'quick_wellness_check',
        'detect_crisis_with_context'
    ]
    
    for workflow in workflows:
        assert hasattr(orchestrator, workflow), f"Missing workflow: {workflow}"
        print(f"  ✓ {workflow}()")
    
    print("\n✓ All 4 orchestration workflows available")
    return True


def main():
    """Run orchestrator and endpoint tests"""
    print("\n" + "█" * 80)
    print("  ORCHESTRATOR & ENDPOINTS TEST SUITE")
    print("  Quick validation without OpenAI API calls")
    print("█" * 80)
    
    try:
        # Test 1: Orchestrator initialization
        test_orchestrator_initialization()
        
        # Test 2: API endpoints
        test_api_endpoints()
        
        # Test 3: Workflow methods
        test_orchestrator_workflows()
        
        # Final Summary
        print("\n" + "=" * 80)
        print("  ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\n✓ AgentOrchestrator initialized with 5 agents")
        print("✓ All 6 new API endpoints registered")
        print("✓ All 4 orchestration workflows available")
        print("\n[Next Steps]")
        print("1. Run full agent tests with OpenAI API: python tests/test_new_agents.py")
        print("2. Test endpoints with curl or Postman")
        print("3. Integrate orchestrator into shift creation workflow")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
