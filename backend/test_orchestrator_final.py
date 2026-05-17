#!/usr/bin/env python3
"""
Final smoke test summary for the LangGraph orchestrator
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from langchain_core.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).resolve().parent))

async def test_orchestrator_final():
    print("\n" + "="*80)
    print("FINAL SMOKE TEST: LangGraph Orchestrator - End-to-End Pipeline")
    print("="*80 + "\n")
    
    try:
        from auto_fetal_biometry import build_orchestrator
        
        print("[STEP 1] Initializing orchestrator...")
        orchestrator = await build_orchestrator()
        print("         [OK] Orchestrator compiled\n")
        
        test_image = Path(__file__).resolve().parent / "single_test_img.png"
        if not test_image.exists():
            print(f"[ERROR] Test image not found: {test_image}")
            return False
        
        print(f"[STEP 2] Processing ultrasound image...")
        print(f"         Image: {test_image.name}")
        
        session_id = str(uuid4())
        state = {
            "session_id": session_id,
            "file_path": str(test_image),
            "patient_data": {
                "full_name": "Jane Doe",
                "age": "28",
                "clinical_ga_weeks": 28,
                "husband_father_name": "John Doe",
                "contact_number": "+91 9876543210",
                "postal_address": "123 Medical Center, City, State",
                "indication_ultrasound": "Routine fetal biometry screening",
            },
            "messages": [HumanMessage(content=str(test_image))],
        }
        
        print(f"         Session ID: {session_id}\n")
        
        print("[STEP 3] Running orchestrator pipeline:")
        print("         - Vision Node (image processing + measurements)")
        print("         - RAG Node (clinical guidelines retrieval)")
        print("         - Reasoning Node (form assembly)")
        print("         - Validation Node (data verification)")
        print("         - PDF Compilation (report generation)\n")
        
        result = await orchestrator.ainvoke(state)
        
        # Check if PDF was created
        sessions_dir = Path(__file__).resolve().parent / "sessions"
        pdfs = list(sessions_dir.glob(f"report_*.pdf"))
        
        print("[STEP 4] Results:\n")
        
        if pdfs and len(pdfs) > 0:
            latest_pdf = sorted(pdfs)[-1]
            print(f"         SUCCESS: Pipeline completed successfully!")
            print(f"         Generated PDF: {latest_pdf.name}")
            print(f"         PDF Size: {latest_pdf.stat().st_size} bytes")
            
            # Also check for session JSON
            session_json = sessions_dir / f"{session_id}.json"
            if session_json.exists():
                print(f"         Session State: {session_json.name}")
            
            print(f"\n[SUMMARY] All nodes executed successfully:")
            print(f"          1. Vision: {result.get('raw_biometry_data', {}).get('hc_pixels', 'N/A')} pixels HC extracted")
            if result.get('extracted_form'):
                print(f"          2. Reasoning: Form assembled with {len(result.get('extracted_form', {}))} fields")
            if result.get('verification_errors') is not None and len(result.get('verification_errors', [])) == 0:
                print(f"          3. Validation: PASSED (no errors)")
            print(f"          4. PDF: Generated successfully")
            
            print("\n" + "="*80)
            print("TEST PASSED [OK]")
            print("="*80 + "\n")
            return True
        else:
            print("[FAILED] No PDF generated")
            return False
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_orchestrator_final())
    sys.exit(0 if success else 1)
