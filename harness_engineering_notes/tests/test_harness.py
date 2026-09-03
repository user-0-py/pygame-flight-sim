"""Tests for the teaching harness (no network, no API keys)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent_harness import (  # noqa: E402
    AgentHarness,
    HarnessConfig,
    InMemoryTracer,
    Message,
    MockToolModel,
    Policy,
    ToolCall,
    ToolRegistry,
    ToolSpec,
    compact_messages,
)
from agent_harness.tools import ToolError  # noqa: E402
from agent_harness.workspace import ToyWorkspace  # noqa: E402


def _echo_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="echo",
            description="Return the given text.",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        ),
        lambda text: text,
    )
    return registry


def test_single_tool_then_final_answer():
    model = MockToolModel(
        [
            Message(
                role="assistant",
                tool_calls=[
                    ToolCall(id="c1", name="echo", arguments={"text": "ping"})
                ],
            ),
            Message(role="assistant", content="pong from echo"),
        ]
    )
    harness = AgentHarness(
        model=model,
        tools=_echo_registry(),
        system_prompt="Use echo, then answer.",
    )
    result = harness.run("say ping")
    assert result.stop_reason == "final_text"
    assert result.final_text == "pong from echo"
    assert result.steps == 2
    assert result.tracer.summary()["tool_ok"] == 1


def test_unknown_tool_becomes_observation_not_crash():
    model = MockToolModel(
        [
            Message(
                role="assistant",
                tool_calls=[ToolCall(id="c1", name="boom", arguments={})],
            ),
            Message(role="assistant", content="recovered"),
        ]
    )
    harness = AgentHarness(
        model=model, tools=_echo_registry(), system_prompt="Be careful."
    )
    result = harness.run("hi")
    tool_msg = next(m for m in result.messages if m.role == "tool")
    assert tool_msg.content.startswith("ERROR:")
    assert result.final_text == "recovered"


def test_policy_blocks_denied_tool():
    registry = _echo_registry()
    registry.register(
        ToolSpec(name="rm", description="delete", parameters={"type": "object"}),
        lambda: "deleted",
    )
    model = MockToolModel(
        [
            Message(
                role="assistant",
                tool_calls=[ToolCall(id="c1", name="rm", arguments={})],
            ),
            Message(role="assistant", content="blocked, good"),
        ]
    )
    harness = AgentHarness(
        model=model,
        tools=registry,
        system_prompt="Follow policy.",
        policy=Policy(denied_tools=frozenset({"rm"})),
    )
    result = harness.run("delete everything")
    tool_msg = next(m for m in result.messages if m.role == "tool")
    assert "denied" in tool_msg.content
    assert result.tracer.summary().get("policy_block") == 1


def test_max_steps_stop_reason():
    model = MockToolModel(
        [
            Message(
                role="assistant",
                tool_calls=[
                    ToolCall(id="c1", name="echo", arguments={"text": "loop"})
                ],
            )
            for _ in range(5)
        ]
    )
    harness = AgentHarness(
        model=model,
        tools=_echo_registry(),
        system_prompt="loop",
        config=HarnessConfig(max_steps=3),
    )
    result = harness.run("loop")
    assert result.stop_reason == "max_steps"
    assert result.final_text == ""
    assert result.steps == 3


def test_compact_truncates_old_tool_payloads():
    messages = [
        Message(role="system", content="sys"),
        Message(role="user", content="q"),
        Message(role="assistant", content="call"),
        Message(role="tool", content="x" * 2000, tool_call_id="1", name="echo"),
        Message(role="assistant", content="more"),
        Message(role="user", content="again"),
        Message(role="assistant", content="call2"),
        Message(role="tool", content="short", tool_call_id="2", name="echo"),
        Message(role="assistant", content="done"),
    ]
    out = compact_messages(messages, keep_last=3, max_tool_chars=20)
    old_tool = next(m for m in out if m.role == "tool" and m.tool_call_id == "1")
    assert "truncated by harness" in old_tool.content
    assert len(old_tool.content) < 80


def test_workspace_read_and_escape(tmp_path: Path):
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")
    ws = ToyWorkspace(tmp_path)
    assert "hello" in ws.read_file("note.txt")
    with pytest.raises(ToolError):
        ws.read_file("../secret")


def test_file_agent_answers_from_runbook():
    root = ROOT / "examples" / "toy_workspace"
    ws = ToyWorkspace(root)
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="list_files",
            description="List workspace files.",
            parameters={"type": "object", "properties": {}},
        ),
        lambda: ws.list_files(),
    )
    registry.register(
        ToolSpec(
            name="read_file",
            description="Read a workspace file.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        ),
        lambda path: ws.read_file(path),
    )
    model = MockToolModel(
        [
            Message(
                role="assistant",
                tool_calls=[ToolCall(id="1", name="list_files", arguments={})],
            ),
            Message(
                role="assistant",
                tool_calls=[
                    ToolCall(id="2", name="read_file", arguments={"path": "RUNBOOK.md"})
                ],
            ),
            Message(
                role="assistant",
                content="On-call is #infra-oncall.",
            ),
        ]
    )
    harness = AgentHarness(
        model=model,
        tools=registry,
        system_prompt="Answer from files only.",
    )
    result = harness.run("Who is on-call for checkout-service?")
    assert "#infra-oncall" in result.final_text
    listed = next(m.content for m in result.messages if m.role == "tool" and m.name == "list_files")
    assert "RUNBOOK.md" in listed


def test_mlflow_logs_parent_and_nested_tool_runs(tmp_path: Path):
    from agent_harness import configure_local_tracking, log_harness_run, search_experiment_table

    uri = configure_local_tracking(tmp_path / "mlruns")
    assert uri.startswith("sqlite:")
    model = MockToolModel(
        [
            Message(
                role="assistant",
                tool_calls=[ToolCall(id="c1", name="echo", arguments={"text": "ping"})],
            ),
            Message(role="assistant", content="pong"),
        ]
    )
    harness = AgentHarness(
        model=model,
        tools=_echo_registry(),
        system_prompt="echo then stop",
        tracer=InMemoryTracer(),
    )
    result = harness.run("ping")
    run_id = log_harness_run(
        result,
        experiment="harness-unit",
        run_name="echo-happy-path",
        harness=harness,
        extra_metrics={"task_correct": 1.0},
    )
    assert run_id
    table = search_experiment_table("harness-unit")
    assert len(table) == 1
    assert table[0]["run_name"] == "echo-happy-path"
    assert table[0]["stop_reason"] == "final_text"
    assert table[0]["tool_ok"] == 1.0
    assert table[0]["task_correct"] == 1.0
