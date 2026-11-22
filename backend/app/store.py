"""Tiny JSON-file backed store for policies and complaint records.

The goal is a zero-setup, inspectable persistence layer for a student project.
It is deliberately simple: two JSON files plus a thread lock.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schemas.models import AnalysisRecord, PolicyDetail

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_POLICY_FILE = os.path.join(_DATA_DIR, "policies.json")
_COMPLAINT_FILE = os.path.join(_DATA_DIR, "complaints.json")

_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []


def _write(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


# --------------------------------------------------------------------------- #
# Policies
# --------------------------------------------------------------------------- #
def add_policy(policy: PolicyDetail) -> PolicyDetail:
    with _LOCK:
        rows = _read(_POLICY_FILE)
        rows.append(policy.model_dump())
        _write(_POLICY_FILE, rows)
    return policy


def list_policies() -> List[PolicyDetail]:
    return [PolicyDetail(**row) for row in _read(_POLICY_FILE)]


def get_policy(policy_id: str) -> Optional[PolicyDetail]:
    for row in _read(_POLICY_FILE):
        if row.get("id") == policy_id:
            return PolicyDetail(**row)
    return None


def delete_policy(policy_id: str) -> bool:
    with _LOCK:
        rows = _read(_POLICY_FILE)
        remaining = [row for row in rows if row.get("id") != policy_id]
        removed = len(remaining) != len(rows)
        if removed:
            _write(_POLICY_FILE, remaining)
    return removed


# --------------------------------------------------------------------------- #
# Complaints
# --------------------------------------------------------------------------- #
def add_complaint(record: AnalysisRecord) -> AnalysisRecord:
    with _LOCK:
        rows = _read(_COMPLAINT_FILE)
        rows.append(record.model_dump())
        _write(_COMPLAINT_FILE, rows)
    return record


def list_complaints() -> List[AnalysisRecord]:
    rows = _read(_COMPLAINT_FILE)
    rows.sort(key=lambda row: row.get("created_at", ""), reverse=True)
    return [AnalysisRecord(**row) for row in rows]


def get_complaint(record_id: str) -> Optional[AnalysisRecord]:
    for row in _read(_COMPLAINT_FILE):
        if row.get("id") == record_id:
            return AnalysisRecord(**row)
    return None


def update_complaint(record_id: str, patch: Dict[str, Any]) -> Optional[AnalysisRecord]:
    with _LOCK:
        rows = _read(_COMPLAINT_FILE)
        updated: Optional[AnalysisRecord] = None
        for row in rows:
            if row.get("id") == record_id:
                row.update(patch)
                updated = AnalysisRecord(**row)
        if updated is not None:
            _write(_COMPLAINT_FILE, rows)
    return updated


def policy_count() -> int:
    return len(_read(_POLICY_FILE))
