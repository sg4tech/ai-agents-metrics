"""Canonical path rules for grouping agent worktrees into projects."""
from __future__ import annotations

from pathlib import Path


def normalize_project_cwd(value: object) -> str | None:
    """Return an absolute normalized project path when ``value`` is usable."""
    if not isinstance(value, (str, Path)):
        return None
    raw = str(value).strip()
    if not raw:
        return None
    return str(Path(raw).expanduser().resolve())


def parent_project_cwd(value: object) -> str | None:
    """Collapse a Claude Code worktree path into its parent checkout path."""
    normalized = normalize_project_cwd(value)
    if normalized is None:
        return None
    marker = "/.claude/worktrees/"
    marker_index = normalized.find(marker)
    if marker_index == -1:
        return normalized
    parent = normalized[:marker_index]
    return parent or normalized
