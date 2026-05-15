"""
Single image prediction for fetal head biometry.

Prediction response contract (single source of truth for API / UI keys):

    hc_pixels (float | None)
        Head circumference in upsampled pixel units when the ellipse + HC
        path succeeds; ``None`` if geometry checks fail.
    hc_mm (float | None)
        HC in millimeters only when ``pixel_spacing_mm`` is supplied and valid;
        otherwise None.
    calibration (str)
        ``"none"`` — no mm conversion; ``"spacing"`` — ``hc_mm`` from spacing.
    confidence (float | None)
        Mean sigmoid activation on foreground (pixels with p > τ); ``None`` if
        no foreground pixels.
    confidence_detail (dict)
        mask_area_ratio, foreground_threshold, ellipse_valid (ellipse path only).
    quality_flag (str)
        ``HIGH`` | ``MEDIUM`` | ``LOW`` from mask confidence and ellipse validity.
    quality_reasons (list[str])
        Machine-readable explanations for judges / support.
    ga_weeks_from_hc (float | None)
        Hadlock gestational age (weeks) estimated from ``hc_mm`` when in range.
    growth_code (str)
        ``NORMAL`` | ``SMALL_FOR_GA`` | ``LARGE_FOR_GA`` | ``INSUFFICIENT_DATA``.
        Requires ``hc_mm`` and ``clinical_ga_weeks`` for classification.
    growth_detail (dict)
        ``clinical_ga_weeks``, ``hc_ga_minus_clinical_weeks``, ``normal_band_weeks``.
    growth_reasons (list[str])
        Why growth is ``INSUFFICIENT_DATA`` when applicable.
    growth_verdict (str | None)
        Short non-diagnostic explanation of the growth classification.

Latency: :func:`get_inference_model` caches CSM per device. The first request on a
device pays weight load + a short inference warmup; repeat scans in the same process
are much faster (typical for live demo / API workers).
"""
from __future__ import annotations

import argparse
import sys
import time
from typing import Any, Dict, List, Optional

import torch
import cv2
import numpy as np

from pathlib import Path
from modules import CSM, mcc_edge, ellip_fit

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from project_paths import Paths
from pixel_to_mm import convert_hc_to_mm, validate_pixel_spacing
from growth_assessment import assess_growth_from_hc
from gemini_verdict import generate_growth_verdict

# Foreground mask for mean activation (sigmoid output is in [0, 1]).
FOREGROUND_THRESHOLD = 0.5

# CSM weights are loaded once per process per device (see :func:`get_inference_model`).
# The first request on a device also runs a short CUDA/cuDNN warmup; later calls reuse both.
_MODEL_BY_DEVICE: Dict[str, torch.nn.Module] = {}
_WARMED_DEVICES: set[str] = set()
_INFERENCE_WARMUP_PASSES = 2


def _resolve_device(device: str) -> str:
    if device == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return device


def get_inference_model(device: str = "cuda") -> tuple[torch.nn.Module, str, float]:
    """
    Return the shared CSM instance for ``device``.

    Loads ``Paths.MODEL_TEST`` once per process per device. Subsequent calls return
    the cached module with ~0 ms load time.
    """
    device = _resolve_device(device)
    load_start = time.time()
    if device not in _MODEL_BY_DEVICE:
        net = CSM()
        state = torch.load(Paths.MODEL_TEST, map_location=device, weights_only=True)
        net.load_state_dict(state)
        net.to(device)
        net.eval()
        _MODEL_BY_DEVICE[device] = net
    load_ms = (time.time() - load_start) * 1000
    return _MODEL_BY_DEVICE[device], device, load_ms


def preload_inference_model(device: str = "cuda") -> None:
    """Eager-load weights at app startup so the first scan avoids disk I/O."""
    get_inference_model(device)


def _warmup_inference(
    net: torch.nn.Module,
    device: str,
    input_img: torch.Tensor,
    *,
    passes: int = _INFERENCE_WARMUP_PASSES,
) -> float:
    """Run cuDNN autotune warmups once per device; return elapsed ms."""
    if device in _WARMED_DEVICES:
        return 0.0
    start = time.time()
    with torch.inference_mode():
        for _ in range(passes):
            net(input_img)
            if device == "cuda":
                torch.cuda.synchronize()
    _WARMED_DEVICES.add(device)
    return (time.time() - start) * 1000


def compute_sigmoid_confidence_metrics(
    prob: np.ndarray,
    *,
    tau: float = FOREGROUND_THRESHOLD,
) -> Dict[str, Any]:
    """
    Derive confidence from the raw model probability map (before binarization).

    Foreground is ``prob > tau``. ``confidence`` is the mean of ``prob`` over
    those pixels. If there are no foreground pixels, ``confidence`` is None.
    """
    prob = np.asarray(prob, dtype=np.float64)
    if prob.ndim != 2:
        raise ValueError("prob must be a 2D HxW array")
    prob = np.clip(prob, 0.0, 1.0)
    fg = prob > tau
    n_fg = int(fg.sum())
    h, w = prob.shape
    mask_area_ratio = n_fg / float(h * w)
    if n_fg == 0:
        return {
            "confidence": None,
            "mask_area_ratio": mask_area_ratio,
            "foreground_threshold": tau,
            "foreground_empty": True,
        }
    return {
        "confidence": float(prob[fg].mean()),
        "mask_area_ratio": mask_area_ratio,
        "foreground_threshold": tau,
        "foreground_empty": False,
    }


def _compute_laplacian_variance(prob: np.ndarray) -> Optional[float]:
    """
    Compute Laplacian variance (image blur metric).
    Higher variance = sharper image; lower variance = blurred image.
    
    Args:
        prob: 2D probability map (HxW) in [0, 1].
    
    Returns:
        Laplacian variance or None if image is too small.
    """
    prob_uint8 = (prob * 255).astype(np.uint8)
    if prob_uint8.shape[0] < 3 or prob_uint8.shape[1] < 3:
        return None
    laplacian = cv2.Laplacian(prob_uint8, cv2.CV_64F)
    variance = float(laplacian.var())
    return variance


def _compute_quality_flag_and_reasons(
    confidence: Optional[float],
    *,
    ellipse_valid: Optional[bool] = None,
    mask_area_ratio: Optional[float] = None,
    prob_map: Optional[np.ndarray] = None,
    confidence_low_cutoff: float = 0.5,
    confidence_high_cutoff: float = 0.8,
    mask_area_min: float = 0.05,
    mask_area_max: float = 0.40,
    blur_variance_cutoff: float = 50.0,
) -> tuple[str, List[str]]:
    """
    Compute quality_flag and quality_reasons based on multiple criteria.
    
    Criteria:
    - Ellipse validity: invalid → LOW
    - Confidence: < low_cutoff → LOW; < high_cutoff → MEDIUM; >= high_cutoff → HIGH
    - Mask area: ratio outside [min, max] range → downgrade to MEDIUM/LOW
    - Blur: Laplacian variance < blur_cutoff → downgrade to MEDIUM
    
    Args:
        confidence: Mean sigmoid on foreground [0, 1] or None.
        ellipse_valid: Whether ellipse fit succeeded.
        mask_area_ratio: Foreground pixels / total pixels [0, 1].
        prob_map: Raw probability map for blur detection (optional).
        confidence_low_cutoff: Confidence threshold for LOW (default 0.5).
        confidence_high_cutoff: Confidence threshold for MEDIUM→HIGH (default 0.8).
        mask_area_min: Min plausible mask area ratio (default 0.05).
        mask_area_max: Max plausible mask area ratio (default 0.40).
        blur_variance_cutoff: Laplacian variance threshold for blur (default 50.0).
    
    Returns:
        (quality_flag, quality_reasons): e.g., ("HIGH", ["confidence_high", ...])
    """
    reasons: List[str] = []
    base_flag = "HIGH"
    
    # Check 1: Ellipse validity is critical
    if ellipse_valid is False:
        base_flag = "LOW"
        reasons.append("ellipse_geometry_invalid")
    
    # Check 2: Confidence thresholds
    if confidence is None:
        base_flag = min(base_flag, "LOW", key=lambda x: {"HIGH": 2, "MEDIUM": 1, "LOW": 0}[x])
        reasons.append("confidence_unavailable")
    elif confidence < confidence_low_cutoff:
        base_flag = min(base_flag, "LOW", key=lambda x: {"HIGH": 2, "MEDIUM": 1, "LOW": 0}[x])
        reasons.append(f"confidence_low_{confidence:.2f}")
    elif confidence < confidence_high_cutoff:
        base_flag = min(base_flag, "MEDIUM", key=lambda x: {"HIGH": 2, "MEDIUM": 1, "LOW": 0}[x])
        reasons.append(f"confidence_medium_{confidence:.2f}")
    else:
        reasons.append(f"confidence_high_{confidence:.2f}")
    
    # Check 3: Mask area plausibility
    if mask_area_ratio is not None:
        if mask_area_ratio < mask_area_min:
            base_flag = min(base_flag, "MEDIUM", key=lambda x: {"HIGH": 2, "MEDIUM": 1, "LOW": 0}[x])
            reasons.append(f"mask_area_too_small_{mask_area_ratio:.4f}")
        elif mask_area_ratio > mask_area_max:
            base_flag = min(base_flag, "MEDIUM", key=lambda x: {"HIGH": 2, "MEDIUM": 1, "LOW": 0}[x])
            reasons.append(f"mask_area_too_large_{mask_area_ratio:.4f}")
        else:
            reasons.append(f"mask_area_valid_{mask_area_ratio:.4f}")
    
    # Check 4: Blur detection (optional second pass)
    if prob_map is not None:
        blur_var = _compute_laplacian_variance(prob_map)
        if blur_var is not None:
            if blur_var < blur_variance_cutoff:
                base_flag = min(base_flag, "MEDIUM", key=lambda x: {"HIGH": 2, "MEDIUM": 1, "LOW": 0}[x])
                reasons.append(f"possible_blur_{blur_var:.1f}")
            else:
                reasons.append(f"sharpness_ok_{blur_var:.1f}")
    
    return base_flag, reasons


def _clinical_response_fields(
    *,
    hc_pixels: Optional[float] = None,
    pixel_spacing_mm: Optional[float] = None,
    clinical_ga_weeks: Optional[float] = None,
    hc_mm: Optional[float] = None,
    sigmoid_metrics: Optional[Dict[str, Any]] = None,
    ellipse_valid: Optional[bool] = None,
    prob_map: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Dashboard / API fields shared by all ``single_predict`` return variants.

    ``sigmoid_metrics`` comes from :func:`compute_sigmoid_confidence_metrics``.
    ``ellipse_valid`` is set only on the full ellipse + HC path; else ``None``.
    Pass ``clinical_ga_weeks`` from patient intake for Hadlock growth classification.
    ``prob_map`` is the raw [0,1] probability map used for blur detection.
    """
    sm = sigmoid_metrics or {}
    confidence: Optional[float] = sm.get("confidence")
    mask_area_ratio: Optional[float] = sm.get("mask_area_ratio")
    foreground_threshold: Optional[float] = sm.get("foreground_threshold")
    foreground_empty: bool = bool(sm.get("foreground_empty"))
    ran_sigmoid = bool(sm)

    calibration = "none"
    reasons: List[str] = []

    if hc_mm is None and hc_pixels is not None and pixel_spacing_mm is not None:
        if validate_pixel_spacing(pixel_spacing_mm):
            hc_mm = float(convert_hc_to_mm(hc_pixels, pixel_spacing_mm))
            calibration = "spacing"
        else:
            reasons.append("invalid_pixel_spacing")
    elif hc_mm is not None:
        calibration = "spacing"

    if not ran_sigmoid:
        reasons.append("confidence_not_computed")
    elif foreground_empty:
        reasons.append("empty_segmentation_foreground")

    # Compute quality_flag with comprehensive criteria
    quality_flag, quality_detail_reasons = _compute_quality_flag_and_reasons(
        confidence,
        ellipse_valid=ellipse_valid,
        mask_area_ratio=mask_area_ratio,
        prob_map=prob_map,
    )
    reasons.extend(quality_detail_reasons)

    growth = assess_growth_from_hc(hc_mm, clinical_ga_weeks=clinical_ga_weeks)
    reasons.extend(growth.get("growth_reasons") or [])

    growth_code = growth.get("growth_code")
    growth_detail = growth.get("growth_detail") or {}
    growth_verdict = generate_growth_verdict(
        growth_code,
        clinical_ga_weeks=growth_detail.get("clinical_ga_weeks"),
        hc_ga_weeks=growth_detail.get("ga_weeks_from_hc"),
        hc_ga_minus_clinical_weeks=growth_detail.get("hc_ga_minus_clinical_weeks"),
        normal_band_weeks=growth_detail.get("normal_band_weeks", 2.0),
    )

    return {
        "calibration": calibration,
        "hc_mm": hc_mm,
        "confidence": confidence,
        "confidence_detail": {
            "mask_area_ratio": mask_area_ratio,
            "foreground_threshold": foreground_threshold,
            "ellipse_valid": ellipse_valid,
        },
        "quality_flag": quality_flag,
        "quality_reasons": reasons,
        "ga_weeks_from_hc": growth["ga_weeks_from_hc"],
        "growth_code": growth["growth_code"],
        "growth_detail": growth["growth_detail"],
        "growth_reasons": growth.get("growth_reasons") or [],
        "growth_verdict": growth_verdict,
    }


def single_predict(
    image_path,
    device="cuda",
    seg_only=False,
    no_ellipse=False,
    pixel_spacing_mm: Optional[float] = None,
    clinical_ga_weeks: Optional[float] = None,
):
    """
    Run HC segmentation and optional ellipse fit.

    Args:
        image_path: Path to grayscale ultrasound frame.
        device: ``cuda`` or ``cpu``.
        seg_only: If True, return uint8 mask only (plus clinical envelope).
        no_ellipse: If True, return edge image only (plus clinical envelope).
        pixel_spacing_mm: When set and valid, ``hc_mm`` is filled on the full
            ellipse return path; otherwise ``hc_mm`` is null and
            ``calibration`` is ``none``.
        clinical_ga_weeks: Documented gestational age from intake (weeks).
            With ``hc_mm``, enables Hadlock ``growth_code`` classification.
    """
    wall_start = time.time()
    # CUDA sanity check
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Using device: {torch.cuda.get_device_name(0)}")
    else:
        print(f"WARNING: CUDA not available, falling back to CPU")
        device = 'cpu'
    
    # Runtime diagnostics
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA version: {torch.version.cuda}")
    print(f"cuDNN available: {torch.backends.cudnn.is_available()}")
    print(f"cuDNN enabled: {torch.backends.cudnn.enabled}")
    if torch.backends.cudnn.is_available():
        print(f"cuDNN version: {torch.backends.cudnn.version()}")
    
    # Start total timer
    total_start = time.time()
    
    load_start = time.time()
    net, device, _ = get_inference_model(device)
    load_end = time.time()
    print(f"Model device: {next(net.parameters()).device}")
    if load_end - load_start > 0.01:
        print(
            "Note: first request in this process loads weights and warms up CUDA; "
            "later scans reuse the cached model."
        )
    
    # Load and preprocess image
    preprocess_start = time.time()
    img = cv2.imread(image_path, 0)
    if img is None:
        print(f"Error: Cannot load image from {image_path}")
        return
    
    # Resize factor (same as predict.py)
    k1 = 4
    w = int(768 / k1)
    h = int(512 / k1)
    
    # Preprocess (same as predict.py)
    input_img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    input_img = input_img.astype('float32')
    input_img = input_img / 255.0
    
    # To torch.tensor (same as predict.py)
    input_img = torch.from_numpy(input_img)
    input_img = input_img.unsqueeze(0)
    input_img = input_img.unsqueeze(0)
    input_img = input_img.to(device)
    
    # Confirm input tensor device
    print(f"Input tensor device: {input_img.device}")
    
    preprocess_end = time.time()
    
    warmup_ms = _warmup_inference(net, device, input_img)

    if device == 'cuda':
        torch.cuda.synchronize()
    forward_start = time.time()
    with torch.inference_mode():
        _, _, predict = net(input_img)
    if device == 'cuda':
        torch.cuda.synchronize()
    forward_end = time.time()
    
    # GPU->CPU: keep raw sigmoid probabilities in [0, 1] for confidence; then
    # binarize the same way as before (round -> *255 -> uint8) for mcc_edge.
    to_cpu_start = time.time()
    prob_map = predict[0, 0].detach().float().cpu().numpy()
    sigmoid_metrics = compute_sigmoid_confidence_metrics(prob_map)
    predict_uint8 = (np.round(prob_map) * 255).astype(np.uint8)
    to_cpu_end = time.time()

    if seg_only:
        total_end = time.time()
        print(f"\n=== Timing Breakdown ===")
        print(f"Model load time: {(load_end - load_start)*1000:.2f} ms")
        print(f"Preprocess time: {(preprocess_end - preprocess_start)*1000:.2f} ms")
        print(f"Warmup time: {warmup_ms:.2f} ms")
        print(f"Forward pass time: {(forward_end - forward_start)*1000:.2f} ms")
        print(f"GPU->CPU transfer time: {(to_cpu_end - to_cpu_start)*1000:.2f} ms")
        print(f"Postprocess + ellipse time: 0.00 ms")
        print(f"Total time: {(total_end - total_start)*1000:.2f} ms")

        wall_end = time.time()
        print(f"Wall time (single_predict, incl prints): {(wall_end - wall_start)*1000:.2f} ms")
        return {
            "predict_mask_uint8": predict_uint8,
            "image_path": image_path,
            **_clinical_response_fields(
                sigmoid_metrics=sigmoid_metrics,
                clinical_ga_weeks=clinical_ga_weeks,
                prob_map=prob_map,
            ),
        }
    
    # Postprocess - extract edge (same as postprocess.py)
    postprocess_start = time.time()
    edge_img = mcc_edge(predict_uint8)

    if no_ellipse:
        postprocess_end = time.time()
        total_end = time.time()
        print(f"\n=== Timing Breakdown ===")
        print(f"Model load time: {(load_end - load_start)*1000:.2f} ms")
        print(f"Preprocess time: {(preprocess_end - preprocess_start)*1000:.2f} ms")
        print(f"Warmup time: {warmup_ms:.2f} ms")
        print(f"Forward pass time: {(forward_end - forward_start)*1000:.2f} ms")
        print(f"GPU->CPU transfer time: {(to_cpu_end - to_cpu_start)*1000:.2f} ms")
        print(f"Postprocess + ellipse time: {(postprocess_end - postprocess_start)*1000:.2f} ms")
        print(f"Total time: {(total_end - total_start)*1000:.2f} ms")

        wall_end = time.time()
        print(f"Wall time (single_predict, incl prints): {(wall_end - wall_start)*1000:.2f} ms")
        return {
            "edge_img_uint8": edge_img,
            "image_path": image_path,
            **_clinical_response_fields(
                sigmoid_metrics=sigmoid_metrics,
                clinical_ga_weeks=clinical_ga_weeks,
                prob_map=prob_map,
            ),
        }
    
    # Ellipse fitting (same as ellip_fit.py)
    xc, yc, theta, a, b = ellip_fit(edge_img)

    # Calculate head circumference (same as ellip_fit.py)
    u = 16  # upsample factor

    # 1. Restore Center Coordinates
    xc = (xc + 0.5) * u - 0.5
    yc = (yc + 0.5) * u - 0.5

    # 2. CALIBRATION: Subtract offset
    offset = 0.05
    a = (a - offset) * u
    b = (b - offset) * u

    # 3. RAMANUJAN'S FORMULA for head circumference
    h = ((a - b) ** 2) / ((a + b) ** 2) if abs(a + b) > 1e-12 else np.nan
    radicand = 4 - 3 * h
    if not (np.isfinite(h) and np.isfinite(radicand) and radicand >= 0):
        hc = float("nan")
    else:
        hc = np.pi * (a + b) * (1 + (3 * h) / (10 + np.sqrt(radicand)))

    ellipse_valid = bool(
        np.isfinite(hc)
        and hc > 0
        and np.isfinite(xc)
        and np.isfinite(yc)
        and np.isfinite(theta)
        and np.isfinite(a)
        and np.isfinite(b)
        and min(abs(a), abs(b)) > 1e-3
    )
    postprocess_end = time.time()
    
    # End total timer
    total_end = time.time()
    
    # Print timing breakdown
    print(f"\n=== Timing Breakdown ===")
    print(f"Model load time: {(load_end - load_start)*1000:.2f} ms")
    print(f"Preprocess time: {(preprocess_end - preprocess_start)*1000:.2f} ms")
    print(f"Warmup time: {warmup_ms:.2f} ms")
    print(f"Forward pass time: {(forward_end - forward_start)*1000:.2f} ms")
    print(f"GPU->CPU transfer time: {(to_cpu_end - to_cpu_start)*1000:.2f} ms")
    print(f"Postprocess + ellipse time: {(postprocess_end - postprocess_start)*1000:.2f} ms")
    print(f"Total time: {(total_end - total_start)*1000:.2f} ms")
    
    # Display results
    print(f"\n=== Fetal Head Circumference Measurement ===")
    print(f"Image: {image_path}")
    if ellipse_valid:
        print(f"Head Circumference: {hc:.2f} pixels")
        print(f"Center: ({xc:.2f}, {yc:.2f}) pixels")
        print(f"Semi-axes: a={a:.2f}, b={b:.2f} pixels")
        print(f"Angle: {theta:.4f} radians")
    else:
        print("Head Circumference: invalid (ellipse geometry check failed)")

    wall_end = time.time()
    print(f"Wall time (single_predict, incl prints): {(wall_end - wall_start)*1000:.2f} ms")
    
    # Return measurement data + shared clinical/dashboard keys
    clinical = _clinical_response_fields(
        hc_pixels=float(hc) if ellipse_valid else None,
        pixel_spacing_mm=pixel_spacing_mm,
        clinical_ga_weeks=clinical_ga_weeks,
        sigmoid_metrics=sigmoid_metrics,
        ellipse_valid=ellipse_valid,
        prob_map=prob_map,
    )
    return {
        "hc_pixels": hc if ellipse_valid else None,
        "center": (xc, yc) if ellipse_valid else None,
        "axes": (a, b) if ellipse_valid else None,
        "angle": theta if ellipse_valid else None,
        "image_path": image_path,
        **clinical,
    }

if __name__ == "__main__":
    script_start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('image_path')
    parser.add_argument('--seg-only', action='store_true')
    parser.add_argument('--no-ellipse', action='store_true')
    parser.add_argument("--pixel-spacing-mm", type=float, default=None,
                        help="Pixel spacing in mm/pixel for hc_mm on full prediction path")
    parser.add_argument("--clinical-ga-weeks", type=float, default=None,
                        help="Clinical gestational age in weeks (from intake) for growth_code")
    args = parser.parse_args()

    image_path = args.image_path

    # Run single prediction first
    single_predict(
        image_path,
        seg_only=args.seg_only,
        no_ellipse=args.no_ellipse,
        pixel_spacing_mm=args.pixel_spacing_mm,
        clinical_ga_weeks=args.clinical_ga_weeks,
    )

    if args.seg_only or args.no_ellipse:
        script_end = time.time()
        print(f"Wall time (full script): {(script_end - script_start)*1000:.2f} ms")
        sys.exit(0)
    
    print("\n=== In-process microbenchmark ===")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    net, device, _ = get_inference_model(device)
    
    # Prepare input tensor once
    img = cv2.imread(image_path, 0)
    k1 = 4
    w = int(768 / k1)
    h = int(512 / k1)
    input_img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    input_img = input_img.astype('float32') / 255.0
    input_img = torch.from_numpy(input_img).unsqueeze(0).unsqueeze(0).to(device)
    
    # Warmup runs
    print("Warmup runs (5 iterations):")
    for i in range(5):
        with torch.inference_mode():
            _, _, predict = net(input_img)
        if device == 'cuda':
            torch.cuda.synchronize()
    
    # Benchmark runs
    print("Benchmark runs (20 iterations):")
    times = []
    for i in range(20):
        start = time.time()
        if device == 'cuda':
            torch.cuda.synchronize()
        with torch.inference_mode():
            _, _, predict = net(input_img)
        if device == 'cuda':
            torch.cuda.synchronize()
        end = time.time()
        times.append((end - start) * 1000)
    
    print(f"Forward pass times (ms): min={min(times):.2f}, max={max(times):.2f}, mean={sum(times)/len(times):.2f}")
    
    script_end = time.time()
    print(f"Wall time (full script): {(script_end - script_start)*1000:.2f} ms")