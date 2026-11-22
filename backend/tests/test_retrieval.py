"""Tests for the explainable keyword policy retriever."""
from app.services.retrieval import (
    format_clauses_for_prompt,
    retrieve_relevant_clauses,
    split_clauses,
    tokenize,
)

POLICY = """
1. REFUND POLICY
Customers may request a full refund within 7 days of delivery if the item is unused
and returned in its original packaging. Refunds are processed to the original payment
method within 5 to 7 business days after inspection.

2. REPLACEMENT POLICY
Damaged or defective items reported within 10 days of delivery are eligible for a free
replacement. A photograph of the damage must be provided with the request.

3. DELIVERY POLICY
Standard delivery takes 4 to 6 business days. Delayed deliveries are not eligible for
compensation unless the delay exceeds 15 days.

4. EXCEPTIONS
Requests outside these windows require human review and manager approval.
"""


def test_tokenize_removes_stopwords():
    tokens = tokenize("Please refund the damaged item")
    assert "the" not in tokens
    assert "refund" in tokens
    assert "damaged" in tokens


def test_split_clauses_detects_numbered_headings():
    clauses = split_clauses(POLICY)
    headings = [heading for heading, _ in clauses]
    assert any("REFUND POLICY" in heading for heading in headings)
    assert len(clauses) >= 4


def test_retriever_returns_refund_clause_for_refund_complaint():
    clauses = retrieve_relevant_clauses(POLICY, "I want a refund for my order")
    assert clauses, "expected at least one clause"
    assert "refund" in clauses[0].text.lower()


def test_retriever_returns_delivery_clause_for_late_delivery():
    clauses = retrieve_relevant_clauses(POLICY, "My parcel is very late and still not delivered")
    joined = " ".join(clause.text.lower() for clause in clauses)
    assert "delivery" in joined


def test_retriever_returns_empty_for_blank_complaint():
    assert retrieve_relevant_clauses(POLICY, "   ") == []


def test_format_clauses_is_human_readable():
    clauses = retrieve_relevant_clauses(POLICY, "defective product replacement")
    rendered = format_clauses_for_prompt(clauses)
    assert "[" in rendered and "]" in rendered
