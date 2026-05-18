# Anandi: AI-Driven Decision Support for PC-PNDT Ultrasound Workflows

A Gemma 4-powered clinical assistant that automates fetal head biometry, verifies Form F compliance, and delivers explainable diagnostics for Indian obstetric sonologists.

<img width="1566" height="704" alt="gatha_example1" src="https://github.com/user-attachments/assets/8fe60fe3-8aeb-49a5-b67c-e7e4c08eaa7d" />

## Track

Health & Sciences

## Executive Summary

Anandi is a physician-facing decision support system built to reduce clerical risk and improve clinical confidence in Indian obstetric ultrasound workflows governed by the PC-PNDT Act. It combines automated fetal head circumference measurement with expert-guided clinical documentation and legally grounded reasoning. A fine-tuned Gemma 4 E4B model powers the RAG-enabled decision engine, which explains cautions, generates compliance-aware insights, and helps the sonologist complete Form F with minimal error.

This submission is rooted in an urgent real-world challenge: India’s PC-PNDT Act protects the child sex ratio but also creates disproportionate risk for sonologists when small paperwork mistakes trigger machine seals and practice shutdowns. Anandi solves this problem by bringing native on-device intelligence, function calling, and multimodal verification into the ultrasound workflow.

## Problem Statement

India’s PCPNDT law is essential for preventing sex-selective abortions, but it places enormous legal pressure on sonologists. Clinics are frequently audited, and even innocent transcription errors or mismatched clinical notes can lead to machine sealing and long investigations.

A representative case from 2018 illustrates this problem: Dr. Twinkle, a qualified gynecologist registered in Maharashtra and Gujarat, had her sonography machine sealed over minor clerical registry errors despite no evidence of illegal sex determination. The consequences lasted six years.

This is not isolated. In 2016, more than 700 radiologists in Hyderabad protested the law after clerical errors caused mass service shutdowns affecting over 2,000 patients. The gap is not between medicine and intent; it is between documentation, clinical support, and legally compliant reporting.

## Solution Overview

Anandi addresses this gap by delivering a tightly integrated ultrasound workflow with three core capabilities:

1. Automated fetal head circumference (HC) measurement from ultrasound images using a DETR-based computer vision pipeline.
2. A Form F workflow that enforces verification, clinical field validation, and legal safeguards before saving.
3. A Gemma 4 E4B powered RAG decision engine that explains caution flags and generates clinically compliant diagnostic insights.

The system is designed for sonologists, not patients. It generates a doctor-facing smart report with sensitive compliance details, while intentionally excluding patient-facing sex-determination content.

## Technical Architecture

### Frontend

The application is organized as a Next.js frontend inside `frontend/`. It provides a clean, doctor-oriented experience with the following flow:

- **Scan Upload**: The sonologist uploads an ultrasound image of the fetal head.
- **Biometry Overlay**: A DETR-inspired computer vision model computes the fetal head ellipse and head circumference, rendering interactive overlay metrics on the scan.
- **Clinical GA Input**: The sonologist enters the patient’s clinical gestational age from the last menstrual period.
- **Form F Navigation**: After image submission, the app routes to a dedicated Form F page where patient identity, obstetric history, referral details, AI insights, and digital sign-off sections are completed.
- **Verification Lock**: The form can only be saved after every field has been reviewed, verified, and approved by the sonologist.

### Backend

The backend lives under `backend/` and exposes APIs for inference, report generation, and RAG reasoning. Core backend modules include:

- `biometry_models/` and `single_predict.py` for image segmentation, ellipse inference, and HC calculation.
- `tools.py` and `hadlock_lookup.py` for gestational age estimation, quality scoring, and clinical growth classification.
- `llm/` and `rag/` for retrieval-augmented generation, prompt orchestration, and LLM verdict creation.
- `reports/doc_report.py` for doctor-facing PDF report generation.

### Gemma 4 Integration

Anandi is built around a fine-tuned Gemma 4 E4B model. The model is specialized on:

- PCPNDT guidelines
- ISUOG ultrasound reporting standards
- A synthetic dataset of ultrasound scans mapped to legally and clinically compliant diagnostic reports

That fine-tuned Gemma 4 instance is used for:

- **Decision Support**: When clinical GA differs from AI-estimated GA, the system raises a caution and uses the model to generate an explainable rationale with citations.
- **Report Insights**: The AI produces procedure-level decisions and physician-facing interpretation notes for the smart report.
- **Compliance Guidance**: Gemma 4 is conditioned to avoid patient-facing sex determination and instead focus on legally relevant clinical reasoning.

### RAG and Retrieval

The decision engine is not a standalone chat model. It is a retrieval-augmented generation pipeline that combines Gemma 4 with domain knowledge from indexed medical guidelines and legal documents. Key features include:

- Document ingestion of PC-PNDT and ISUOG material, converted to markdown and embedded to support semantic search.
- Function calling through LangGraph-style orchestrator tools to compute gestational age, validate metrics, and return structured outputs.
- Guardrails that prompt the model to cite sources and explain why a caution was raised.

### Clinical Safeguards

Anandi was built with several deterministic safety and quality mechanisms:

- **Image Quality Assessment**: Laplacian variance blur detection and segmentation confidence flags identify poor-quality scans.
- **Ellipse Quality Metrics**: The system computes confidence scores for the segmentation and ellipse output before trusting HC measurements.
- **Clinical Confidence Scoring**: The app evaluates multiple factors, including model fit, clinical GA mismatch, and segmentation reliability.
- **Strict Save Policy**: Form F cannot be saved until every section is verified, reducing clerical oversight risk.

## Why Gemma 4?

Gemma 4 is the foundation of Anandi’s intelligence because it supports:

- **Multimodal reasoning** for combining ultrasound-derived metrics with textual clinical context.
- **Native function calling** for grounded outputs and structured clinical decisions.
- **Fine-tuning and domain adaptation** so the model can be calibrated to PC-PNDT legal norms and sonography best practices.

The project uses a locally optimized frontier model to keep sensitive medical reasoning close to the workflow and to reduce dependency on remote inference.

## Real-World Impact

Anandi is designed for the realities of healthcare delivery in India:

- Reduces the legal risk of PC-PNDT audits by enforcing accurate, verifiable Form F documentation.
- Helps sonologists avoid machine seizures caused by clerical error and undocumented GA mismatches.
- Improves trust in ultrasound workflows by providing explainable, source-cited clinical reasoning.
- Preserves privacy and regulatory intent by keeping the app doctor-facing and by avoiding any patient-directed sex-determination output.

This solution is not just a convenience feature; it is a legal risk mitigation tool that can preserve clinical capacity in underserved communities where every ultrasound appointment counts.

## Architecture Diagram (conceptual)

1. **Ultrasound Scan Upload** → `frontend/scan/page.tsx`
2. **CV Inference** → `backend/single_predict.py` + DETR biometry model
3. **GA Comparison & Quality Scoring** → `backend/hadlock_lookup.py`, `backend/tools.py`
4. **RAG Retrieval** → `backend/rag/retreiver.py`
5. **Gemma 4 E4B Decision Engine** → `backend/llm/client.py`, `backend/llm/config.py`
6. **Form F Verification** → `frontend/forms/PatientIntakeForm.tsx` and `frontend/forms/ReportPreviewModal.tsx`
7. **PDF Report Generation** → `backend/reports/doc_report.py`

## Engineering Challenges and Solutions

### Challenge: Aligning AI GA estimates with legally reported clinical GA

- **Solution:** Implemented Hadlock-based GA estimation and clinical growth classification to compare AI measurement-derived gestational age with the patient’s reported LMP-based GA.
- **Result:** The system can raise targeted cautions with citation-backed reasoning when the two measures diverge.

### Challenge: Preventing unsafe model output in a sensitive regulatory workflow

- **Solution:** Built a decision support engine on a fine-tuned Gemma 4 E4B model with explicit prompts focused on compliance, report generation, and medical reasoning.
- **Result:** The model strictly avoids sex determination language and instead produces clinically relevant insights for the sonologist.

### Challenge: Minimizing false confidence from low-quality ultrasound scans

- **Solution:** Added deterministic image quality metrics, segmentation confidence, and ellipse quality flags.
- **Result:** The app only surface results when both CV outputs and clinical conditions satisfy quality thresholds.

### Challenge: Enforcing strict clinician review before form completion

- **Solution:** Designed the UI to require review and verification before saving the Form F entry.
- **Result:** This reduces the risk of clerical mistakes and ensures the final output is signed off by a qualified sonologist.

## Future Work

Potential enhancements for Anandi include:

- Move away from the Next.js web frontend, which was built purely for the judges' ease of testing, and package the stack into a standalone, physical Edge AI device (like using an NVIDIA Jetson) that plugs directly into lany ultrasound machine (ultrasound  machine-agnostism), along with the flagship feature of Real-Time Probe Guidance.
- Extending biometry support beyond fetal head circumference to AC, FL, and BPD.
- Enabling audit trail logging for regulatory inspection and machine seal defense.


## Why This Project Matters

Anandi is built at the intersection of AI, clinical workflow, and legal compliance. It is not merely an ultrasound assistant; it is an intelligent safety net for a system where paperwork and documentation can carry career-ending consequences.

By combining computer vision, fine-tuned Gemma 4 models, and retrieval-augmented clinical reasoning, this submission demonstrates a meaningful use of frontier models to protect clinicians, preserve services, and support maternal healthcare in contexts where trust and accuracy matter most.

## Conclusion

Anandi is a practical, high-impact application of Gemma 4 models in health and compliance. It leverages the model’s reasoning and function calling capabilities to create a transparent, clinically validated ultrasound documentation workflow for Indian practice.

This project is built for real-world change, and it demonstrates how local, specialized AI can reduce unnecessary regulatory harm while keeping patient safety and legal compliance at the center of care.