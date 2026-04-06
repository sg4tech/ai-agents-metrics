# Decision Log

Key architectural and design decisions — why things are the way they are.

Format: decision title, context, reasoning, known trade-offs. Add new entries as decisions are made or recalled.

---

## JSON as the primary store, not SQLite

**Context:** the tool tracks metrics for AI agent tasks. The data needs to be stored persistently.

**Decision:** `metrics/codex_metrics.json` is the source of truth. SQLite is used only as an intermediate cache for the history pipeline.

**Reasoning:**
- Human-readable and git-diffable — changes are visible in pull requests
- Trivially portable — no tooling required to inspect or back up
- Simple to load entirely into memory; the dataset is small (hundreds of goals)

**Trade-offs:** not suitable if the dataset grows to tens of thousands of records or requires concurrent multi-writer access.

---

## fcntl for cross-process locking, not threading.Lock

**Context:** multiple CLI invocations may run concurrently against the same `codex_metrics.json`.

**Decision:** `storage.metrics_mutation_lock` uses `fcntl.flock`.

**Reasoning:** the tool runs as short-lived CLI processes, not a long-lived server. Concurrent access comes from multiple processes, not threads within one process. `fcntl.flock` works across processes; `threading.Lock` does not.

**Trade-offs:** fcntl is POSIX-only (no Windows support). Acceptable because the tool targets macOS/Linux developer environments.

---

## OS-level immutability flags on the metrics file

**Context:** `codex_metrics.json` is the source of truth. Accidental overwrites or edits by tools (editors, scripts) would corrupt data silently.

**Decision:** `save_metrics` sets `chflags uchg` (macOS) on the file after every write. The flag is lifted only during the write operation via `metrics_file_immutability_guard`.

**Reasoning:** creates a hard barrier against accidental mutation by any process other than the CLI itself. Catches mistakes early (permission error) rather than silently corrupting data.

**Trade-offs:** complicates tests (requires `unlock_tmp_path_immutability` fixture in conftest.py). Never remove the flag manually to unblock a failing command — diagnose the root cause instead.

---

## History pipeline as a separate SQLite warehouse

**Context:** Codex agent stores session history in `~/.codex/state_5.sqlite` and `~/.codex/logs_1.sqlite`. The tool needs to derive goal history from this raw data.

**Decision:** a three-stage pipeline (ingest → normalize → derive) with an intermediate SQLite warehouse at `.codex-metrics/codex_raw_history.sqlite`, separate from the primary JSON store.

**Reasoning:**
- Raw source data is large and noisy; normalisation and derivation are expensive
- The warehouse acts as a cache — the pipeline can be re-run without re-reading the source
- Each stage has a single responsibility and can be tested independently
- Derived results can be compared against `codex_metrics.json` without mutating it

**Trade-offs:** inter-stage contracts exist only as SQLite column names, not Python types (tracked in ARCH-006).

---

## Timestamps stored as ISO strings in dataclasses

**Context:** `GoalRecord` and `AttemptEntryRecord` have `started_at` and `finished_at` fields.

**Decision:** stored as `str | None`, not `datetime | None`.

**Reasoning:** initial implementation chose the simplest representation that serialises directly to JSON without a custom encoder.

**Known downside:** parsing is scattered across the codebase; two parse functions exist (`parse_iso_datetime` and `parse_iso_datetime_flexible`) because input format is not normalised at the boundary. This is a known weakness tracked in ARCH-003.

---

## cli.py as a re-export facade

**Context:** early in the project, external scripts and tests imported symbols directly from `cli.py` before the module structure was stable.

**Decision:** `cli.py` re-exports ~50 symbols from `domain`, `reporting`, and `storage` to maintain backward compatibility.

**Known downside:** any code importing from `cli` pulls the entire CLI layer as a dependency. Adding a new domain function requires updating the re-export list. This is a known weakness tracked in ARCH-001.
