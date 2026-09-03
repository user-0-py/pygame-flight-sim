from __future__ import annotations

import json
from typing import Any

from .models import ToolFn, ToolSpec


class ToolError(Exception):
    """Raised inside a tool so the harness can turn it into an observation."""


class ToolRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._fns: dict[str, ToolFn] = {}

    def register(self, spec: ToolSpec, fn: ToolFn) -> None:
        if spec.name in self._specs:
            raise ValueError(f"duplicate tool: {spec.name}")
        self._specs[spec.name] = spec
        self._fns[spec.name] = fn

    def specs(self) -> list[ToolSpec]:
        return list(self._specs.values())

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        if name not in self._fns:
            raise ToolError(f"unknown tool '{name}'")
        try:
            result = self._fns[name](**arguments)
        except TypeError as exc:
            raise ToolError(f"bad arguments for '{name}': {exc}") from exc
        except ToolError:
            raise
        except Exception as exc:  # noqa: BLE001 — tools must not crash the loop
            raise ToolError(f"tool '{name}' failed: {exc}") from exc
        if not isinstance(result, str):
            result = json.dumps(result, default=str)
        return result
