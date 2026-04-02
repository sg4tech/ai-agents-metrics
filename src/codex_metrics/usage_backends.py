from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class UsageWindow:
    cost_usd: float | None
    total_tokens: int | None
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    model_name: str | None
    backend_name: str


class UsageBackend(Protocol):
    name: str

    def resolve_window(
        self,
        *,
        state_path: Path,
        logs_path: Path,
        cwd: Path,
        started_at: str | None,
        finished_at: str | None,
        pricing_path: Path,
        thread_id: str | None = None,
    ) -> UsageWindow: ...


def resolve_usage_window(
    backend: UsageBackend,
    *,
    state_path: Path,
    logs_path: Path,
    cwd: Path,
    started_at: str | None,
    finished_at: str | None,
    pricing_path: Path,
    thread_id: str | None = None,
) -> UsageWindow:
    return backend.resolve_window(
        state_path=state_path,
        logs_path=logs_path,
        cwd=cwd,
        started_at=started_at,
        finished_at=finished_at,
        pricing_path=pricing_path,
        thread_id=thread_id,
    )
