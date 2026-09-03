from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Policy:
    """Hard constraints the harness enforces *around* the model."""

    allowed_tools: frozenset[str] | None = None
    denied_tools: frozenset[str] = field(default_factory=frozenset)
    max_argument_chars: int = 8_000

    def check_tool(self, name: str, arguments_json: str) -> str | None:
        """Return a refusal reason, or None if the call is allowed."""
        if self.allowed_tools is not None and name not in self.allowed_tools:
            return f"tool '{name}' is not on the allow-list"
        if name in self.denied_tools:
            return f"tool '{name}' is denied by policy"
        if len(arguments_json) > self.max_argument_chars:
            return "tool arguments exceed size limit"
        return None


def default_policy() -> Policy:
    return Policy()
