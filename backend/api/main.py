"""
HTTP API for fetal head circumference inference (Strike A) + optional Form F extract hook.

Run from repo root (Windows-friendly):

  py -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

BACKEND_ROOT = Path(__file__).resolve().parents[1]
HC_CODE_DIR = BACKEND_ROOT / "biometry_models" / "head_circumference" / "code"
sys.path.insert(0, str(HC_CODE_DIR))
sys.path.insert(0, str(BACKEND_ROOT))

from single_predict import single_predict  # noqa: E402

app = FastAPI(title="Auto Fetal Biometry API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.floating, np.integer)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    return value


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict/hc")
async def predict_hc(
    file: UploadFile = File(...),
    pixel_spacing_mm: float | None = None,
    clinical_ga_weeks: float | None = None,
) -> dict[str, Any]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload must be an image file.")

    suffix = Path(file.filename or "upload.png").suffix or ".png"
    tmp_path: str | None = None
    try:
        body = await file.read()
        if not body:
            raise HTTPException(status_code=400, detail="Empty file.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(body)
            tmp_path = tmp.name

        result = single_predict(
            tmp_path,
            pixel_spacing_mm=pixel_spacing_mm,
            clinical_ga_weeks=clinical_ga_weeks,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except OSError:
                pass

    if result is None:
        raise HTTPException(status_code=422, detail="Could not read or process image.")

    return _json_safe(result)


@app.post("/extract/form-f")
async def extract_form_f() -> dict[str, Any]:
    """
    Placeholder for OCR / intake extraction (Strike B).

    Returns empty ``fields`` so the frontend fills values from the scan session bridge;
    populate ``fields`` / ``citation`` here when a real extraction pipeline exists.
    """
    return {"fields": {}, "citation": None}
