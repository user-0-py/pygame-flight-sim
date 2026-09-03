from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mlflow

from .loop import AgentHarness, RunResult


def configure_local_tracking(tracking_dir: Path) -> str:
    """SQLite-backed MLflow so the notebook runs without a server.

    Current MLflow treats the legacy ``./mlruns`` file store as
    maintenance-mode; sqlite is the local default that still matches
    'one machine, no ops.'
    """
    tracking_dir = tracking_dir.resolve()
    tracking_dir.mkdir(parents=True, exist_ok=True)
    db = tracking_dir / "mlflow.db"
    uri = f"sqlite:///{db}"
    mlflow.set_tracking_uri(uri)
    return uri


def log_harness_run(
    result: RunResult,
    *,
    experiment: str,
    run_name: str,
    harness: AgentHarness,
    extra_metrics: dict[str, float] | None = None,
    extra_params: dict[str, Any] | None = None,
) -> str:
    """One parent run per episode; nested runs per tool dispatch.

    This is the engineering analogue of 'the harness owns observability':
    params are knobs you set, metrics are what the episode did, artifacts
    are the replayable transcript.
    """
    mlflow.set_experiment(experiment)
    summary = result.tracer.summary()
    params = {
        "max_steps": harness.config.max_steps,
        "compact_every": harness.config.compact_every,
        "keep_last": harness.config.keep_last,
        "n_tools": len(harness.tools.specs()),
        "n_denied_tools": len(harness.policy.denied_tools),
        "system_prompt_chars": len(harness.system_prompt),
    }
    if extra_params:
        params.update({k: _param_value(v) for k, v in extra_params.items()})

    with mlflow.start_run(run_name=run_name) as parent:
        mlflow.log_params({k: _param_value(v) for k, v in params.items()})
        mlflow.set_tags(
            {
                "stop_reason": result.stop_reason,
                "harness": "agent_harness",
            }
        )
        mlflow.log_metrics(
            {
                "steps": float(result.steps),
                "tool_ok": float(summary.get("tool_ok", 0)),
                "tool_error": float(summary.get("tool_error", 0)),
                "policy_block": float(summary.get("policy_block", 0)),
                "context_compacted": float(summary.get("context_compacted", 0)),
                "final_chars": float(len(result.final_text)),
                "success": 1.0 if result.stop_reason == "final_text" else 0.0,
            }
        )
        if extra_metrics:
            mlflow.log_metrics(extra_metrics)

        for event in result.tracer.events:
            if event.kind not in {"tool_ok", "tool_error", "policy_block"}:
                continue
            child_name = f"{event.kind}:{event.payload.get('tool', 'unknown')}"
            with mlflow.start_run(run_name=child_name, nested=True):
                mlflow.log_params(
                    {
                        "event": event.kind,
                        "tool": str(event.payload.get("tool", "")),
                    }
                )
                numeric = {
                    k: float(v)
                    for k, v in event.payload.items()
                    if isinstance(v, (int, float)) and k != "tool"
                }
                if numeric:
                    mlflow.log_metrics(numeric)
                mlflow.set_tag("parent_event", event.kind)

        transcript = [
            {
                "role": m.role,
                "name": m.name,
                "content": m.content,
                "tool_calls": [
                    {"id": c.id, "name": c.name, "arguments": c.arguments}
                    for c in m.tool_calls
                ],
            }
            for m in result.messages
        ]
        mlflow.log_dict(transcript, "transcript.json")
        mlflow.log_dict(
            [{"kind": e.kind, "t": e.t, "payload": e.payload} for e in result.tracer.events],
            "trace_events.json",
        )
        return parent.info.run_id


def search_experiment_table(experiment: str) -> list[dict[str, Any]]:
    """Flatten parent runs for a comparison table (ignores nested tool runs)."""
    rows = mlflow.search_runs(
        experiment_names=[experiment],
        order_by=["start_time ASC"],
    )
    if rows is None or rows.empty:
        return []
    parent_col = "tags.mlflow.parentRunId"
    if parent_col in rows.columns:
        nested = rows[parent_col].fillna("")
        rows = rows[nested == ""]
    records = []
    for rec in rows.to_dict(orient="records"):
        records.append(
            {
                "run_name": rec.get("tags.mlflow.runName"),
                "stop_reason": rec.get("tags.stop_reason"),
                "steps": rec.get("metrics.steps"),
                "tool_ok": rec.get("metrics.tool_ok"),
                "policy_block": rec.get("metrics.policy_block"),
                "success": rec.get("metrics.success"),
                "task_correct": rec.get("metrics.task_correct"),
                "run_id": rec.get("run_id"),
            }
        )
    return records


def _param_value(value: Any) -> str:
    if isinstance(value, (str, int, float, bool)):
        return value  # type: ignore[return-value]
    return json.dumps(value, default=str)
