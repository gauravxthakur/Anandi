"""
Generate a short LLM-based explanation of fetal growth classification.

Step 4: Gemini line — builds structured prompt with growth_code, deltas,
and clinical/HC-implied GA; calls ChatGoogleGenerativeAI with guardrails
to ensure the verdict matches the growth_code. Falls back to static templates
on disagreement or API failure.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Growth code categories for prompt construction and validation
GROWTH_NORMAL = "NORMAL"
GROWTH_SMALL_FOR_GA = "SMALL_FOR_GA"
GROWTH_LARGE_FOR_GA = "LARGE_FOR_GA"
GROWTH_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

# Static verdict templates (hackathon cheat) — used if Gemini unavailable or disagrees
VERDICT_TEMPLATES = {
    GROWTH_NORMAL: (
        "Head circumference is consistent with expected size for reported gestational age. "
        "No growth concerns detected."
    ),
    GROWTH_SMALL_FOR_GA: (
        "Head circumference appears smaller than expected for reported gestational age. "
        "Close monitoring is recommended; clinical correlation advised."
    ),
    GROWTH_LARGE_FOR_GA: (
        "Head circumference appears larger than expected for reported gestational age. "
        "Further assessment and clinical correlation are recommended."
    ),
    GROWTH_INSUFFICIENT_DATA: (
        "Unable to classify growth due to missing or out-of-range measurements. "
        "Please provide clinical gestational age and ensure HC measurement is valid."
    ),
}


def _build_gemini_prompt(
    growth_code: str,
    *,
    clinical_ga_weeks: Optional[float] = None,
    hc_ga_weeks: Optional[float] = None,
    hc_ga_minus_clinical_weeks: Optional[float] = None,
    normal_band_weeks: float = 2.0,
) -> str:
    """
    Build a structured prompt for Gemini.

    Input: growth_code, numeric deltas, clinical/HC GA (all in JSON for clarity).
    Instruction: Do not change the category; only explain it.
    """
    context = {
        "growth_code": growth_code,
        "clinical_ga_weeks": clinical_ga_weeks,
        "hc_ga_weeks": hc_ga_weeks,
        "hc_ga_minus_clinical_weeks": hc_ga_minus_clinical_weeks,
        "normal_band_weeks": normal_band_weeks,
    }
    context_json = json.dumps(context, indent=2)

    prompt = f"""\
You are a medical AI assistant providing brief explanations of fetal biometry measurements. \
Your task is to explain the growth classification without changing it or introducing new facts.

Growth Classification Context:
{context_json}

Classification Rules:
- NORMAL: HC-implied GA is within ±{normal_band_weeks} weeks of clinical GA.
- SMALL_FOR_GA: HC-implied GA is more than {normal_band_weeks} weeks younger than clinical GA.
- LARGE_FOR_GA: HC-implied GA is more than {normal_band_weeks} weeks older than clinical GA.
- INSUFFICIENT_DATA: Cannot classify (missing HC, missing clinical GA, or HC out of Hadlock range).

Your task:
1. Do NOT change the growth_code "{growth_code}" — it is already determined by the rules above.
2. Write ONE short sentence or brief paragraph (2–3 sentences max) explaining why this \
classification applies.
3. Use clinically appropriate but accessible language.
4. Do NOT invent new measurements or facts beyond what is provided above.

Respond with ONLY the explanation text, no preamble."""

    return prompt


def _extract_verdict_from_response(response_text: str) -> Optional[str]:
    """
    Extract and validate the verdict text from Gemini response.

    Returns the text if valid (non-empty, reasonable length); else None.
    """
    if not response_text:
        return None
    verdict = response_text.strip()
    # Sanity checks: not too short, not too long
    if len(verdict) < 20 or len(verdict) > 500:
        logger.warning(f"Verdict text out of bounds (len={len(verdict)}): {verdict[:50]}")
        return None
    return verdict


def _validate_verdict_matches_code(
    verdict_text: str,
    growth_code: str,
) -> bool:
    """
    Guardrail: check if the verdict text mentions keywords consistent with growth_code.

    Extremely loose check — if Gemini mentions contradictory keywords,
    reject the verdict and fall back to template.
    """
    verdict_lower = verdict_text.lower()

    # Keywords that would contradict each code
    if growth_code == GROWTH_NORMAL:
        bad_keywords = ["small", "large", "concern", "abnormal", "deficit"]
        if any(kw in verdict_lower for kw in bad_keywords):
            logger.warning(
                f"Verdict contradicts NORMAL: {verdict_text[:60]}"
            )
            return False
    elif growth_code == GROWTH_SMALL_FOR_GA:
        bad_keywords = ["large", "big", "excessive"]
        if any(kw in verdict_lower for kw in bad_keywords):
            logger.warning(
                f"Verdict contradicts SMALL_FOR_GA: {verdict_text[:60]}"
            )
            return False
    elif growth_code == GROWTH_LARGE_FOR_GA:
        bad_keywords = ["small", "deficit", "reduced"]
        if any(kw in verdict_lower for kw in bad_keywords):
            logger.warning(
                f"Verdict contradicts LARGE_FOR_GA: {verdict_text[:60]}"
            )
            return False

    return True


def generate_gemini_verdict(
    growth_code: str,
    *,
    clinical_ga_weeks: Optional[float] = None,
    hc_ga_weeks: Optional[float] = None,
    hc_ga_minus_clinical_weeks: Optional[float] = None,
    normal_band_weeks: float = 2.0,
    use_template_only: bool = False,
) -> Optional[str]:
    """
    Generate a short LLM-based explanation of the growth classification.

    Steps:
    1. Build structured prompt from growth_code and numeric context.
    2. Call ChatGoogleGenerativeAI (if API key available and use_template_only=False).
    3. Validate response against growth_code keywords.
    4. Fall back to static template on API error, timeout, or guardrail failure.

    Args:
        growth_code: One of NORMAL, SMALL_FOR_GA, LARGE_FOR_GA, INSUFFICIENT_DATA.
        clinical_ga_weeks: Clinical gestational age (weeks).
        hc_ga_weeks: HC-implied gestational age (weeks).
        hc_ga_minus_clinical_weeks: Delta between HC GA and clinical GA.
        normal_band_weeks: Threshold for "normal band" (default 2.0).
        use_template_only: If True, skip Gemini and use static template (for testing).

    Returns:
        One-line verdict string (non-diagnostic) or None if template unavailable.
    """
    # Get static template as fallback
    template = VERDICT_TEMPLATES.get(growth_code)
    if template is None:
        logger.warning(f"No template for growth_code {growth_code}")
        return None

    # Hackathon cheat: if use_template_only, return template immediately
    if use_template_only:
        logger.info(f"Using template-only mode for {growth_code}")
        return template

    # Try Gemini if API key is available
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.info("GOOGLE_API_KEY not set; using template for verdict")
        return template

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

        prompt_text = _build_gemini_prompt(
            growth_code,
            clinical_ga_weeks=clinical_ga_weeks,
            hc_ga_weeks=hc_ga_weeks,
            hc_ga_minus_clinical_weeks=hc_ga_minus_clinical_weeks,
            normal_band_weeks=normal_band_weeks,
        )

        message = HumanMessage(content=prompt_text)
        response = llm.invoke([message])
        response_text = response.content if hasattr(response, "content") else str(response)

        # Validate and extract
        verdict = _extract_verdict_from_response(response_text)
        if verdict is None:
            logger.warning("Verdict extraction failed; using template")
            return template

        # Guardrail: check consistency with growth_code
        if not _validate_verdict_matches_code(verdict, growth_code):
            logger.warning("Verdict guardrail failed; using template")
            return template

        logger.info(f"Gemini verdict succeeded for {growth_code}")
        return verdict

    except Exception as e:
        logger.warning(f"Gemini API call failed ({type(e).__name__}: {e}); using template")
        return template
