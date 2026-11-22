# PolicyPilot AI — Intelligent, Policy-Grounded Customer Support & Resolution Assistant

PolicyPilot AI helps customer-support teams analyse complaints, ground their answers in
company policy, and draft accurate, empathetic replies **without inventing promises**.
It combines a transparent keyword policy retriever, three progressively stronger prompts,
structured validation, and a human-in-the-loop review step.

> ⚠️ All sample policies and customer details in this repository are **fictional** and used
> for demonstration only.

## Team members

| Role | Name | Enrollment no. |
| --- | --- | --- |
| Team leader | `Bhumika Sharma` | `S24CSEU2310` |
| Member | `Mahak` | `S24CSEU2325` |

- **Team ID:** `36`
- **Batch:** `87`
- **Faculty:** `Indrajeet Gupta`
- **Prototype link:** `<PROTOTYPE_LINK>`
- **Reel link:** `<REEL_LINK>`



## What it does

- **Complaint analysis** — summary, category, customer intent, sentiment, urgency, risk level.
- **Policy library** — upload policy PDFs (text extracted with PyMuPDF) or paste policy text.
- **Explainable retrieval** — relevant clauses retrieved by keyword overlap, each with a score.
- **Response generation** — one reply per tone, grounded in the retrieved clauses.
- **Guardrails** — refuses to promise refunds, replacements, compensation or delivery dates
  that the policy does not support.
- **Human-in-the-loop** — flags unclear, high-risk, exception or low-confidence cases.
- **Prompt Engineering Lab** — compares three prompt versions on the same input.
- **Complaint history** — every run stored with its inputs, evidence and evaluation.

## Technology stack

| Layer | Tools |
| --- | --- |
| Frontend | React 18, Vite, Tailwind CSS, React Router, Axios, Recharts |
| Backend | Python, FastAPI, Pydantic, Uvicorn |
| AI | Google Gemini (`gemini-2.5-flash`) via the Gemini REST API |
| Documents | PyMuPDF (PDF text extraction) |
| Testing | Pytest |

The Gemini API key is stored **only** in the backend environment and is never exposed to the
browser.

## How to run locally

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env      # then edit .env and add GEMINI_API_KEY
uvicorn app.main:app --reload
```

The API is served at `http://127.0.0.1:8000` (interactive docs at `/docs`).

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Demo / offline mode

If no `GEMINI_API_KEY` is set, set `ENABLE_DEMO_MODE=true` in `backend/.env`. The app will then
return **clearly-labelled deterministic demo output** (`mode: "demo"`, shown with an amber
banner) so the interface can be explored offline. It is never presented as a real model answer,
and no fake success is returned when the AI is unconfigured.

## Project structure

```
PolicyPilot-AI/
├── frontend/            React + Vite + Tailwind UI
│   └── src/
│       ├── components/  Layout, reusable UI, AnalysisView
│       ├── pages/       Dashboard, Analyze, Policy Library, Prompt Lab, History, Settings
│       ├── services/    Axios API client
│       └── context/     Backend health / AI-mode provider
├── backend/             FastAPI service
│   ├── app/
│   │   ├── routes/      dashboard, policies, complaints, prompts
│   │   ├── services/    gemini_client, pdf_service, retrieval, analysis, evaluator
│   │   ├── prompts/     prompt version definitions (v1, v2, v3)
│   │   ├── schemas/     Pydantic models
│   │   └── store.py     JSON-file persistence
│   └── tests/           Pytest suite
├── sample_data/         Fictional policy + 12 test cases
└── docs/                Diagrams, documentation, Milestone 2 PDF
```

## Running the tests

```bash
cd backend
python -m pytest -q
```

## API overview

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | AI mode and model |
| GET | `/api/dashboard/stats` | Aggregated statistics from real records |
| POST | `/api/policies/upload` | Upload a policy PDF |
| POST | `/api/policies/text` | Save pasted policy text |
| GET | `/api/policies` | List policies |
| POST | `/api/complaints/analyze` | Analyse one complaint |
| POST | `/api/complaints/compare` | Run v1, v2, v3 on one complaint |
| GET | `/api/complaints` | Complaint history |
| PATCH | `/api/complaints/{id}/review` | Approve or edit a reply |

## Limitations

- Retrieval is keyword-based (no embeddings yet), so unusual paraphrases may score low.
- The prototype drafts replies only; it never sends emails or issues refunds.
- Stored data is a local JSON file, suitable for a demo but not production.
