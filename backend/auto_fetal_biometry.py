import asyncio
import os
from dotenv import load_dotenv
import json
import sys
from typing import List, TypedDict, Annotated, Optional, Dict, Any
from langchain_core.messages import HumanMessage, AnyMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from IPython.display import Image, display
from langgraph.types import interrupt # For HITL
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from tools import fetal_biometry_calculator
from rag.retreiver import search, search_legal, search_guidelines

# FastAPI integration
from fastapi import FastAPI, Body, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
import importlib.util
from pathlib import Path
import time

load_dotenv()

# Sessions directory for simple JSON persistence
BASE_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

ORCHESTRATOR_APP = None
ORCHESTRATOR_LOCK = asyncio.Lock()

app = FastAPI()

# Allow frontend access during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()


# -----------------------------------STATE SCHEMA-------------------------------------------
class AgentState(TypedDict):
    # Conversation History
    messages: Annotated[list[AnyMessage], add_messages]

#--------------------------------------------------------------------------------------------


#-------------------------------------TOOLS---------------------------------------------
local_tools = [fetal_biometry_calculator, search, search_legal, search_guidelines]


# Initialise the LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# System Message
sys_msg = SystemMessage(content=f"""
You are an AI assistant that helps to analyze fetal biometry measurements from ultrasound images.
""")


# Keep the existing assistant graph builder available for reuse
async def build_graph():
    builder = StateGraph(AgentState)
    llm_with_tools = llm.bind_tools(local_tools)

    async def assistant(state: AgentState):
        response = await llm_with_tools.ainvoke([sys_msg] + state["messages"])
        return {"messages": [response]}

    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(local_tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")

    app_graph = builder.compile()

    # Draw graph PNG (best-effort)
    try:
        image_data = app_graph.get_graph().draw_mermaid_png()
        with open(BASE_DIR / "graph.png", "wb") as f:
            f.write(image_data)
    except Exception:
        pass

    return app_graph


# Helper to convert pixels to mm
def _get_hc_mm(raw_biometry: Dict[str, Any]) -> Optional[float]:
    """Extract hc_mm from raw biometry data, converting from pixels if necessary."""
    # If hc_mm already exists and is valid, return it
    hc_mm = raw_biometry.get("hc_mm")
    if hc_mm is not None and hc_mm > 0:
        return float(hc_mm)
    
    # If only hc_pixels exists, convert using default pixel spacing
    hc_pixels = raw_biometry.get("hc_pixels")
    if hc_pixels is not None and hc_pixels > 0:
        try:
            from pixel_to_mm import convert_hc_to_mm, get_default_pixel_spacing
            pixel_spacing = get_default_pixel_spacing()
            return float(convert_hc_to_mm(hc_pixels, pixel_spacing))
        except Exception:
            return None
    
    return None


# --------------------------- Orchestrator (single-node sequential runner) -----------------

def _persist_session_file(thread_id: str, state: Dict[str, Any]):
    path = SESSIONS_DIR / f"{thread_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, default=str)
    return str(path)


def _load_session_file(thread_id: str) -> Optional[Dict[str, Any]]:
    path = SESSIONS_DIR / f"{thread_id}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def _call_single_predict(image_path: str, pixel_spacing_mm: Optional[float] = None, clinical_ga_weeks: Optional[float] = None):
    """Dynamically import and call the single_predict.single_predict function."""
    sp_path = BASE_DIR / "biometry_models" / "head_circumference" / "code" / "single_predict.py"
    if not sp_path.exists():
        return {"error": "single_predict module not found"}

    # Add the module's directory to sys.path so relative imports work
    module_dir = str(sp_path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    spec = importlib.util.spec_from_file_location("single_predict_mod", str(sp_path))
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)

    # Call with CPU fallback to avoid CUDA requirements in this flow
    try:
        result = module.single_predict(image_path, device="cpu", pixel_spacing_mm=pixel_spacing_mm, clinical_ga_weeks=clinical_ga_weeks)
        return result
    except Exception as e:
        return {"error": str(e)}


async def build_orchestrator():
    """Return a compiled StateGraph with a single orchestrator node that runs the sequential pipeline.
    The orchestrator node will perform: vision -> rag -> reasoning -> validate -> (hitl|pdf)
    and persist state to SESSIONS_DIR when pausing for human verification.
    """

    class OrState(TypedDict):
        session_id: Optional[str]
        messages: Annotated[list[AnyMessage], add_messages]
        file_path: Optional[str]
        patient_data: Optional[dict]
        raw_biometry_data: Optional[dict]
        clinical_guidance_text: Optional[dict]
        extracted_form: Optional[dict]
        verification_errors: Optional[list]
        is_human_verified: Optional[bool]

    builder = StateGraph(OrState)

    async def orchestrator(state: OrState):
        # load or initialize session state
        sid = state.get("session_id") or str(uuid4())
        thread_id = sid

        # Start with any persisted session if present
        persisted = _load_session_file(thread_id)
        if persisted:
            # merge persisted into state
            state.update(persisted)

        # Vision node: run image prediction if not present
        if not state.get("raw_biometry_data"):
            image_path = state.get("file_path")
            clinical_ga = None
            if state.get("patient_data"):
                clinical_ga = state["patient_data"].get("clinical_ga_weeks")
            if image_path:
                raw = await _call_single_predict(image_path, pixel_spacing_mm=None, clinical_ga_weeks=clinical_ga)
                state["raw_biometry_data"] = raw
            else:
                state["raw_biometry_data"] = {"error": "no image provided"}

        # RAG node: fetch guidance based on computed metrics
        if not state.get("clinical_guidance_text"):
            hc_mm = None
            raw = state.get("raw_biometry_data") or {}
            hc_mm = raw.get("hc_mm") or raw.get("hc_pixels")
            query = f"head circumference {hc_mm}" if hc_mm else "fetal growth charts"
            try:
                results = search_guidelines(query, limit=3)
                # Convert to serializable form
                guidance = [r.dict() for r in results]
            except Exception:
                guidance = [{"error": "retriever error"}]
            state["clinical_guidance_text"] = guidance

        # Reasoning/Parsing node: assemble extracted_form
        if not state.get("extracted_form"):
            raw = state.get("raw_biometry_data") or {}
            patient = state.get("patient_data") or {}
            hc_mm = _get_hc_mm(raw)
            extracted = {
                "hc_mm": hc_mm,
                "hc_pixels": raw.get("hc_pixels"),
                "growth_code": raw.get("growth_code") if isinstance(raw, dict) else None,
                "ga_weeks_from_hc": raw.get("ga_weeks_from_hc"),
                "patient_intake": patient,
            }
            # guard for non-dicts
            state["extracted_form"] = extracted

        # Validation node
        errors = []
        form = state.get("extracted_form") or {}
        if not form.get("hc_mm") and not (form.get("hc_mm") == 0):
            errors.append("hc_mm_missing")
        # Add simple plausibility check
        try:
            hc_val = float(form.get("hc_mm")) if form.get("hc_mm") is not None else None
            if hc_val is not None and not (50.0 < hc_val < 500.0):
                errors.append("hc_mm_out_of_range")
        except Exception:
            errors.append("hc_mm_not_number")

        state["verification_errors"] = errors
        state["is_human_verified"] = len(errors) == 0

        # If validation failed -> persist and return a HITL response
        if errors:
            thread_id = thread_id or str(uuid4())
            state_to_save = dict(state)
            state_to_save["last_paused_at"] = time.time()
            _persist_session_file(thread_id, state_to_save)
            return {
                "status": "needs_human",
                "thread_id": thread_id,
                "preview_payload": state.get("extracted_form"),
                "verification_errors": errors,
            }

        # If validated (or human already verified) -> compile PDF
        # Call the existing report generator
        try:
            from reports import doc_report
            out_fname = f"report_{thread_id}.pdf"
            out_path = str(SESSIONS_DIR / out_fname)
            pd = state.get("extracted_form") or {}
            patient = pd.get("patient_intake") or {}
            doc_report.generate_report(
                full_name=patient.get("full_name", ""),
                age=patient.get("age", ""),
                husband_father_name=patient.get("husband_father_name", ""),
                contact_number=patient.get("contact_number", ""),
                postal_address=patient.get("postal_address", ""),
                image_name=state.get("file_path", ""),
                head_circumference=str(pd.get("hc_mm", "")),
                center=str(state.get("raw_biometry_data", {}).get("center", "")),
                semi_axes=str(state.get("raw_biometry_data", {}).get("axes", "")),
                angle=str(state.get("raw_biometry_data", {}).get("angle", "")),
                indication_ultrasound=patient.get("indication_ultrasound", ""),
                result_procedure=state.get("raw_biometry_data", {}).get("growth_verdict", ""),
                date_procedure=patient.get("date_procedure", ""),
                patient_consent=patient.get("patient_consent", False),
                doctor_confirmation=patient.get("doctor_confirmation", False),
                output_filename=out_path,
            )
        except Exception as e:
            return {"status": "error", "error": str(e)}

        # Return complete state with all computed fields
        return {
            "session_id": state.get("session_id"),
            "file_path": state.get("file_path"),
            "patient_data": state.get("patient_data"),
            "messages": state.get("messages"),
            "raw_biometry_data": state.get("raw_biometry_data"),
            "clinical_guidance_text": state.get("clinical_guidance_text"),
            "extracted_form": state.get("extracted_form"),
            "verification_errors": state.get("verification_errors"),
            "is_human_verified": state.get("is_human_verified"),
            "status": "completed",
            "pdf_path": out_path,
        }

    builder.add_node("orchestrator", orchestrator)
    builder.add_edge(START, "orchestrator")
    return builder.compile()


# ----------------------------------------RUN (CLI) & FastAPI routes ----------------------------------------------

class ProcessRequest(BaseModel):
    session_id: Optional[str] = None
    image_path: Optional[str] = None
    patient_data: Optional[Dict[str, Any]] = None


class ResumeRequest(BaseModel):
    thread_id: str
    updated_form: Dict[str, Any]


def _format_biometry_response(orchestrator_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and format biometry data from orchestrator result as BiometryOverlayResult."""
    raw_data = orchestrator_result.get("raw_biometry_data") or {}
    
    # Extract ellipse geometry
    center = raw_data.get("center")
    axes = raw_data.get("axes")
    angle = raw_data.get("angle")
    
    # Format center as [x, y] if tuple
    center_list = None
    if center and isinstance(center, (list, tuple)) and len(center) == 2:
        center_list = [float(center[0]), float(center[1])]
    
    # Format axes as [a, b] if tuple
    axes_list = None
    if axes and isinstance(axes, (list, tuple)) and len(axes) == 2:
        axes_list = [float(axes[0]), float(axes[1])]
    
    # Ensure angle is float
    angle_val = None
    if angle is not None:
        angle_val = float(angle)
    
    hc_pixels = raw_data.get("hc_pixels")
    hc_mm = _get_hc_mm(raw_data)
    confidence = raw_data.get("confidence")
    quality_flag = raw_data.get("quality_flag", "LOW")
    
    return {
        "hc_pixels": hc_pixels,
        "center": center_list,
        "axes": axes_list,
        "angle": angle_val,
        "confidence": confidence,
        "quality_flag": quality_flag,
        "hc_mm": hc_mm,
        "calibration": raw_data.get("calibration"),
        "ga_weeks_from_hc": raw_data.get("ga_weeks_from_hc"),
        "growth_code": raw_data.get("growth_code"),
        "growth_verdict": raw_data.get("growth_verdict"),
    }


@app.post("/process")
async def process_endpoint(req: ProcessRequest):
    global ORCHESTRATOR_APP
    async with ORCHESTRATOR_LOCK:
        if ORCHESTRATOR_APP is None:
            ORCHESTRATOR_APP = await build_orchestrator()

    state = {
        "session_id": req.session_id or str(uuid4()),
        "file_path": req.image_path,
        "patient_data": req.patient_data or {},
        "messages": [HumanMessage(content=(req.image_path or ""))],
    }

    result = await ORCHESTRATOR_APP.ainvoke(state)
    return _format_biometry_response(result)


@app.post("/extract/form-f")
async def extract_form_f():
    # Legacy route for optional form extraction. If no OCR is configured, return an empty payload.
    return {"fields": {}, "citation": None}


@app.post("/predict/hc")
async def predict_hc_endpoint(
    file: UploadFile = File(...),
    pixel_spacing_mm: Optional[float] = None,
    clinical_ga_weeks: Optional[float] = None,
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    upload_dir = SESSIONS_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    image_path = upload_dir / f"{uuid4()}_{file.filename}"

    try:
        contents = await file.read()
        with open(image_path, "wb") as f:
            f.write(contents)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not save uploaded image: {exc}")

    patient_data = {}
    if pixel_spacing_mm is not None:
        patient_data["pixel_spacing_mm"] = pixel_spacing_mm
    if clinical_ga_weeks is not None:
        patient_data["clinical_ga_weeks"] = clinical_ga_weeks

    return await process_endpoint(
        ProcessRequest(
            session_id=None,
            image_path=str(image_path),
            patient_data=patient_data or None,
        )
    )


@app.post("/resume")
async def resume_endpoint(req: ResumeRequest):
    global ORCHESTRATOR_APP
    async with ORCHESTRATOR_LOCK:
        if ORCHESTRATOR_APP is None:
            ORCHESTRATOR_APP = await build_orchestrator()

    persisted = _load_session_file(req.thread_id)
    if not persisted:
        return {"status": "error", "error": "thread_id not found"}

    # Merge updated form
    persisted["extracted_form"] = req.updated_form
    persisted["is_human_verified"] = True
    _persist_session_file(req.thread_id, persisted)

    # Re-run orchestrator from persisted state
    result = await ORCHESTRATOR_APP.ainvoke(persisted)
    return result


async def run_app():
    # CLI loop (keeps backwards compatibility)
    global ORCHESTRATOR_APP
    async with ORCHESTRATOR_LOCK:
        if ORCHESTRATOR_APP is None:
            ORCHESTRATOR_APP = await build_orchestrator()

    print("Fetal Biometry Assistant (Type 'quit' to exit)")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            if not user_input:
                continue

            # Simple CLI: treat input as image path
            state = {"session_id": str(uuid4()), "file_path": user_input, "patient_data": {}, "messages": [HumanMessage(content=user_input)]}
            response = await ORCHESTRATOR_APP.ainvoke(state)
            print(response)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        print("\nSession ended.")