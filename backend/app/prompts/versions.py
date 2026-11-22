"""Prompt engineering assets: three prompt versions and their metadata.

The prompt text below is the single source of truth. The same strings are
rendered into the Milestone 2 PDF (Section 2 prompt sheets) and shown live in
the "Prompt Engineering Lab" page, so the PDF and the app can never drift apart.
"""
from __future__ import annotations

from typing import Dict

from ..schemas.models import PromptVersionInfo

# --------------------------------------------------------------------------- #
# Version 1 - Basic prompt (plain-text reply, no structure)
# --------------------------------------------------------------------------- #
V1_SYSTEM_PROMPT = ""

V1_USER_PROMPT = """You are a customer support assistant. Read the customer complaint and the company policy below, then write a short reply to the customer.

Customer complaint:
{complaint}

Company policy:
{policy_text}"""

# --------------------------------------------------------------------------- #
# Version 2 - Structured prompt (role, context, task, constraints, output format)
# --------------------------------------------------------------------------- #
V2_SYSTEM_PROMPT = """You are a senior customer support analyst for an e-commerce company.
You always answer in valid JSON and never invent company policy."""

V2_USER_PROMPT = """ROLE: Senior customer support analyst.
CONTEXT: A customer has raised a complaint. You are given the complaint and the full company policy text.
TASK: Analyse the complaint and propose a resolution, then write a reply.
CONSTRAINTS:
- Base the resolution only on the policy text provided.
- Do not promise refunds, replacements, compensation or delivery dates unless the policy explicitly allows it.
- Reply in English, in a professional and polite tone.
OUTPUT FORMAT: Return ONLY a JSON object with exactly these keys:
{"complaint_summary": "", "category": "", "sentiment": "", "urgency": "", "customer_intent": "", "suggested_resolution": "", "missing_information": [], "risk_level": "", "generated_reply": ""}
risk_level and urgency must be one of: low, medium, high.

Customer complaint:
{complaint}

Company policy:
{policy_text}"""

# --------------------------------------------------------------------------- #
# Version 3 - Advanced policy-grounded prompt (retrieval + guardrails)
# --------------------------------------------------------------------------- #
V3_SYSTEM_PROMPT = """You are PolicyPilot, a policy-grounded customer support assistant.
You are given (a) a customer complaint and (b) ONLY the specific policy clauses retrieved for that complaint.

Hard rules:
1. Ground every claim in the retrieved clauses. Never use policy knowledge that is not in the provided clauses.
2. Never promise a refund, replacement, compensation or delivery date unless a retrieved clause explicitly permits it.
3. If a needed rule is missing or ambiguous, say so and add it to missing_information instead of guessing.
4. Detect when a human must review the case (missing policy, missing customer details, exception requests, high risk, low confidence).
5. If the complaint is not covered by the retrieved clauses, set human_review_required to true.
6. Reply to the customer in English. Ask for missing information when required.
7. Output valid JSON only, with no markdown fences and no extra text."""

V3_USER_PROMPT = """CUSTOMER CONTEXT
- Name: {customer_name}
- Order ID: {order_id}
- Product category: {product_category}

RETRIEVED POLICY CLAUSES (the only policy knowledge you may use)
{policy_clauses}

CUSTOMER COMPLAINT
{complaint}

Return ONLY this JSON object:
{"complaint_summary": "", "category": "", "sentiment": "", "urgency": "", "customer_intent": "", "policy_evidence": [], "suggested_resolution": "", "missing_information": [], "risk_level": "", "human_review_required": false, "human_review_reason": "", "generated_reply": ""}

Field rules:
- policy_evidence: list of the clause ids you relied on, e.g. ["c2", "c5"].
- missing_information: list of concrete facts still needed from the customer, e.g. ["order id", "photo of the damaged item"].
- risk_level and urgency: one of low, medium, high.
- human_review_required: true if the case is high risk, the policy is unclear or unavailable, the customer asks for an exception, or key information is missing.
- human_review_reason: one short sentence explaining the escalation when human_review_required is true, else an empty string."""

PROMPT_VARIABLES_V1: Dict[str, str] = {
    "complaint": "The customer's complaint text (free text).",
    "policy_text": "The full text of the selected policy document(s).",
}

PROMPT_VARIABLES_V2: Dict[str, str] = {
    "complaint": "The customer's complaint text (free text).",
    "policy_text": "The full text of the selected policy document(s).",
}

PROMPT_VARIABLES_V3: Dict[str, str] = {
    "customer_name": "Customer name from the form, or 'not provided'.",
    "order_id": "Order id from the form, or 'not provided'.",
    "product_category": "Product category from the form, or 'not provided'.",
    "policy_clauses": "The top-k clauses returned by the keyword retriever, each labelled [c1], [c2] ...",
    "complaint": "The customer's complaint text (free text).",
}

PROMPTS: Dict[str, PromptVersionInfo] = {
    "v1": PromptVersionInfo(
        id="v1",
        name="P1 - Basic reply",
        step="Step 1 of 3 - first-pass reply generation",
        purpose="Produce a quick, unstructured customer reply to establish a baseline.",
        tool_model="Gemini 2.5 Flash (Google AI Studio / Gemini API), default settings",
        settings="temperature 0.2, no response schema",
        system_prompt=V1_SYSTEM_PROMPT or "none",
        user_prompt_template=V1_USER_PROMPT,
        variables=PROMPT_VARIABLES_V1,
        examples_included=0,
        output_format="Plain text reply (no JSON, no metadata).",
    ),
    "v2": PromptVersionInfo(
        id="v2",
        name="P2 - Structured analysis",
        step="Step 2 of 3 - structured complaint analysis",
        purpose="Force consistent fields (category, sentiment, urgency, risk) via a fixed schema.",
        tool_model="Gemini 2.5 Flash (Google AI Studio / Gemini API)",
        settings="temperature 0.2, JSON output requested in the prompt",
        system_prompt=V2_SYSTEM_PROMPT,
        user_prompt_template=V2_USER_PROMPT,
        variables=PROMPT_VARIABLES_V2,
        examples_included=0,
        output_format="Single JSON object with 9 fixed keys.",
    ),
    "v3": PromptVersionInfo(
        id="v3",
        name="P3 - Policy-grounded resolution",
        step="Step 3 of 3 - grounded resolution, guardrails and escalation",
        purpose="Ground the answer in retrieved clauses, block unsupported promises and flag human review.",
        tool_model="Gemini 2.5 Flash (Google AI Studio / Gemini API)",
        settings="temperature 0.2, JSON output requested in the prompt",
        system_prompt=V3_SYSTEM_PROMPT,
        user_prompt_template=V3_USER_PROMPT,
        variables=PROMPT_VARIABLES_V3,
        examples_included=0,
        output_format=(
            "JSON object with 12 keys including policy_evidence, missing_information, "
            "risk_level, human_review_required, human_review_reason and generated_reply."
        ),
    ),
}


def render(template: str, values: Dict[str, str]) -> str:
    """Replace {tokens} in a template without touching JSON braces."""
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered
