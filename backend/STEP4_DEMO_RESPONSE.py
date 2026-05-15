"""
STEP 4 DEMO: Sample API Response with gemma_verdict
====================================================

When single_predict() is called with a real image and clinical_ga_weeks,
the response now includes the Step 4 gemma_verdict field populated by
the new generate_gemini_verdict() function.

EXAMPLE RESPONSE (with Step 4):
"""

sample_response = {
    # Measurement fields
    "hc_pixels": 95.3,
    "hc_mm": 38.2,
    "calibration": "spacing",
    "center": (128.5, 96.2),
    "axes": (32.1, 29.8),
    "angle": 0.524,
    
    # Step 2: Confidence metrics
    "confidence": 0.87,
    "confidence_detail": {
        "mask_area_ratio": 0.15,
        "foreground_threshold": 0.5,
        "ellipse_valid": True,
    },
    
    # Step 5: Quality flag
    "quality_flag": "HIGH",
    "quality_reasons": [],
    
    # Step 3: Growth classification
    "ga_weeks_from_hc": 20.5,
    "growth_code": "NORMAL",
    "growth_detail": {
        "clinical_ga_weeks": 20.0,
        "hc_ga_minus_clinical_weeks": 0.5,
        "normal_band_weeks": 2.0,
    },
    "growth_reasons": [],
    
    # STEP 4: Gemini verdict (NEW)
    "gemma_verdict": (
        "Head circumference is consistent with expected size for reported "
        "gestational age. No growth concerns detected."
    ),
    
    # Metadata
    "image_path": "/path/to/image.png",
}

print(__doc__)
print(f"\nResponse Structure:")
import json
print(json.dumps(sample_response, indent=2))

print("\n" + "=" * 70)
print("STEP 4 FIELDS EXPLAINED:")
print("=" * 70)
print("""
gemma_verdict (str | None):
  - Short LLM-generated explanation of growth classification
  - Non-diagnostic; decision support only (UI shows disclaimer)
  - Never contradicts growth_code (guardrails enforce this)
  - Falls back to static template if Gemini API unavailable/fails
  - Currently using templates in demo mode (switch to live Gemini later)

How it's generated:
  1. growth_code = "NORMAL" (from Step 3)
  2. Structured prompt sent to ChatGoogleGenerativeAI with:
     - growth_code, clinical_ga_weeks, hc_ga_weeks, delta
     - Instruction: "Do not change the category; only explain it"
  3. Response validated against growth_code keywords
  4. If valid: returned as gemma_verdict
  5. If invalid/error: template used instead

API Integration:
  - GOOGLE_API_KEY from .env (same as auto_fetal_biometry.py)
  - Model: gemini-2.5-flash with temperature=0
  - Graceful fallback: template if API key missing or API fails
""")
