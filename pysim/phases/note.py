"""Shared result type for takeoff / path / landing checks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PhaseNote:
    hint: str
    done: bool = False
    failed: bool = False
    fail_reason: str = ""
