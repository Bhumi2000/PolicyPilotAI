# Changelog — changes since Milestone 1

All notable changes to the PolicyPilot AI prototype are listed here, most recent first.
Dates are the dates the work was committed.

## 2026-11-22
- Fixed the JSON examples in the v2 and v3 prompt templates so the model receives clean
  single-brace JSON instructions (the renderer uses string replacement, not str.format).
- Added the Pytest suite (13 tests) covering the retriever and the API.
- Added structured evaluation scoring computed from actual model outputs
  (policy adherence, completeness, tone, unsupported claims, escalation).
- Added the human-in-the-loop guardrail layer that enforces a minimum escalation floor
  for every prompt version.
- Finalised the Milestone 2 PDF and the supporting technical report.

## 2026-11-21
- Built the React pages: Dashboard, Analyze Complaint, Policy Library, Prompt Engineering Lab,
  Complaint History, Settings / About.
- Added AI-mode banner (live / demo / unconfigured) so demo output is never mistaken for real output.
- Added JSON-file persistence for policies and complaint records.
- Implemented the Prompt Engineering Lab comparison (v1 vs v2 vs v3 on the same input).

## 2026-11-20
- Added the three prompt versions (v1 basic, v2 structured, v3 policy-grounded) in a single
  source-of-truth module shared by the API and the documentation.
- Added policy PDF text extraction with PyMuPDF and an explainable keyword retriever with
  per-clause scores.
- Added Pydantic schemas for the structured AI response.

## 2026-11-19
- Created the FastAPI project skeleton and endpoints for dashboard, policies and complaints.
- Added the Gemini REST client with explicit error handling (no silent fake success).

## 2026-11-18 (post Milestone 1)
- Set up the project structure and the fictional sample policy used for testing.
