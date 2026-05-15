"""
Quick sanity checks for sigmoid confidence metrics (no model weights required).

Run from this directory with venv activated:
    py confidence_quick_test.py
"""
from __future__ import annotations

import numpy as np

from single_predict import (
    FOREGROUND_THRESHOLD,
    _clinical_response_fields,
    _compute_quality_flag_and_reasons,
    compute_sigmoid_confidence_metrics,
)


def main() -> None:
    h, w = 64, 96
    empty = np.zeros((h, w), dtype=np.float32)
    r0 = compute_sigmoid_confidence_metrics(empty)
    assert r0["confidence"] is None
    assert r0["foreground_empty"] is True
    assert "empty_segmentation_foreground" in _clinical_response_fields(
        sigmoid_metrics=r0,
    )["quality_reasons"]

    block = np.zeros((h, w), dtype=np.float32)
    block[10:30, 20:50] = 0.9
    r1 = compute_sigmoid_confidence_metrics(block)
    assert r1["confidence"] is not None
    assert 0.89 < r1["confidence"] <= 0.91
    assert r1["foreground_threshold"] == FOREGROUND_THRESHOLD
    assert r1["mask_area_ratio"] > 0

    c1 = _clinical_response_fields(sigmoid_metrics=r1)
    assert c1["quality_flag"] in ("HIGH", "MEDIUM", "LOW")
    assert c1["confidence"] == r1["confidence"]

    q_bad, _ = _compute_quality_flag_and_reasons(0.99, ellipse_valid=False)
    assert q_bad == "LOW"

    q_seg, _ = _compute_quality_flag_and_reasons(0.99, ellipse_valid=None)
    assert q_seg == "HIGH"

    print("confidence_quick_test: all checks passed")


if __name__ == "__main__":
    main()
