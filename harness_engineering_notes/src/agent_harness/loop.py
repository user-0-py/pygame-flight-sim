from __future__ import annotations

import json
from dataclasses import dataclass, field

from .context import compact_messages
from .models import LanguageModel, Message, ToolCall
from .policies import Policy, default_policy
from .tools import ToolError, ToolRegistry
from .tracing import InMemoryTracer


@dataclass
class HarnessConfig:
    max_steps: int = 8
    compact_every: int = 0  # 0 = never; otherwise compact after N messages
    keep_last: int = 6
    stop_on_empty_tool_calls: bool = True


@dataclass
class RunResult:
    final_text: str
    messages: list[Message]
    steps: int
    stop_reason: str
    tracer: InMemoryTracer


@dataclass
class AgentHarness:
    model: LanguageModel
    tools: ToolRegistry
    system_prompt: str
    policy: Policy = field(default_factory=default_policy)
    config: HarnessConfig = field(default_factory=HarnessConfig)
    tracer: InMemoryTracer = field(default_factory=InMemoryTracer)

    def run(self, user_text: str) -> RunResult:
        messages: list[Message] = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_text),
        ]
        self.tracer.emit("run_start", user=user_text)

        for step in range(1, self.config.max_steps + 1):
            if self.config.compact_every and len(messages) > self.config.compact_every:
                messages = compact_messages(messages, keep_last=self.config.keep_last)
                self.tracer.emit("context_compacted", n=len(messages))

            assistant = self.model.complete(messages, self.tools.specs())
            messages.append(assistant)
            self.tracer.emit(
                "model_turn",
                step=step,
                content=assistant.content,
                n_tool_calls=len(assistant.tool_calls),
            )

            if not assistant.tool_calls:
                self.tracer.emit("run_end", reason="final_text", steps=step)
                return RunResult(
                    final_text=assistant.content,
                    messages=messages,
                    steps=step,
                    stop_reason="final_text",
                    tracer=self.tracer,
                )

            for call in assistant.tool_calls:
                observation = self._dispatch(call)
                messages.append(
                    Message(
                        role="tool",
                        content=observation,
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )

        self.tracer.emit("run_end", reason="max_steps", steps=self.config.max_steps)
        return RunResult(
            final_text="",
            messages=messages,
            steps=self.config.max_steps,
            stop_reason="max_steps",
            tracer=self.tracer,
        )

    def _dispatch(self, call: ToolCall) -> str:
        args_json = json.dumps(call.arguments, default=str)
        refusal = self.policy.check_tool(call.name, args_json)
        if refusal:
            self.tracer.emit("policy_block", tool=call.name, reason=refusal)
            return f"ERROR: {refusal}"
        try:
            result = self.tools.execute(call.name, call.arguments)
        except ToolError as exc:
            self.tracer.emit("tool_error", tool=call.name, error=str(exc))
            return f"ERROR: {exc}"
        self.tracer.emit("tool_ok", tool=call.name, n_chars=len(result))
        return result
