"""Explainable keyword-based policy retrieval.

This module is intentionally transparent: every retrieved clause comes with the
exact score that produced it, so the UI and the evaluator can see *why* a clause
was selected. No embeddings or black-box models are used here.
"""
from __future__ import annotations

import re
from typing import List, Sequence, Tuple

from ..schemas.models import PolicyClause

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in", "on",
    "for", "with", "is", "are", "was", "were", "be", "been", "being", "am", "i",
    "we", "you", "they", "he", "she", "it", "my", "our", "your", "their", "this",
    "that", "these", "those", "as", "at", "by", "from", "has", "have", "had",
    "do", "does", "did", "will", "would", "can", "could", "should", "not", "no",
    "please", "dear", "hi", "hello", "thanks", "thank", "regards", "sir", "madam",
}

_NUMBERED_HEADING = re.compile(r"^\s*(?:\d+(?:\.\d+)*|[IVX]+\.)\s+\S")
_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> List[str]:
    """Lowercase word tokens with stopwords removed."""
    return [w for w in _WORD.findall(text.lower()) if w not in _STOPWORDS and len(w) > 1]


def split_clauses(text: str) -> List[Tuple[str, str]]:
    """Split raw policy text into (heading, body) clauses.

    Blocks are separated by blank lines. A leading numbered/uppercase line is
    promoted to the heading; otherwise the first sentence acts as the heading.
    """
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    # Also split on numbered headings that are not preceded by a blank line.
    expanded: List[str] = []
    for block in blocks:
        lines = block.split("\n")
        current: List[str] = []
        for line in lines:
            if _NUMBERED_HEADING.match(line) and current:
                expanded.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            expanded.append("\n".join(current).strip())

    clauses: List[Tuple[str, str]] = []
    for block in expanded:
        if not block:
            continue
        first_line = block.split("\n", 1)[0]
        if _NUMBERED_HEADING.match(first_line) or (
            first_line.isupper() and len(first_line) > 3
        ) or len(first_line) < 70:
            heading = first_line.strip(" :.")
            body = block
        else:
            heading = block.split(".")[0][:60].strip()
            body = block
        clauses.append((heading, body))
    return clauses


def retrieve_relevant_clauses(
    policy_text: str, complaint: str, top_k: int = 4
) -> List[PolicyClause]:
    """Return the top-k clauses ranked by keyword overlap with the complaint."""
    if not policy_text.strip() or not complaint.strip():
        return []

    complaint_tokens = set(tokenize(complaint))
    # Bigrams boost precision for phrases like "refund period" or "wrong item".
    words = tokenize(complaint)
    complaint_bigrams = {f"{a} {b}" for a, b in zip(words, words[1:])}

    scored: List[PolicyClause] = []
    for index, (heading, body) in enumerate(split_clauses(policy_text), start=1):
        clause_tokens = tokenize(body)
        if not clause_tokens:
            continue
        clause_set = set(clause_tokens)
        overlap = complaint_tokens & clause_set
        # Term frequency of overlapping tokens (capped) keeps long clauses fair.
        hits = 0
        for token in complaint_tokens:
            hits += min(body.lower().count(token), 3)
        bigram_hits = sum(1 for bg in complaint_bigrams if bg in body.lower())
        score = (len(overlap) / max(len(complaint_tokens), 1)) * 10.0
        score += hits * 0.15
        score += bigram_hits * 1.5
        if score <= 0:
            continue
        scored.append(
            PolicyClause(
                clause_id=f"c{index}",
                heading=heading,
                text=body,
                score=round(score, 3),
            )
        )

    scored.sort(key=lambda clause: clause.score, reverse=True)
    return scored[:top_k]


def format_clauses_for_prompt(clauses: Sequence[PolicyClause]) -> str:
    """Render retrieved clauses as numbered evidence blocks for the prompt."""
    if not clauses:
        return "NO POLICY CLAUSES RETRIEVED."
    lines = []
    for clause in clauses:
        lines.append(f"[{clause.clause_id}] {clause.heading}\n{clause.text}")
    return "\n\n".join(lines)
