from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from ai_agents_metrics.history_normalize import (
    NormalizedLogRow,
    NormalizedMessageRow,
    NormalizedSessionRow,
    NormalizedThreadRow,
    NormalizedUsageEventRow,
)


@dataclass(frozen=True)
class DeriveSummary:
    warehouse_path: Path
    projects: int
    goals: int
    attempts: int
    timeline_events: int
    retry_chains: int
    message_facts: int
    session_usage: int


def _normalize_timestamp(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _message_date_from_timestamp(value: str | None) -> str | None:
    timestamp = _normalize_timestamp(value)
    if timestamp is None:
        return None
    if len(timestamp) < 10:
        return None
    return timestamp[:10]


def _normalize_project_cwd(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _parent_project_cwd(value: Any) -> str | None:
    """Return the parent project cwd, collapsing Claude Code worktree paths into their root.

    Worktrees created by Claude Code live under ``<project>/.claude/worktrees/<name>``.
    Any thread whose cwd matches that pattern is attributed to ``<project>`` instead,
    so worktree activity is merged into the parent project when aggregating stats.
    """
    raw = _normalize_project_cwd(value)
    if raw is None:
        return None
    marker = "/.claude/worktrees/"
    idx = raw.find(marker)
    if idx == -1:
        return raw
    parent = raw[:idx]
    return parent if parent else raw


def _pick_earliest_timestamp(current: str | None, candidate: str | None) -> str | None:
    current_value = _normalize_timestamp(current)
    candidate_value = _normalize_timestamp(candidate)
    if current_value is None:
        return candidate_value
    if candidate_value is None:
        return current_value
    return candidate_value if candidate_value < current_value else current_value


def _pick_latest_timestamp(current: str | None, candidate: str | None) -> str | None:
    current_value = _normalize_timestamp(current)
    candidate_value = _normalize_timestamp(candidate)
    if current_value is None:
        return candidate_value
    if candidate_value is None:
        return current_value
    return candidate_value if candidate_value > current_value else current_value


def _compact_text(value: str | None, *, limit: int = 120) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 1]}…"


def _timeline_sort_key(item: dict[str, Any]) -> tuple[int, str, int, str, str, int, str]:
    timestamp = _normalize_timestamp(item.get("timestamp"))
    return (
        1 if timestamp is None else 0,
        timestamp or "",
        int(item.get("event_rank") or 0),
        str(item.get("thread_id") or ""),
        str(item.get("session_path") or ""),
        int(item.get("event_order") or 0),
        str(item.get("event_type") or ""),
    )


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS derived_goals (
            thread_id TEXT PRIMARY KEY,
            source_path TEXT NOT NULL,
            cwd TEXT,
            model_provider TEXT,
            model TEXT,
            title TEXT,
            archived INTEGER,
            session_count INTEGER NOT NULL,
            attempt_count INTEGER NOT NULL,
            retry_count INTEGER NOT NULL,
            message_count INTEGER NOT NULL,
            usage_event_count INTEGER NOT NULL,
            log_count INTEGER NOT NULL,
            timeline_event_count INTEGER NOT NULL,
            first_seen_at TEXT,
            last_seen_at TEXT,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS derived_attempts (
            attempt_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            source_path TEXT NOT NULL,
            session_path TEXT NOT NULL,
            attempt_index INTEGER NOT NULL,
            session_timestamp TEXT,
            cwd TEXT,
            source TEXT,
            model_provider TEXT,
            cli_version TEXT,
            originator TEXT,
            event_count INTEGER NOT NULL,
            message_count INTEGER NOT NULL,
            usage_event_count INTEGER NOT NULL,
            first_event_at TEXT,
            last_event_at TEXT,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS derived_timeline_events (
            timeline_event_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            source_path TEXT NOT NULL,
            session_path TEXT,
            attempt_index INTEGER,
            event_type TEXT NOT NULL,
            event_rank INTEGER NOT NULL,
            event_order INTEGER NOT NULL,
            timestamp TEXT,
            summary TEXT,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS derived_message_facts (
            message_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            source_path TEXT NOT NULL,
            session_path TEXT NOT NULL,
            attempt_index INTEGER,
            event_index INTEGER NOT NULL,
            message_index INTEGER NOT NULL,
            role TEXT NOT NULL,
            message_timestamp TEXT,
            message_date TEXT,
            text TEXT NOT NULL,
            model TEXT,
            usage_event_id TEXT,
            usage_event_index INTEGER,
            usage_timestamp TEXT,
            input_tokens INTEGER,
            cached_input_tokens INTEGER,
            output_tokens INTEGER,
            reasoning_output_tokens INTEGER,
            total_tokens INTEGER,
            raw_json TEXT NOT NULL
        )
        """
    )
    existing_message_fact_columns = {row[1] for row in conn.execute("PRAGMA table_info(derived_message_facts)").fetchall()}
    if "model" not in existing_message_fact_columns:
        conn.execute("ALTER TABLE derived_message_facts ADD COLUMN model TEXT")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS derived_retry_chains (
            thread_id TEXT PRIMARY KEY,
            source_path TEXT NOT NULL,
            attempt_count INTEGER NOT NULL,
            retry_count INTEGER NOT NULL,
            has_retry_pressure INTEGER NOT NULL,
            first_attempt_session_path TEXT,
            last_attempt_session_path TEXT,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS derived_session_usage (
            session_usage_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            source_path TEXT NOT NULL,
            session_path TEXT NOT NULL,
            attempt_index INTEGER NOT NULL,
            usage_event_count INTEGER NOT NULL,
            input_tokens INTEGER,
            cache_creation_input_tokens INTEGER,
            cached_input_tokens INTEGER,
            output_tokens INTEGER,
            reasoning_output_tokens INTEGER,
            total_tokens INTEGER,
            first_usage_at TEXT,
            last_usage_at TEXT,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS derived_projects (
            project_cwd TEXT PRIMARY KEY,
            parent_project_cwd TEXT,
            thread_count INTEGER NOT NULL,
            attempt_count INTEGER NOT NULL,
            retry_thread_count INTEGER NOT NULL,
            message_count INTEGER NOT NULL,
            usage_event_count INTEGER NOT NULL,
            log_count INTEGER NOT NULL,
            timeline_event_count INTEGER NOT NULL,
            input_tokens INTEGER,
            cache_creation_input_tokens INTEGER,
            cached_input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            first_seen_at TEXT,
            last_seen_at TEXT,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_goals_cwd ON derived_goals(cwd)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_attempts_thread_id ON derived_attempts(thread_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_timeline_thread_id ON derived_timeline_events(thread_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_message_facts_thread_id ON derived_message_facts(thread_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_message_facts_session_path ON derived_message_facts(session_path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_message_facts_message_date ON derived_message_facts(message_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_message_facts_model ON derived_message_facts(model)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_retry_chains_thread_id ON derived_retry_chains(thread_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_session_usage_thread_id ON derived_session_usage(thread_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_derived_projects_cwd ON derived_projects(project_cwd)")
    for table in ("derived_session_usage", "derived_projects"):
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if "cache_creation_input_tokens" not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN cache_creation_input_tokens INTEGER")
    existing_projects = {row[1] for row in conn.execute("PRAGMA table_info(derived_projects)").fetchall()}
    if "parent_project_cwd" not in existing_projects:
        conn.execute("ALTER TABLE derived_projects ADD COLUMN parent_project_cwd TEXT")


def _clear_derived_tables(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM derived_goals")
    conn.execute("DELETE FROM derived_attempts")
    conn.execute("DELETE FROM derived_timeline_events")
    conn.execute("DELETE FROM derived_message_facts")
    conn.execute("DELETE FROM derived_retry_chains")
    conn.execute("DELETE FROM derived_session_usage")
    conn.execute("DELETE FROM derived_projects")


def _fetch_normalized_threads(conn: sqlite3.Connection) -> list[NormalizedThreadRow]:
    rows = conn.execute(
        """
        SELECT thread_id, source_path, cwd, model_provider, model, title, archived,
               session_count, event_count, message_count, log_count,
               first_seen_at, last_seen_at, raw_json
        FROM normalized_threads
        ORDER BY thread_id
        """
    ).fetchall()
    return [cast(NormalizedThreadRow, dict(row)) for row in rows]


def _fetch_normalized_sessions(conn: sqlite3.Connection) -> list[NormalizedSessionRow]:
    rows = conn.execute(
        """
        SELECT session_path, thread_id, source_path, session_timestamp, cwd, source,
               model_provider, cli_version, originator, event_count, message_count,
               first_event_at, last_event_at, raw_json
        FROM normalized_sessions
        ORDER BY thread_id, session_timestamp, session_path
        """
    ).fetchall()
    return [cast(NormalizedSessionRow, dict(row)) for row in rows]


def _fetch_normalized_messages(conn: sqlite3.Connection) -> list[NormalizedMessageRow]:
    rows = conn.execute(
        """
        SELECT message_id, thread_id, session_path, source_path, event_index, message_index,
               role, text, timestamp, raw_json
        FROM normalized_messages
        ORDER BY thread_id, session_path, event_index, message_index
        """
    ).fetchall()
    return [cast(NormalizedMessageRow, dict(row)) for row in rows]


def _fetch_normalized_usage_events(conn: sqlite3.Connection) -> list[NormalizedUsageEventRow]:
    rows = conn.execute(
        """
        SELECT usage_event_id, thread_id, session_path, source_path, event_index, timestamp,
               input_tokens, cache_creation_input_tokens, cached_input_tokens,
               output_tokens, reasoning_output_tokens, total_tokens, model, raw_json
        FROM normalized_usage_events
        ORDER BY thread_id, session_path, event_index, usage_event_id
        """
    ).fetchall()
    return [cast(NormalizedUsageEventRow, dict(row)) for row in rows]


def _fetch_normalized_logs(conn: sqlite3.Connection) -> list[NormalizedLogRow]:
    rows = conn.execute(
        """
        SELECT source_path, row_id, thread_id, ts, ts_iso, level, target, body, raw_json
        FROM normalized_logs
        ORDER BY thread_id, ts, row_id
        """
    ).fetchall()
    return [cast(NormalizedLogRow, dict(row)) for row in rows]


def _sum_known_int(values: list[int | None]) -> int | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return sum(filtered)


def _derived_attempt_id(thread_id: str, session_path: str) -> str:
    return hashlib.sha256(f"{thread_id}:{session_path}".encode("utf-8")).hexdigest()


def _session_usage_id(session_path: str) -> str:
    return hashlib.sha256(session_path.encode("utf-8")).hexdigest()


def _resolve_assistant_message_event_index(
    usage_event_index: int,
    assistant_event_indices: list[int],
) -> int | None:
    if usage_event_index in assistant_event_indices:
        return usage_event_index
    for event_index in assistant_event_indices:
        if event_index > usage_event_index:
            return event_index
    for event_index in reversed(assistant_event_indices):
        if event_index < usage_event_index:
            return event_index
    return None


def _resolve_message_model(usage_event: NormalizedUsageEventRow | None, thread_model: str | None) -> str | None:
    if usage_event is not None:
        usage_model = usage_event["model"]
        if isinstance(usage_model, str):
            cleaned = usage_model.strip()
            if cleaned:
                return cleaned
    if isinstance(thread_model, str):
        cleaned = thread_model.strip()
        if cleaned:
            return cleaned
    return None


def _timeline_event_id(thread_id: str, event_type: str, event_order: int, session_path: str | None, timestamp: str | None) -> str:
    seed = f"{thread_id}:{event_type}:{event_order}:{session_path or ''}:{timestamp or ''}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _build_index_maps(
    normalized_sessions: list[NormalizedSessionRow],
    normalized_messages: list[NormalizedMessageRow],
    normalized_usage_events: list[NormalizedUsageEventRow],
    normalized_logs: list[NormalizedLogRow],
) -> tuple[
    dict[str, list[NormalizedSessionRow]],
    dict[str, list[NormalizedMessageRow]],
    dict[str, list[NormalizedMessageRow]],
    dict[str, list[NormalizedUsageEventRow]],
    dict[str, list[NormalizedUsageEventRow]],
    dict[str, list[NormalizedLogRow]],
]:
    sessions_by_thread: dict[str, list[NormalizedSessionRow]] = {}
    messages_by_session: dict[str, list[NormalizedMessageRow]] = {}
    messages_by_thread: dict[str, list[NormalizedMessageRow]] = {}
    usage_events_by_session: dict[str, list[NormalizedUsageEventRow]] = {}
    usage_events_by_thread: dict[str, list[NormalizedUsageEventRow]] = {}
    logs_by_thread: dict[str, list[NormalizedLogRow]] = {}

    for session_row in normalized_sessions:
        if (tid := session_row["thread_id"]) is not None:
            sessions_by_thread.setdefault(tid, []).append(session_row)

    for message_row in normalized_messages:
        messages_by_session.setdefault(message_row["session_path"], []).append(message_row)
        if (tid := message_row["thread_id"]) is not None:
            messages_by_thread.setdefault(tid, []).append(message_row)

    for usage_row in normalized_usage_events:
        usage_events_by_session.setdefault(usage_row["session_path"], []).append(usage_row)
        if (tid := usage_row["thread_id"]) is not None:
            usage_events_by_thread.setdefault(tid, []).append(usage_row)

    for log_row in normalized_logs:
        if (tid := log_row["thread_id"]) is not None:
            logs_by_thread.setdefault(tid, []).append(log_row)

    return (
        sessions_by_thread,
        messages_by_session,
        messages_by_thread,
        usage_events_by_session,
        usage_events_by_thread,
        logs_by_thread,
    )


def _build_message_usage_groups(
    messages_by_session: dict[str, list[NormalizedMessageRow]],
    usage_events_by_session: dict[str, list[NormalizedUsageEventRow]],
) -> dict[str, dict[int, list[NormalizedUsageEventRow]]]:
    message_usage_groups: dict[str, dict[int, list[NormalizedUsageEventRow]]] = {}
    for session_path, session_messages in messages_by_session.items():
        assistant_event_indices = sorted(
            {int(row["event_index"]) for row in session_messages if row["role"] == "assistant"}
        )
        if not assistant_event_indices:
            continue
        usage_groups: dict[int, list[NormalizedUsageEventRow]] = {}
        for usage_row in usage_events_by_session.get(session_path, []):
            target = _resolve_assistant_message_event_index(
                int(usage_row["event_index"]), assistant_event_indices
            )
            if target is not None:
                usage_groups.setdefault(target, []).append(usage_row)
        if usage_groups:
            message_usage_groups[session_path] = usage_groups
    return message_usage_groups


def _build_timeline_items(
    thread_id: str,
    thread_sessions: list[NormalizedSessionRow],
    thread_messages: list[NormalizedMessageRow],
    thread_usage_events: list[NormalizedUsageEventRow],
    thread_logs: list[NormalizedLogRow],
) -> list[dict[str, Any]]:
    session_index_map = {row["session_path"]: idx for idx, row in enumerate(thread_sessions, start=1)}
    items: list[dict[str, Any]] = []

    for session_index, session_row in enumerate(thread_sessions, start=1):
        items.append({
            "thread_id": thread_id,
            "source_path": session_row["source_path"],
            "session_path": session_row["session_path"],
            "attempt_index": session_index,
            "event_type": "session_start",
            "event_rank": 0,
            "event_order": session_index,
            "timestamp": _normalize_timestamp(session_row["session_timestamp"]),
            "summary": _compact_text(
                f"session start {session_row['session_path']} {session_row['originator'] or ''}".strip()
            ),
            "raw_json": session_row["raw_json"],
        })

    for message_row in thread_messages:
        items.append({
            "thread_id": thread_id,
            "source_path": message_row["source_path"],
            "session_path": message_row["session_path"],
            "attempt_index": session_index_map.get(message_row["session_path"]),
            "event_type": "message",
            "event_rank": 1,
            "event_order": int(message_row["event_index"]),
            "timestamp": _normalize_timestamp(message_row["timestamp"]),
            "summary": _compact_text(f"{message_row['role']}: {message_row['text']}"),
            "raw_json": message_row["raw_json"],
        })

    for usage_row in thread_usage_events:
        items.append({
            "thread_id": thread_id,
            "source_path": usage_row["source_path"],
            "session_path": usage_row["session_path"],
            "attempt_index": session_index_map.get(usage_row["session_path"]),
            "event_type": "usage_event",
            "event_rank": 2,
            "event_order": int(usage_row["event_index"]),
            "timestamp": _normalize_timestamp(usage_row["timestamp"]),
            "summary": _compact_text(
                f"usage tokens={usage_row['total_tokens']} model={usage_row['model'] or ''}".strip()
            ),
            "raw_json": usage_row["raw_json"],
        })

    for log_row in thread_logs:
        items.append({
            "thread_id": thread_id,
            "source_path": log_row["source_path"],
            "session_path": None,
            "attempt_index": None,
            "event_type": "log",
            "event_rank": 3,
            "event_order": int(log_row["row_id"]),
            "timestamp": _normalize_timestamp(log_row["ts_iso"]),
            "summary": _compact_text(log_row["body"] or log_row["target"]),
            "raw_json": log_row["raw_json"],
        })

    items.sort(key=_timeline_sort_key)
    return items


def _insert_timeline_events(
    conn: sqlite3.Connection,
    thread_id: str,
    timeline_items: list[dict[str, Any]],
) -> int:
    count = 0
    for event_order, item in enumerate(timeline_items, start=1):
        event_id = _timeline_event_id(
            thread_id,
            str(item["event_type"]),
            event_order,
            item.get("session_path"),
            item.get("timestamp"),
        )
        conn.execute(
            """
            INSERT INTO derived_timeline_events (
                timeline_event_id, thread_id, source_path, session_path, attempt_index,
                event_type, event_rank, event_order, timestamp, summary, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                thread_id,
                item["source_path"],
                item.get("session_path"),
                item.get("attempt_index"),
                item["event_type"],
                item["event_rank"],
                event_order,
                item.get("timestamp"),
                item.get("summary"),
                item["raw_json"],
            ),
        )
        count += 1
    return count


def _insert_message_facts(
    conn: sqlite3.Connection,
    thread_id: str,
    thread_row: NormalizedThreadRow,
    thread_messages: list[NormalizedMessageRow],
    thread_sessions: list[NormalizedSessionRow],
    message_usage_groups: dict[str, dict[int, list[NormalizedUsageEventRow]]],
) -> int:
    session_index_map = {row["session_path"]: idx for idx, row in enumerate(thread_sessions, start=1)}
    messages_by_session: dict[str, list[NormalizedMessageRow]] = {}
    for row in thread_messages:
        messages_by_session.setdefault(row["session_path"], []).append(row)

    count = 0
    for session_path, session_messages in messages_by_session.items():
        usage_groups = message_usage_groups.get(session_path, {})
        attempt_index = session_index_map.get(session_path)
        for message_row in session_messages:
            usage_rows = usage_groups.get(int(message_row["event_index"]), [])
            usage_event = usage_rows[0] if usage_rows else None
            message_timestamp = _normalize_timestamp(message_row["timestamp"])
            conn.execute(
                """
                INSERT INTO derived_message_facts (
                    message_id, thread_id, source_path, session_path, attempt_index,
                    event_index, message_index, role, message_timestamp, message_date,
                    text, model, usage_event_id, usage_event_index, usage_timestamp,
                    input_tokens, cached_input_tokens, output_tokens,
                    reasoning_output_tokens, total_tokens, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_row["message_id"],
                    thread_id,
                    message_row["source_path"],
                    session_path,
                    attempt_index,
                    message_row["event_index"],
                    message_row["message_index"],
                    message_row["role"],
                    message_timestamp,
                    _message_date_from_timestamp(message_timestamp),
                    message_row["text"],
                    _resolve_message_model(usage_event, thread_row["model"]),
                    None if usage_event is None else usage_event["usage_event_id"],
                    None if usage_event is None else int(usage_event["event_index"]),
                    None if usage_event is None else _normalize_timestamp(usage_event["timestamp"]),
                    _sum_known_int([row["input_tokens"] for row in usage_rows]),
                    _sum_known_int([row["cached_input_tokens"] for row in usage_rows]),
                    _sum_known_int([row["output_tokens"] for row in usage_rows]),
                    _sum_known_int([row["reasoning_output_tokens"] for row in usage_rows]),
                    _sum_known_int([row["total_tokens"] for row in usage_rows]),
                    message_row["raw_json"],
                ),
            )
            count += 1
    return count


def _insert_attempts_and_session_usage(
    conn: sqlite3.Connection,
    thread_id: str,
    sorted_sessions: list[NormalizedSessionRow],
    usage_events_by_session: dict[str, list[NormalizedUsageEventRow]],
    stats_entry: dict[str, Any] | None,
) -> int:
    count = 0
    for attempt_index, session_row in enumerate(sorted_sessions, start=1):
        session_path = session_row["session_path"]
        usage_rows = usage_events_by_session.get(session_path, [])
        usage_input = _sum_known_int([r["input_tokens"] for r in usage_rows])
        usage_cache_create = _sum_known_int([r["cache_creation_input_tokens"] for r in usage_rows])
        usage_cached = _sum_known_int([r["cached_input_tokens"] for r in usage_rows])
        usage_output = _sum_known_int([r["output_tokens"] for r in usage_rows])
        usage_reasoning = _sum_known_int([r["reasoning_output_tokens"] for r in usage_rows])
        usage_total = _sum_known_int([r["total_tokens"] for r in usage_rows])

        if stats_entry is not None:
            stats_entry["input_tokens"] += usage_input or 0
            stats_entry["cache_creation_input_tokens"] += usage_cache_create or 0
            stats_entry["cached_input_tokens"] += usage_cached or 0
            stats_entry["output_tokens"] += usage_output or 0
            stats_entry["total_tokens"] += usage_total or 0

        conn.execute(
            """
            INSERT INTO derived_attempts (
                attempt_id, thread_id, source_path, session_path, attempt_index,
                session_timestamp, cwd, source, model_provider, cli_version, originator,
                event_count, message_count, usage_event_count, first_event_at, last_event_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _derived_attempt_id(thread_id, session_path),
                thread_id,
                session_row["source_path"],
                session_path,
                attempt_index,
                _normalize_timestamp(session_row["session_timestamp"]),
                session_row["cwd"],
                session_row["source"],
                session_row["model_provider"],
                session_row["cli_version"],
                session_row["originator"],
                session_row["event_count"],
                session_row["message_count"],
                len(usage_rows),
                _normalize_timestamp(session_row["first_event_at"]),
                _normalize_timestamp(session_row["last_event_at"]),
                session_row["raw_json"],
            ),
        )
        conn.execute(
            """
            INSERT INTO derived_session_usage (
                session_usage_id, thread_id, source_path, session_path, attempt_index,
                usage_event_count, input_tokens, cache_creation_input_tokens,
                cached_input_tokens, output_tokens, reasoning_output_tokens,
                total_tokens, first_usage_at, last_usage_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _session_usage_id(session_path),
                thread_id,
                session_row["source_path"],
                session_path,
                attempt_index,
                len(usage_rows),
                usage_input,
                usage_cache_create,
                usage_cached,
                usage_output,
                usage_reasoning,
                usage_total,
                min((ts for r in usage_rows if (ts := _normalize_timestamp(r["timestamp"])) is not None), default=None),
                max((ts for r in usage_rows if (ts := _normalize_timestamp(r["timestamp"])) is not None), default=None),
                json.dumps(
                    {
                        "thread_id": thread_id,
                        "session_path": session_path,
                        "attempt_index": attempt_index,
                        "usage_event_count": len(usage_rows),
                        "input_tokens": usage_input,
                        "cache_creation_input_tokens": usage_cache_create,
                        "cached_input_tokens": usage_cached,
                        "output_tokens": usage_output,
                        "reasoning_output_tokens": usage_reasoning,
                        "total_tokens": usage_total,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
        )
        count += 1
    return count


def _insert_goal_and_retry_chain(
    conn: sqlite3.Connection,
    thread_id: str,
    thread_row: NormalizedThreadRow,
    sorted_sessions: list[NormalizedSessionRow],
    thread_usage_events: list[NormalizedUsageEventRow],
    timeline_items: list[dict[str, Any]],
) -> None:
    attempt_count = len(sorted_sessions)
    retry_count = max(attempt_count - 1, 0)
    conn.execute(
        """
        INSERT INTO derived_goals (
            thread_id, source_path, cwd, model_provider, model, title, archived,
            session_count, attempt_count, retry_count, message_count,
            usage_event_count, log_count, timeline_event_count, first_seen_at,
            last_seen_at, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            thread_id,
            thread_row["source_path"],
            thread_row["cwd"],
            thread_row["model_provider"],
            thread_row["model"],
            thread_row["title"],
            thread_row["archived"],
            thread_row["session_count"],
            attempt_count,
            retry_count,
            thread_row["message_count"],
            len(thread_usage_events),
            thread_row["log_count"],
            len(timeline_items),
            _normalize_timestamp(thread_row["first_seen_at"]),
            _normalize_timestamp(thread_row["last_seen_at"]),
            thread_row["raw_json"],
        ),
    )
    conn.execute(
        """
        INSERT INTO derived_retry_chains (
            thread_id, source_path, attempt_count, retry_count, has_retry_pressure,
            first_attempt_session_path, last_attempt_session_path, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            thread_id,
            thread_row["source_path"],
            attempt_count,
            retry_count,
            1 if attempt_count > 1 else 0,
            None if not sorted_sessions else sorted_sessions[0]["session_path"],
            None if not sorted_sessions else sorted_sessions[-1]["session_path"],
            json.dumps(
                {
                    "thread_id": thread_id,
                    "attempt_count": attempt_count,
                    "retry_count": retry_count,
                    "has_retry_pressure": attempt_count > 1,
                    "session_paths": [row["session_path"] for row in sorted_sessions],
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        ),
    )


def _insert_projects(conn: sqlite3.Connection, project_stats: dict[str, dict[str, Any]]) -> int:
    count = 0
    for project_cwd, stats in project_stats.items():
        # project_cwd is already the collapsed parent path (worktree suffix stripped by
        # _parent_project_cwd at aggregation time), so parent_project_cwd == project_cwd for
        # every row.  The column exists so that read_history_signals and history_compare_store
        # can query by parent_project_cwd without needing a LIKE workaround on derived_projects.
        conn.execute(
            """
            INSERT INTO derived_projects (
                project_cwd, parent_project_cwd, thread_count, attempt_count, retry_thread_count,
                message_count, usage_event_count, log_count, timeline_event_count, input_tokens,
                cache_creation_input_tokens, cached_input_tokens, output_tokens,
                total_tokens, first_seen_at, last_seen_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_cwd,
                project_cwd,
                stats["thread_count"],
                stats["attempt_count"],
                stats["retry_thread_count"],
                stats["message_count"],
                stats["usage_event_count"],
                stats["log_count"],
                stats["timeline_event_count"],
                stats["input_tokens"] or None,
                stats["cache_creation_input_tokens"] or None,
                stats["cached_input_tokens"] or None,
                stats["output_tokens"] or None,
                stats["total_tokens"] or None,
                stats["first_seen_at"],
                stats["last_seen_at"],
                json.dumps(
                    {
                        "project_cwd": project_cwd,
                        "parent_project_cwd": project_cwd,
                        "thread_count": stats["thread_count"],
                        "attempt_count": stats["attempt_count"],
                        "retry_thread_count": stats["retry_thread_count"],
                        "message_count": stats["message_count"],
                        "usage_event_count": stats["usage_event_count"],
                        "log_count": stats["log_count"],
                        "timeline_event_count": stats["timeline_event_count"],
                        "input_tokens": stats["input_tokens"],
                        "cache_creation_input_tokens": stats["cache_creation_input_tokens"],
                        "cached_input_tokens": stats["cached_input_tokens"],
                        "output_tokens": stats["output_tokens"],
                        "total_tokens": stats["total_tokens"],
                        "first_seen_at": stats["first_seen_at"],
                        "last_seen_at": stats["last_seen_at"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
        )
        count += 1
    return count


def derive_codex_history(*, warehouse_path: Path) -> DeriveSummary:
    if not warehouse_path.exists():
        raise ValueError(
            f"Warehouse does not exist: {warehouse_path}. "
            "Run 'ai-agents-metrics history-update' first."
        )

    goals = 0
    attempts = 0
    timeline_events = 0
    retry_chains = 0
    message_facts = 0
    session_usage = 0

    with sqlite3.connect(warehouse_path) as conn:
        conn.row_factory = sqlite3.Row
        _ensure_schema(conn)
        try:
            normalized_threads = _fetch_normalized_threads(conn)
            normalized_sessions = _fetch_normalized_sessions(conn)
            normalized_messages = _fetch_normalized_messages(conn)
            normalized_usage_events = _fetch_normalized_usage_events(conn)
            normalized_logs = _fetch_normalized_logs(conn)
        except sqlite3.OperationalError as exc:
            raise ValueError(
                "Warehouse does not contain normalized Codex history; run history-normalize first"
            ) from exc
        except IndexError as exc:
            raise ValueError(
                "Warehouse schema is incompatible with this version of codex-metrics; "
                "run history-normalize first"
            ) from exc

        (
            sessions_by_thread,
            messages_by_session,
            messages_by_thread,
            usage_events_by_session,
            usage_events_by_thread,
            logs_by_thread,
        ) = _build_index_maps(normalized_sessions, normalized_messages, normalized_usage_events, normalized_logs)

        _clear_derived_tables(conn)
        message_usage_groups = _build_message_usage_groups(messages_by_session, usage_events_by_session)

        project_stats: dict[str, dict[str, Any]] = {}

        def get_project_stats(cwd: str) -> dict[str, Any]:
            if cwd not in project_stats:
                project_stats[cwd] = {
                    "thread_count": 0, "attempt_count": 0, "retry_thread_count": 0,
                    "message_count": 0, "usage_event_count": 0, "log_count": 0,
                    "timeline_event_count": 0, "input_tokens": 0,
                    "cache_creation_input_tokens": 0, "cached_input_tokens": 0,
                    "output_tokens": 0, "total_tokens": 0,
                    "first_seen_at": None, "last_seen_at": None,
                }
            return project_stats[cwd]

        for thread_row in normalized_threads:
            thread_id = thread_row["thread_id"]
            project_cwd = _parent_project_cwd(thread_row["cwd"])
            thread_sessions = sessions_by_thread.get(thread_id, [])
            thread_messages = messages_by_thread.get(thread_id, [])
            thread_usage_events = usage_events_by_thread.get(thread_id, [])
            thread_logs = logs_by_thread.get(thread_id, [])

            if project_cwd is not None:
                stats = get_project_stats(project_cwd)
                stats["thread_count"] += 1
                stats["attempt_count"] += int(thread_row["session_count"] or 0)
                stats["retry_thread_count"] += 1 if int(thread_row["session_count"] or 0) > 1 else 0
                stats["message_count"] += int(thread_row["message_count"] or 0)
                stats["log_count"] += int(thread_row["log_count"] or 0)
                stats["usage_event_count"] += len(thread_usage_events)
                stats["first_seen_at"] = _pick_earliest_timestamp(stats["first_seen_at"], thread_row["first_seen_at"])
                stats["last_seen_at"] = _pick_latest_timestamp(stats["last_seen_at"], thread_row["last_seen_at"])

            timeline_items = _build_timeline_items(
                thread_id, thread_sessions, thread_messages, thread_usage_events, thread_logs
            )

            if project_cwd is not None:
                get_project_stats(project_cwd)["timeline_event_count"] += len(timeline_items)

            timeline_events += _insert_timeline_events(conn, thread_id, timeline_items)
            message_facts += _insert_message_facts(
                conn, thread_id, thread_row, thread_messages, thread_sessions, message_usage_groups
            )

            sorted_sessions = sorted(
                thread_sessions,
                key=lambda row: (
                    1 if _normalize_timestamp(row["session_timestamp"]) is None else 0,
                    _normalize_timestamp(row["session_timestamp"]) or "",
                    row["session_path"],
                ),
            )
            session_usage += _insert_attempts_and_session_usage(
                conn,
                thread_id,
                sorted_sessions,
                usage_events_by_session,
                get_project_stats(project_cwd) if project_cwd is not None else None,
            )
            _insert_goal_and_retry_chain(
                conn, thread_id, thread_row, sorted_sessions, thread_usage_events, timeline_items
            )
            goals += 1
            attempts += len(sorted_sessions)
            retry_chains += 1

        projects = _insert_projects(conn, project_stats)
        conn.commit()

    return DeriveSummary(
        warehouse_path=warehouse_path,
        projects=projects,
        goals=goals,
        attempts=attempts,
        timeline_events=timeline_events,
        retry_chains=retry_chains,
        message_facts=message_facts,
        session_usage=session_usage,
    )


def render_derive_summary_json(summary: DeriveSummary) -> str:
    return json.dumps({
        "warehouse_path": str(summary.warehouse_path),
        "projects": summary.projects,
        "goals": summary.goals,
        "attempts": summary.attempts,
        "timeline_events": summary.timeline_events,
        "retry_chains": summary.retry_chains,
        "message_facts": summary.message_facts,
        "session_usage": summary.session_usage,
    })
