"""Structured error model for generation and grading flows.

Every run folder gets a ``status.json`` that the frontend can rely on as
the single source of truth for whether the run succeeded, partially
succeeded (generation OK but grading failed), or fully failed.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


class ErrorType(str, Enum):
    GRADING_PARSE = "grading_parse"
    GRADING_VALIDATION = "grading_validation"
    GRADING_SCHEMA = "grading_schema"
    MERMAID_COMPILATION = "mermaid_compilation"
    GENERATION = "generation"
    UNEXPECTED = "unexpected"


class RunStatusValue(str, Enum):
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL = "partial"  # generation OK, grading failed
    FAILED = "failed"


@dataclass
class RunError:
    """Structured error information attached to a run status."""

    type: ErrorType
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "message": self.message,
            "details": self.details,
            "attempts": self.attempts,
        }


@dataclass
class RunStatus:
    """Persisted run status written to ``status.json``."""

    status: RunStatusValue
    error: Optional[RunError] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "error": self.error.to_dict() if self.error else None,
            "completed_at": self.completed_at,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_status(paths: dict, status: RunStatus) -> None:
    """Write ``status.json`` into the run folder indicated by *paths*."""
    base = paths.get("log_base_dir")
    if not base:
        return
    if status.status in {
        RunStatusValue.SUCCESS,
        RunStatusValue.PARTIAL,
        RunStatusValue.FAILED,
    } and status.completed_at is None:
        status.completed_at = _now_iso()
    dest = os.path.join(base, "status.json")
    try:
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(status.to_dict(), f, indent=2)
    except OSError:
        pass  # best-effort


def read_status(folder: str) -> Optional[dict[str, Any]]:
    """Read ``status.json`` from a run folder. Returns *None* if missing."""
    path = os.path.join(folder, "status.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def write_success(paths: dict) -> None:
    write_status(paths, RunStatus(status=RunStatusValue.SUCCESS))


def write_failure(paths: dict, error: RunError) -> None:
    write_status(paths, RunStatus(status=RunStatusValue.FAILED, error=error))


def write_partial(paths: dict, error: RunError) -> None:
    """Generation succeeded but a downstream step (e.g. grading) failed."""
    write_status(paths, RunStatus(status=RunStatusValue.PARTIAL, error=error))


def write_in_progress(paths: dict) -> None:
    write_status(paths, RunStatus(status=RunStatusValue.IN_PROGRESS))
