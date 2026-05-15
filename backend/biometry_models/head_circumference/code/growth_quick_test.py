"""
Quick tests for Hadlock growth classification (no model weights).

Run:
    py "d:\\auto fetal biometry\\backend\\biometry_models\\head_circumference\\code\\growth_quick_test.py"
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from growth_assessment import (
    GROWTH_INSUFFICIENT_DATA,
    GROWTH_LARGE_FOR_GA,
    GROWTH_NORMAL,
    GROWTH_SMALL_FOR_GA,
    assess_growth_from_hc,
)

SAMPLE_HADLOCK = {
    "data": [
        {
            "gestational_age_weeks": 18,
            "hc_mean": 140,
            "bpd_mean": 40,
            "ac_mean": 120,
            "fl_mean": 25,
        },
        {
            "gestational_age_weeks": 20,
            "hc_mean": 160,
            "bpd_mean": 45,
            "ac_mean": 130,
            "fl_mean": 28,
        },
        {
            "gestational_age_weeks": 22,
            "hc_mean": 180,
            "bpd_mean": 50,
            "ac_mean": 140,
            "fl_mean": 30,
        },
    ]
}


def main() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(SAMPLE_HADLOCK, f)
        hadlock_path = Path(f.name)

    try:
        r0 = assess_growth_from_hc(None, clinical_ga_weeks=20, hadlock_json_path=hadlock_path)
        assert r0["growth_code"] == GROWTH_INSUFFICIENT_DATA
        assert "hc_mm_unavailable" in r0["growth_reasons"]

        r1 = assess_growth_from_hc(160.0, hadlock_json_path=hadlock_path)
        assert r1["ga_weeks_from_hc"] is not None
        assert abs(r1["ga_weeks_from_hc"] - 20.0) < 0.5
        assert r1["growth_code"] == GROWTH_INSUFFICIENT_DATA
        assert "clinical_ga_required_for_growth" in r1["growth_reasons"]

        r2 = assess_growth_from_hc(
            160.0, clinical_ga_weeks=20.0, hadlock_json_path=hadlock_path
        )
        assert r2["growth_code"] == GROWTH_NORMAL

        r3 = assess_growth_from_hc(
            160.0, clinical_ga_weeks=24.0, hadlock_json_path=hadlock_path
        )
        assert r3["growth_code"] == GROWTH_SMALL_FOR_GA

        r4 = assess_growth_from_hc(
            160.0, clinical_ga_weeks=16.0, hadlock_json_path=hadlock_path
        )
        assert r4["growth_code"] == GROWTH_LARGE_FOR_GA
    finally:
        hadlock_path.unlink(missing_ok=True)

    print("growth_quick_test: all checks passed")


if __name__ == "__main__":
    main()
