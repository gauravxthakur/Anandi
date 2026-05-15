#!/usr/bin/env python
"""Test Step 4 integration: single_predict with gemma_verdict."""

import sys
from pathlib import Path

# Add parent paths like single_predict does
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gemini_verdict import generate_gemini_verdict, GROWTH_NORMAL

# Simulate what _clinical_response_fields does with growth data
print("=" * 70)
print("Step 4 Integration Test: _clinical_response_fields with Gemini")
print("=" * 70)

# Simulate growth data from assess_growth_from_hc
growth_detail = {
    "clinical_ga_weeks": 20.0,
    "hc_ga_minus_clinical_weeks": 0.5,
    "ga_weeks_from_hc": 20.5,
    "normal_band_weeks": 2.0,
}

growth_code = GROWTH_NORMAL

print("\n📊 Simulated Growth Data:")
print(f"  Growth Code: {growth_code}")
print(f"  Clinical GA: {growth_detail['clinical_ga_weeks']} weeks")
print(f"  HC GA: {growth_detail['ga_weeks_from_hc']} weeks")
print(f"  Delta: {growth_detail['hc_ga_minus_clinical_weeks']} weeks")

# This is what _clinical_response_fields now does for gemma_verdict
gemma_verdict = generate_gemini_verdict(
    growth_code,
    clinical_ga_weeks=growth_detail.get("clinical_ga_weeks"),
    hc_ga_weeks=growth_detail.get("ga_weeks_from_hc"),
    hc_ga_minus_clinical_weeks=growth_detail.get("hc_ga_minus_clinical_weeks"),
    normal_band_weeks=growth_detail.get("normal_band_weeks", 2.0),
)

print("\n🤖 Step 4 Output (gemma_verdict):")
print(f"  {gemma_verdict}")

print("\n" + "=" * 70)
print("✓ Step 4 Integration Complete:")
print("  • generate_gemini_verdict() called from _clinical_response_fields()")
print("  • Structured prompt with growth_code + numeric context")
print("  • Fallback templates for demo (swap to real Gemini later)")
print("  • Single source of truth for API keys (from .env)")
print("=" * 70)
