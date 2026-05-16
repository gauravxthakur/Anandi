"""
HTTP API for fetal head circumference inference (Strike A) + optional Form F extract hook.

Run from repo root (Windows-friendly):

  py -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import base64
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BACKEND_ROOT = Path(__file__).resolve().parents[1]
HC_CODE_DIR = BACKEND_ROOT / "biometry_models" / "head_circumference" / "code"
sys.path.insert(0, str(HC_CODE_DIR))
sys.path.insert(0, str(BACKEND_ROOT))

from single_predict import single_predict  # noqa: E402
from reports.doc_report import generate_report  # noqa: E402

app = FastAPI(title="Auto Fetal Biometry API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models for Report Generation (Strike C)
# ============================================================================

class BiometryData(BaseModel):
    """Biometry measurement data from frontend prediction."""
    hc_mm: Optional[float] = None
    ga_weeks_from_hc: Optional[float] = None
    growth_verdict: Optional[str] = None
    hc_pixels: Optional[float] = None


class PatientData(BaseModel):
    """Patient intake form data from frontend."""
    fullName: str
    age: int
    husbandOrFatherName: str = ""
    contactNumber: str = ""
    postalAddress: str = ""
    
    livingChildrenTotal: int = 0
    livingSonsCount: int = 0
    livingSonsAges: str = ""
    livingDaughtersCount: int = 0
    livingDaughtersAges: str = ""
    lmpOrWeeks: str = ""
    
    referralSource: str = "self"
    referringDoctorNameAddress: str = ""
    
    indicationForUltrasound: list[str] = []
    resultOfProcedure: str = ""
    indicationForMtp: bool = False
    
    dateOfProcedure: str = ""
    patientConsentNoSexDisclosure: bool = False
    doctorConfirmationNoSexDisclosure: bool = False


class ReportGenerateRequest(BaseModel):
    """Request to generate a report PDF."""
    patient: PatientData
    biometry: Optional[BiometryData] = None


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


@app.post("/report/generate")
async def report_generate(request: ReportGenerateRequest) -> dict[str, Any]:
    """
    Generate a clinical report PDF from patient intake + biometry data.
    
    Returns a dict with 'pdf_base64' key containing the PDF file as base64
    (so it can be safely returned as JSON and downloaded on the frontend).
    """
    try:
        patient = request.patient
        biometry = request.biometry
        
        # Prepare biometry fields for doc_report
        image_name = ""
        head_circumference = ""
        center = ""
        semi_axes = ""
        angle = ""
        
        if biometry:
            if biometry.hc_mm:
                head_circumference = f"{biometry.hc_mm:.1f} mm"
            elif biometry.hc_pixels:
                head_circumference = f"{int(biometry.hc_pixels)} px"
        
        # Format indication and result
        indication_ultrasound = ", ".join(patient.indicationForUltrasound) or ""
        result_procedure = patient.resultOfProcedure or ""
        indication_mtp = "Yes" if patient.indicationForMtp else "No"
        
        # Format date
        date_procedure = patient.dateOfProcedure or ""
        
        # Format living children info
        living_sons_text = str(patient.livingSonsCount)
        if patient.livingSonsAges:
            living_sons_text += f" ({patient.livingSonsAges})"
        
        living_daughters_text = str(patient.livingDaughtersCount)
        if patient.livingDaughtersAges:
            living_daughters_text += f" ({patient.livingDaughtersAges})"
        
        # Generate PDF to a temp file
        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_pdf.close()
        
        try:
            generate_report(
                full_name=patient.fullName,
                age=str(patient.age),
                husband_father_name=patient.husbandOrFatherName,
                contact_number=patient.contactNumber,
                postal_address=patient.postalAddress,
                
                total_living_children=str(patient.livingChildrenTotal),
                living_sons=living_sons_text,
                living_daughters=living_daughters_text,
                lmp_or_weeks=patient.lmpOrWeeks,
                
                referral_source=patient.referralSource if patient.referralSource == "External Reference" else "Self-Referral",
                referring_doctor=patient.referringDoctorNameAddress,
                
                image_name=image_name,
                head_circumference=head_circumference,
                center=center,
                semi_axes=semi_axes,
                angle=angle,
                
                indication_ultrasound=indication_ultrasound,
                result_procedure=result_procedure,
                indication_mtp=indication_mtp,
                
                date_procedure=date_procedure,
                patient_consent=patient.patientConsentNoSexDisclosure,
                doctor_confirmation=patient.doctorConfirmationNoSexDisclosure,
                
                output_filename=tmp_pdf.name,
            )
            
            # Read the PDF file and return as base64
            with open(tmp_pdf.name, "rb") as f:
                pdf_data = f.read()
            
            pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")
            
            return {"pdf_base64": pdf_base64}
        finally:
            # Clean up temp file
            try:
                Path(tmp_pdf.name).unlink(missing_ok=True)
            except OSError:
                pass
    
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
