from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any


@dataclass
class TraceEvent:
    kind: str
    payload: dict[str, Any]
    t: float


class InMemoryTracer:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []
        self._t0 = perf_counter()

    def emit(self, kind: str, **payload: Any) -> None:
        self.events.append(
            TraceEvent(kind=kind, payload=payload, t=perf_counter() - self._t0)
        )

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self.events:
            counts[event.kind] = counts.get(event.kind, 0) + 1
        return counts
