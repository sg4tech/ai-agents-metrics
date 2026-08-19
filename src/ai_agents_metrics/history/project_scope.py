"""Resolve one canonical project scope from warehouse paths."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai_agents_metrics.history.project_paths import normalize_project_cwd, parent_project_cwd

if TYPE_CHECKING:
    import sqlite3


@dataclass(frozen=True)
class ProjectScope:
    """A parent checkout and all warehouse paths attributed to it."""

    project_cwd: str
    member_cwds: tuple[str, ...]


def resolve_project_scope(conn: sqlite3.Connection, cwd: object) -> ProjectScope:
    """Resolve ``cwd`` and any related worktree paths known to the warehouse."""
    normalized_cwd = normalize_project_cwd(cwd)
    project_cwd = parent_project_cwd(normalized_cwd)
    if normalized_cwd is None or project_cwd is None:
        raise ValueError("Project cwd must be a non-empty path")

    normalized_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(normalized_threads)")
    }
    member_cwds: set[str] = set()
    if "cwd" in normalized_columns:
        for (stored_cwd,) in conn.execute(
            "SELECT DISTINCT cwd FROM normalized_threads WHERE cwd IS NOT NULL"
        ):
            normalized_member = normalize_project_cwd(stored_cwd)
            if (
                normalized_member is not None
                and parent_project_cwd(normalized_member) == project_cwd
            ):
                member_cwds.add(normalized_member)
    if not member_cwds:
        member_cwds.add(normalized_cwd)
    return ProjectScope(project_cwd=project_cwd, member_cwds=tuple(sorted(member_cwds)))
