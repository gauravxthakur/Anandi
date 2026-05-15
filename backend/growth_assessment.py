"""
Hadlock-based gestational age from HC and growth classification vs clinical GA.

Growth compares HC-implied gestational age to documented clinical GA using a
fixed week band (default ±2 weeks), matching ``fetal_biometry_calculator``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

# HC-implied GA within this many weeks of clinical GA → NORMAL.
GROWTH_NORMAL_BAND_WEEKS = 2.0

GROWTH_NORMAL = "NORMAL"
GROWTH_SMALL_FOR_GA = "SMALL_FOR_GA"
GROWTH_LARGE_FOR_GA = "LARGE_FOR_GA"
GROWTH_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

_BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_HADLOCK_JSON = _BACKEND_DIR / "rag" / "data" / "hadlock.json"


def _lookup(hadlock_json_path: Optional[Path] = None):
    from rag.hadlock_lookup import HadlockLookup

    path = Path(hadlock_json_path) if hadlock_json_path else DEFAULT_HADLOCK_JSON
    return HadlockLookup(json_path=str(path))


def assess_growth_from_hc(
    hc_mm: Optional[float],
    *,
    clinical_ga_weeks: Optional[float] = None,
    normal_band_weeks: float = GROWTH_NORMAL_BAND_WEEKS,
    hadlock_json_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
  Compute ``ga_weeks_from_hc`` and ``growth_code`` from HC in millimeters.

  Requires ``clinical_ga_weeks`` to classify growth; without it,
  ``growth_code`` stays ``INSUFFICIENT_DATA`` but ``ga_weeks_from_hc`` may
  still be set when Hadlock lookup succeeds.
    """
    detail: Dict[str, Any] = {
        "clinical_ga_weeks": clinical_ga_weeks,
        "normal_band_weeks": normal_band_weeks,
        "hc_ga_minus_clinical_weeks": None,
    }
    reasons: list[str] = []

    if hc_mm is None:
        return {
            "ga_weeks_from_hc": None,
            "growth_code": GROWTH_INSUFFICIENT_DATA,
            "growth_detail": detail,
            "growth_reasons": ["hc_mm_unavailable"],
        }

    lookup = _lookup(hadlock_json_path)
    ga_hc = lookup.ga_for_hc(float(hc_mm))
    detail["ga_weeks_from_hc"] = ga_hc

    if ga_hc is None:
        return {
            "ga_weeks_from_hc": None,
            "growth_code": GROWTH_INSUFFICIENT_DATA,
            "growth_detail": detail,
            "growth_reasons": ["hadlock_hc_out_of_range"],
        }

    if clinical_ga_weeks is None:
        return {
            "ga_weeks_from_hc": float(ga_hc),
            "growth_code": GROWTH_INSUFFICIENT_DATA,
            "growth_detail": detail,
            "growth_reasons": ["clinical_ga_required_for_growth"],
        }

    clinical = float(clinical_ga_weeks)
    diff = float(ga_hc) - clinical
    detail["hc_ga_minus_clinical_weeks"] = diff

    if abs(diff) <= normal_band_weeks:
        code = GROWTH_NORMAL
    elif diff < -normal_band_weeks:
        # HC implies younger GA than documented → smaller head for dates.
        code = GROWTH_SMALL_FOR_GA
    else:
        code = GROWTH_LARGE_FOR_GA

    return {
        "ga_weeks_from_hc": float(ga_hc),
        "growth_code": code,
        "growth_detail": detail,
        "growth_reasons": reasons,
    }
