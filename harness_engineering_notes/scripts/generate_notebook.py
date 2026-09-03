#!/usr/bin/env python3
"""Generate the teaching notebook (keeps JSON boring and valid)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

cells: list[dict] = []


def md(text: str) -> None:
    cells.append(
        {
            "id": uuid.uuid4().hex[:12],
            "cell_type": "markdown",
            "metadata": {},
            "source": text.splitlines(keepends=True),
        }
    )


def code(text: str) -> None:
    cells.append(
        {
            "id": uuid.uuid4().hex[:12],
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": text.splitlines(keepends=True),
        }
    )


md(
    """# Building an agent harness, step by step

This notebook is the lab companion to [`../index.html`](../index.html).

We will **not** start from a vendor SDK. We grow a harness from a message list into a policy-bounded loop that can read files in `examples/toy_workspace`. A language model is treated as a function:

`complete(messages, tools) -> assistant_message`

A **scripted mock** stands in for that function so every cell runs offline. Swapping in a real API is the last section, not the first.
"""
)

code(
    """from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

ROOT = Path.cwd().resolve()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

print("notes root:", ROOT)
"""
)

md(
    """## Step 1 — Messages are the whole state

An episode is a list of messages. Roles we need:

| role | who writes it | purpose |
| --- | --- | --- |
| `system` | harness | job + constraints |
| `user` | harness (from the human) | the task |
| `assistant` | model | text and/or tool calls |
| `tool` | harness | observation after a call |

The model never mutates this list itself. The harness appends.
"""
)

code(
    '''@dataclass
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


def show(messages: list[Message]) -> None:
    for m in messages:
        extra = ""
        if m.tool_calls:
            extra = " tools=" + ",".join(c.name for c in m.tool_calls)
        if m.role == "tool":
            extra = f" name={m.name}"
        preview = (m.content or "")[:90].replace("\\n", " ")
        print(f"[{m.role:10}]{extra:22} {preview}")


transcript = [
    Message("system", "You are a careful file-research agent."),
    Message("user", "Who is on-call?"),
]
show(transcript)
'''
)

md(
    """## Step 2 — A model is just `complete()`

`MockToolModel` pops a prewritten assistant turn each time it is called. That is enough to teach the loop, and enough to write pytest later.
"""
)

code(
    '''class MockToolModel:
    def __init__(self, script: list[Message]):
        self.script = list(script)
        self.seen_lengths: list[int] = []

    def complete(self, messages: list[Message], tools: list[Any]) -> Message:
        self.seen_lengths.append(len(messages))
        if not self.script:
            return Message(role="assistant", content="(script exhausted)")
        return self.script.pop(0)


demo_model = MockToolModel([Message(role="assistant", content="I would look in the runbook.")])
print(demo_model.complete(transcript, []).content)
'''
)

md(
    """## Step 3 — Tools are a protocol

Register a JSON Schema **and** a Python function. The model only sees the spec. Execution happens in the harness. Exceptions become `ToolError` so the loop can turn them into observations instead of crashing.
"""
)

code(
    '''class ToolError(Exception):
    pass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._fns: dict[str, Callable[..., str]] = {}

    def register(self, spec: ToolSpec, fn: Callable[..., str]) -> None:
        self._specs[spec.name] = spec
        self._fns[spec.name] = fn

    def specs(self) -> list[ToolSpec]:
        return list(self._specs.values())

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        if name not in self._fns:
            raise ToolError(f"unknown tool '{name}'. valid: {sorted(self._fns)}")
        try:
            out = self._fns[name](**arguments)
        except ToolError:
            raise
        except Exception as exc:
            raise ToolError(f"tool '{name}' failed: {exc}") from exc
        return out if isinstance(out, str) else json.dumps(out)


tools = ToolRegistry()
tools.register(
    ToolSpec(
        "echo",
        "Return text unchanged.",
        {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    ),
    lambda text: text,
)
print(tools.execute("echo", {"text": "harness > model"}))
try:
    tools.execute("not_a_tool", {})
except ToolError as e:
    print("caught:", e)
'''
)

md(
    """## Step 4 — The loop: propose, dispose, observe

This is the entire theory in executable form. The model may request tools. The harness runs them (or refuses). Observations go back on the tape. We stop on final text or `max_steps`.
"""
)

code(
    '''def run_loop(
    model: MockToolModel,
    tools: ToolRegistry,
    user_text: str,
    system: str,
    max_steps: int = 6,
) -> list[Message]:
    messages = [Message("system", system), Message("user", user_text)]
    for step in range(1, max_steps + 1):
        assistant = model.complete(messages, tools.specs())
        messages.append(assistant)
        if not assistant.tool_calls:
            print(f"stop: final_text at step {step}")
            return messages
        for call in assistant.tool_calls:
            try:
                observation = tools.execute(call.name, call.arguments)
            except ToolError as exc:
                observation = f"ERROR: {exc}"
            messages.append(
                Message("tool", observation, tool_call_id=call.id, name=call.name)
            )
        print(f"step {step}: executed {[c.name for c in assistant.tool_calls]}")
    print("stop: max_steps")
    return messages


scripted = MockToolModel(
    [
        Message(
            role="assistant",
            tool_calls=[ToolCall("1", "echo", {"text": "ping"})],
        ),
        Message(role="assistant", content="The echo came back: ping"),
    ]
)
out = run_loop(scripted, tools, "ping the echo tool", "Use tools when useful.")
show(out)
'''
)

md(
    """## Step 5 — Policy is code, not a plea in the system prompt

Add a gate **before** `execute`. A blocked call still becomes a tool message, so the model can recover. Production harnesses jail paths, cap payload size, and require approval for writes the same way.
"""
)

code(
    '''@dataclass(frozen=True)
class Policy:
    denied_tools: frozenset[str] = frozenset()
    max_argument_chars: int = 8000

    def check(self, name: str, arguments: dict[str, Any]) -> str | None:
        if name in self.denied_tools:
            return f"tool '{name}' is denied by policy"
        blob = json.dumps(arguments)
        if len(blob) > self.max_argument_chars:
            return "arguments too large"
        return None


def run_loop_with_policy(
    model: MockToolModel,
    tools: ToolRegistry,
    user_text: str,
    system: str,
    policy: Policy,
    max_steps: int = 6,
) -> list[Message]:
    messages = [Message("system", system), Message("user", user_text)]
    for _ in range(max_steps):
        assistant = model.complete(messages, tools.specs())
        messages.append(assistant)
        if not assistant.tool_calls:
            return messages
        for call in assistant.tool_calls:
            refusal = policy.check(call.name, call.arguments)
            if refusal:
                observation = f"ERROR: {refusal}"
            else:
                try:
                    observation = tools.execute(call.name, call.arguments)
                except ToolError as exc:
                    observation = f"ERROR: {exc}"
            messages.append(Message("tool", observation, tool_call_id=call.id, name=call.name))
    return messages


tools.register(
    ToolSpec("rm", "Dangerous demo tool.", {"type": "object", "properties": {}}),
    lambda: "deleted",
)
locked = MockToolModel(
    [
        Message(role="assistant", tool_calls=[ToolCall("x", "rm", {})]),
        Message(role="assistant", content="I cannot delete; policy blocked rm."),
    ]
)
blocked = run_loop_with_policy(
    locked, tools, "delete the disk", "Follow policy.", Policy(denied_tools=frozenset({"rm"}))
)
show(blocked)
'''
)

md(
    """## Step 6 — Trace the trajectory

If you cannot name the stop reason, you cannot debug the agent. Emit a few event kinds: `model_turn`, `tool_ok`, `tool_error`, `policy_block`.
"""
)

code(
    '''class Tracer:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.t0 = perf_counter()

    def emit(self, kind: str, **payload: Any) -> None:
        self.events.append({"kind": kind, "t": round(perf_counter() - self.t0, 4), **payload})


tracer = Tracer()
tracer.emit("run_start", user="Who is on-call?")
tracer.emit("model_turn", step=1, n_tool_calls=1)
tracer.emit("tool_ok", tool="read_file")
tracer.emit("run_end", reason="final_text")
print(json.dumps(tracer.events, indent=2))
'''
)

md(
    """## Step 7 — Context is curated

Old tool payloads rot the working tape. Truncate them. Real systems also summarize and offload to files; the *ownership* is the point: the harness, not the model, decides what remains in context.
"""
)

code(
    '''def compact_messages(messages: list[Message], keep_last: int = 4, max_tool_chars: int = 80) -> list[Message]:
    if len(messages) <= keep_last + 1:
        return list(messages)
    head, body = ([messages[0]] if messages[0].role == "system" else []), (
        messages[1:] if messages[0].role == "system" else messages
    )
    older, recent = body[:-keep_last], body[-keep_last:]
    out = []
    for m in older:
        if m.role == "tool" and len(m.content) > max_tool_chars:
            out.append(
                Message(
                    "tool",
                    m.content[:max_tool_chars] + "\\n…[truncated by harness]",
                    tool_call_id=m.tool_call_id,
                    name=m.name,
                )
            )
        else:
            out.append(m)
    return head + out + recent


bloated = [
    Message("system", "sys"),
    Message("user", "q"),
    Message("assistant", "call"),
    Message("tool", "LOG " + "x" * 400, tool_call_id="1", name="echo"),
    Message("assistant", "still going"),
    Message("user", "continue"),
    Message("assistant", "done"),
]
for m in compact_messages(bloated, keep_last=2, max_tool_chars=20):
    print(m.role, len(m.content), m.content[-24:])
'''
)

md(
    """## Step 8 — A tiny file agent (the packaged harness)

We switch to `src/agent_harness`, the same loop with tests. Tools: `list_files` and `read_file` over `examples/toy_workspace`. The mock model lists, then reads `RUNBOOK.md`, then answers.
"""
)

code(
    '''from agent_harness import (
    AgentHarness,
    Message as HMessage,
    MockToolModel as HMock,
    ToolCall as HToolCall,
    ToolRegistry,
    ToolSpec,
)
from agent_harness.workspace import ToyWorkspace

ws = ToyWorkspace(ROOT / "examples" / "toy_workspace")
registry = ToolRegistry()
registry.register(
    ToolSpec("list_files", "List workspace files.", {"type": "object", "properties": {}}),
    lambda: ws.list_files(),
)
registry.register(
    ToolSpec(
        "read_file",
        "Read a workspace file by relative path.",
        {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    ),
    lambda path: ws.read_file(path),
)

model = HMock(
    [
        HMessage(role="assistant", tool_calls=[HToolCall("1", "list_files", {})]),
        HMessage(
            role="assistant",
            tool_calls=[HToolCall("2", "read_file", {"path": "RUNBOOK.md"})],
        ),
        HMessage(role="assistant", content="On-call for checkout-service is #infra-oncall."),
    ]
)

harness = AgentHarness(
    model=model,
    tools=registry,
    system_prompt="Answer only from workspace files. Prefer list_files then read_file.",
)
result = harness.run("Who is on-call for checkout-service?")
print("stop_reason:", result.stop_reason)
print("steps:", result.steps)
print("final:", result.final_text)
print("trace:", result.tracer.summary())
print("--- messages ---")
for m in result.messages:
    bit = m.content[:70].replace("\\n", " ")
    print(f"{m.role:10} {m.name or ''} {bit}")
'''
)

md(
    """## Step 9 — Evaluate the harness, then the agent

Two layers of tests:

1. **Harness tests** (no network): scripted model, assert stop reasons and policy blocks. See `tests/test_harness.py`.
2. **Task tests**: did the trajectory read the runbook and quote the on-call channel?

Golden tasks are small environments with a known answer. Scale that idea and you get SWE-bench-style eval: isolate a world, let the agent act, run a verifier.
"""
)

code(
    '''assert result.stop_reason == "final_text"
assert "#infra-oncall" in result.final_text
assert result.tracer.summary().get("tool_ok") == 2
print("golden task passed")
'''
)

md(
    """## Step 10 — Plug in a real model (optional)

Replace only `complete()`. The loop, registry, policy, and tracer stay. Sketch of an OpenAI-compatible adapter (not executed here):

```python
class OpenAICompatModel:
    def __init__(self, client, model: str):
        self.client, self.model = client, model

    def complete(self, messages, tools):
        payload = serialize_messages(messages)
        schemas = serialize_tools(tools)
        resp = self.client.chat.completions.create(
            model=self.model, messages=payload, tools=schemas
        )
        return parse_assistant(resp.choices[0].message)
```

If wiring a vendor forces you to rewrite the while-loop, the theory never made it into the harness.

**Next:** open `../index.html` for the full argument, then run `PYTHONPATH=src pytest tests` from the notes root.
"""
)

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    },
    "cells": cells,
}

out = Path(__file__).resolve().parents[1] / "notebooks" / "01_harness_from_scratch.ipynb"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(nb, indent=2), encoding="utf-8")
print("wrote", out)
