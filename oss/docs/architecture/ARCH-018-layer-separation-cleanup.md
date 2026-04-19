# ARCH-018: Honor layer separation — move interpretation out of raw_* tables

**Priority:** medium
**Complexity:** medium
**Status:** open

## Problem

The layer rules defined in `oss/docs/warehouse-layering.md` (added 2026-04-19) formalize that Layer 1 (`raw_*`) must contain only byte-perfect capture of source files, and that parsing payload into typed fields is Layer 2 (`normalized_*`) work. Several existing raw tables violate this rule:

- **`raw_messages`** — parses the source JSONL payload into typed fields (`role`, `text`, `timestamp`). This is normalization, not raw capture. A consumer cannot distinguish what Claude/Codex literally wrote from what our parser decided.
- **`raw_token_usage`** — parses payload into typed token fields (`input_tokens`, `cached_input_tokens`, etc.). Same problem.
- **`raw_session_events`** — mixes raw JSON events with light typing.
- **`raw_logs`** — partially typed. Unclear which fields are from the file and which are parser-derived.

Because interpretation leaks into Layer 1, the layer-integrity invariant "deleting raw and re-ingesting from files produces byte-identical rows" cannot currently be tested.

## Proposed solution

Introduce a single proper raw table:

```sql
CREATE TABLE raw_events (
  event_id          TEXT PRIMARY KEY,     -- stable hash(source_path + line_number)
  source_path       TEXT NOT NULL,
  line_number       INTEGER NOT NULL,
  payload           TEXT NOT NULL,        -- exact JSON line as read, unparsed
  provider          TEXT NOT NULL,        -- inferred from source_path root only
  file_sha256       TEXT NOT NULL,
  file_mtime        TEXT NOT NULL,
  ingested_at       TEXT NOT NULL,
  ingest_run_id     TEXT NOT NULL
);
```

Move all parsing out of `raw_*` and into the corresponding `normalized_*` tables. Keep the existing `normalized_messages`, `normalized_usage_events`, `normalized_logs`, `normalized_sessions`, `normalized_threads` in place — they already exist and already do the right job. The migration is about **removing duplicated parse logic from raw tables**, not adding new normalized ones.

## Migration strategy

1. Introduce `raw_events` alongside existing tables. Populate on ingest.
2. Rewire `normalized_*` stages to read from `raw_events` instead of from the typed raw tables.
3. Verify normalized output is byte-identical to the old pipeline (the golden comparison test).
4. Deprecate the typed raw tables (`raw_messages`, `raw_token_usage`, `raw_session_events`, `raw_logs`). Drop them once no code path still reads them.
5. Keep `raw_sessions` and `raw_threads` — they contain only filesystem-derived facts (path, mtime, uuid from directory) and are legal Layer 1 content. Document that they are metadata-per-file, not parsed content.

## Tests to add

- `raw_events.sha256 == sha256(read file slice)` — per-file integrity check
- Rebuilding normalized from raw produces identical rows
- No regex-import, no classifier-config-import in any raw-layer module

## Risks

- Large refactor touching every ingest module. Needs the golden comparison test in place before the rewrite starts, otherwise silent data drift is possible.
- `raw_messages` and `raw_token_usage` are referenced directly from some CLI inspection queries in `history-pipeline.md`. Those queries need to move to the normalized equivalents as part of the migration.
- A payload string column may slightly increase warehouse size (JSON kept twice during transition).

## Why this is not a blocker for new work

New classified tables (`derived_session_kinds`, `derived_message_kinds`) can be built against the existing `normalized_*` layer without waiting for this refactor. This ticket cleans up the raw-layer violation separately, at whatever pace makes sense.

## Related

- `oss/docs/warehouse-layering.md` — the rules this ticket makes the code comply with
- `oss/docs/history-pipeline.md` — current raw table catalog (some entries will be removed when this lands)
