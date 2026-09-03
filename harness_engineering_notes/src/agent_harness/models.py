from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    role: str
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


class LanguageModel(Protocol):
    def complete(self, messages: list[Message], tools: list[ToolSpec]) -> Message:
        """Return an assistant message: either final text or tool_calls."""


class MockToolModel:
    """Deterministic stand-in for an LLM.

    ``script`` is a list of assistant messages. Each call to ``complete``
    pops the next scripted turn. Useful for tests and for teaching the
    harness loop without an API key.
    """

    def __init__(self, script: list[Message]):
        self.script = list(script)
        self.calls: list[list[Message]] = []

    def complete(self, messages: list[Message], tools: list[ToolSpec]) -> Message:
        self.calls.append(list(messages))
        if not self.script:
            return Message(role="assistant", content="(script exhausted)")
        return self.script.pop(0)


# Type alias for tool implementations.
ToolFn = Callable[..., str]
