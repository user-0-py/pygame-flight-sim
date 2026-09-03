from __future__ import annotations

from pathlib import Path

from agent_harness.tools import ToolError


class ToyWorkspace:
    """Tiny read-only file store used by the notebook and tests."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def _resolve(self, rel: str) -> Path:
        path = (self.root / rel).resolve()
        if self.root not in path.parents and path != self.root:
            raise ToolError("path escapes workspace")
        return path

    def list_files(self) -> str:
        files = sorted(
            p.relative_to(self.root).as_posix()
            for p in self.root.rglob("*")
            if p.is_file()
        )
        return "\n".join(files) or "(empty)"

    def read_file(self, path: str) -> str:
        target = self._resolve(path)
        if not target.is_file():
            raise ToolError(f"no such file: {path}")
        return target.read_text(encoding="utf-8")
