from __future__ import annotations

from .models import Message


def compact_messages(
    messages: list[Message],
    *,
    keep_last: int = 6,
    max_tool_chars: int = 400,
) -> list[Message]:
    """Keep system + recent turns; truncate older tool observations.

    Real production harnesses replace this with token-aware summarization.
    The important idea is: the *harness* owns context, not the model.
    """
    if len(messages) <= keep_last + 1:
        return list(messages)

    head: list[Message] = []
    if messages and messages[0].role == "system":
        head.append(messages[0])
        body = messages[1:]
    else:
        body = messages

    older, recent = body[:-keep_last], body[-keep_last:]
    compacted: list[Message] = []
    for msg in older:
        if msg.role == "tool" and len(msg.content) > max_tool_chars:
            compacted.append(
                Message(
                    role="tool",
                    content=msg.content[:max_tool_chars] + "\n…[truncated by harness]",
                    tool_call_id=msg.tool_call_id,
                    name=msg.name,
                )
            )
        else:
            compacted.append(msg)
    return head + compacted + recent
