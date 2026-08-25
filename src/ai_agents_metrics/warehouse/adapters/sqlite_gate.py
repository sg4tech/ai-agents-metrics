"""SQLite adapter for the shared warehouse readiness gate."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Final

from ai_agents_metrics.history.project_paths import parent_project_cwd
from ai_agents_metrics.warehouse.application import (
    WarehouseScope,
    WarehouseState,
    WarehouseStatus,
)

if TYPE_CHECKING:
    from pathlib import Path

REQUIRED_TABLES: Final = frozenset(
    {
        "derived_goals",
        "derived_projects",
        "derived_model_usage",
        "derived_practice_events",
    }
)
REQUIRED_PROJECT_COLUMN: Final = "parent_project_cwd"


class SQLiteWarehouseGate:
    def resolve(self, warehouse_path: Path, project_cwd: Path) -> WarehouseState:
        if not warehouse_path.is_file():
            return WarehouseState(WarehouseStatus.MISSING_FILE)
        canonical_cwd = parent_project_cwd(project_cwd)
        if canonical_cwd is None:
            return WarehouseState(WarehouseStatus.EMPTY_FOR_CWD)
        try:
            with sqlite3.connect(warehouse_path) as connection:
                if not self._has_current_schema(connection):
                    return WarehouseState(WarehouseStatus.SCHEMA_OUTDATED)
                matching_projects = self._project_count(connection, canonical_cwd)
                all_projects = self._project_count(connection)
        except (sqlite3.Error, OSError):
            return WarehouseState(WarehouseStatus.SCHEMA_OUTDATED)
        if matching_projects:
            return WarehouseState.ok(WarehouseScope(canonical_cwd, is_all_projects=False))
        if all_projects:
            return WarehouseState.ok(WarehouseScope(canonical_cwd, is_all_projects=True))
        return WarehouseState(WarehouseStatus.EMPTY_FOR_CWD)

    @staticmethod
    def _has_current_schema(connection: sqlite3.Connection) -> bool:
        tables = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if not tables >= REQUIRED_TABLES:
            return False
        project_columns = {
            str(row[1]) for row in connection.execute("PRAGMA table_info(derived_projects)")
        }
        return REQUIRED_PROJECT_COLUMN in project_columns

    @staticmethod
    def _project_count(connection: sqlite3.Connection, project_cwd: str | None = None) -> int:
        if project_cwd is None:
            row = connection.execute("SELECT COUNT(*) FROM derived_projects").fetchone()
        else:
            row = connection.execute(
                "SELECT COUNT(*) FROM derived_projects WHERE parent_project_cwd = ?",
                (project_cwd,),
            ).fetchone()
        return 0 if row is None else int(row[0])
