#!/usr/bin/env python3
"""
Quick smoke test for the orchestrator with sample image.
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from langchain_core.messages import HumanMessage

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

async def test_orchestrator():
    print("=" * 80)
    print("SMOKE TEST: LangGraph Orchestrator")
    print("=" * 80)
    
    try:
        # Import after sys.path setup
        from auto_fetal_biometry import build_orchestrator
        
        # Build orchestrator
        print("\n[1] Building orchestrator...")
        orchestrator = await build_orchestrator()
        print("[OK] Orchestrator built successfully")
        
        # Test with sample image
        test_image = Path(__file__).resolve().parent / "single_test_img.png"
        if not test_image.exists():
            print(f"[ERROR] Test image not found: {test_image}")
            return
        
        print(f"\n[2] Testing with image: {test_image}")
        
        # Create test state
        state = {
            "session_id": str(uuid4()),
            "file_path": str(test_image),
            "patient_data": {
                "full_name": "Test Patient",
                "age": "28",
                "clinical_ga_weeks": 28,
                "husband_father_name": "Test Father",
                "contact_number": "+91 1234567890",
                "postal_address": "123 Test St",
                "indication_ultrasound": "Fetal biometry screening",
            },
            "messages": [HumanMessage(content=str(test_image))],
        }
        
        print(f"   Session ID: {state['session_id']}")
        print(f"   Patient: {state['patient_data']['full_name']}, GA: {state['patient_data']['clinical_ga_weeks']} weeks")
        
        # Run orchestrator
        print("\n[3] Invoking orchestrator...")
        result = await orchestrator.ainvoke(state)
        
        print("\n[4] Results:")
        print(f"   Full result: {result}")
        print(f"   Status: {result.get('status')}")
        if result.get('status') == 'completed':
            print(f"   [OK] PDF Path: {result.get('pdf_path')}")
        elif result.get('status') == 'needs_human':
            print(f"   [WARN] Needs human review:")
            print(f"     Thread ID: {result.get('thread_id')}")
            print(f"     Errors: {result.get('verification_errors')}")
            print(f"     Preview Payload: {result.get('preview_payload')}")
        else:
            print(f"   [ERROR] {result.get('error')}")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_orchestrator())
    sys.exit(0 if result else 1)
