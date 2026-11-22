# PolicyPilot AI — Project Documentation

## 1. Problem

Customer-support teams receive large volumes of complaints and must check company policy before
replying. This is slow and leads to inconsistent answers and unsupported promises (for example
promising a refund the policy does not allow). PolicyPilot AI makes the process faster, more
consistent and policy-compliant.

## 2. Architecture

```
React frontend (Vite, Tailwind)
        │  /api/*  (JSON)
        ▼
FastAPI backend
        ├── Policy processing  (PyMuPDF extraction, clause splitting)
        ├── Retrieval          (explainable keyword scoring)
        ├── Prompt engineering (v1 basic, v2 structured, v3 policy-grounded)
        ├── Gemini API         (gemini-2.5-flash, JSON output)
        ├── Validation         (Pydantic schemas)
        └── Human review       (deterministic escalation guardrails)
        ▼
Stored records → Dashboard, History, Prompt Lab
```

## 3. Prompt design

| Version | Idea | Output |
| --- | --- | --- |
| v1 | Basic instruction-based prompt | free-text reply |
| v2 | Role + context + task + constraints + fixed JSON schema | 9-key JSON |
| v3 | Grounded in retrieved clauses, missing-info detection, no unsupported promises, escalation | 12-key JSON |

The prompt text lives in `backend/app/prompts/versions.py`, so the running app, the Prompt
Engineering Lab and the documented prompt sheets can never drift apart.

## 4. Retrieval

`backend/app/services/retrieval.py` splits a policy into clauses and ranks them against the
complaint using stop-word-filtered token overlap, term frequency and bigram matches. Every
clause keeps the score that produced it, so the retrieval is fully explainable. No embeddings
or black-box models are used.

## 5. Evaluation

`backend/app/services/evaluator.py` scores each real output on five criteria (0–5 each):
policy adherence, completeness, tone and empathy, unsupported claims, and escalation
appropriateness. Scores are computed from the output of the current run, never hard-coded.

## 6. Human-in-the-loop

The model is asked to escalate in v3, and the application additionally enforces a deterministic
floor: any run with no retrieved clause, a high-risk classification, an exception request, or
many missing fields is marked `human_review_required`.

## 7. Data and privacy

- The Gemini API key is only in the backend environment (`backend/.env`, git-ignored).
- All sample policies and customers are fictional.
- The prototype drafts replies only; it performs no external actions.

## 8. Testing

`backend/tests/` contains 13 Pytest tests: retriever unit tests and API tests
(health, policy creation, analysis, comparison, history/dashboard consistency, upload validation).
