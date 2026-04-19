# Warehouse Layering

**What this document is:** The rules that govern how data flows through the warehouse and what each layer is allowed to contain. Named layers (`raw_*`, `normalized_*`, classified `derived_*`, aggregate `derived_*`) exist to keep interpretation out of raw storage, to let each layer be rebuilt from the one below without loss, and to make classifier rules versionable without touching primary data.

**When to read this:**
- Adding a new table or column to the warehouse
- Designing a new adapter (new provider, new file format)
- Writing or reviewing an ingest/normalize/classify/derive change
- Deciding where a new interpretation rule (regex, heuristic, LLM classifier output) belongs

**Related docs:**
- [history-pipeline.md](history-pipeline.md) — current table catalog and pipeline stages
- [data-schema.md](data-schema.md) — field reference per table
- [architecture.md](architecture.md) — where each stage runs in the code

---

## The four layers

| Layer | Purpose | Built from | Can be rebuilt losslessly |
|---|---|---|---|
| 1. `raw_*` | Byte-perfect capture of source files | The filesystem | Yes — from source files |
| 2. `normalized_*` | Deterministic parsing of raw content | `raw_*` only | Yes — from `raw_*` |
| 3. Classified `derived_*` | Per-item interpretation (one row per normalized item) | `normalized_*` only | Yes — from `normalized_*` |
| 4. Aggregate `derived_*` | Rollups, cross-item relationships, goal/attempt shape | Classified + normalized | Yes — from lower layers |

Every layer can be dropped and rebuilt from the layers below it. This is a non-negotiable invariant: it is the only reason the pipeline is debuggable.

---

## Layer 1 — Raw

**Purpose:** faithfully mirror what is on disk. Downstream layers may change behavior; raw must not.

**Allowed in a raw row:**
- Content of the source file as a string or bytes (e.g. one JSON line per `raw_events` row)
- Facts derived trivially from the file path or filesystem metadata: `source_path`, `file_size`, `mtime`, `sha256`, `provider` (inferred from `~/.codex` vs `~/.claude`), and directory-level identifiers Claude and Codex put directly into the path (`thread_uuid`, `session_uuid`)
- Ingest metadata: `ingested_at`, `ingest_run_id`

**Forbidden in a raw row:**
- Parsed content of the payload (e.g. extracting `role`, `text`, `timestamp` fields — that is normalization)
- Joins across files, sessions, or threads
- Regex matches on the payload or classification outputs
- Any field that depends on another row
- Any field whose value would change if the classifier config changed

**Test of the invariant:** deleting the raw layer and re-ingesting from the source files produces byte-identical rows (modulo `ingested_at` / `ingest_run_id`). If the new rows differ in any other column, something is doing interpretation and belongs in a later layer.

---

## Layer 2 — Normalized

**Purpose:** turn raw content into stable, typed, deduplicated rows that every later stage can rely on. Still no semantics — a human tagger, a regex classifier, and an LLM classifier must all see the same normalized rows.

**Allowed in a normalized row:**
- Typed extraction of payload fields that are explicitly present in source JSON (`role`, `text`, `timestamp`, `model`, `message_id`, `session_id`, `thread_id`)
- Deduplication by stable keys (same `message_id` seen twice → keep one)
- Rejection of malformed entries with an error row in `normalized_errors` (proposed)
- Light structural extraction where the source makes the relationship explicit: e.g. a tool-use event whose payload literally names a spawned session can produce a `parent_session_id` in `normalized_session_events`
- Normalize metadata: `normalized_at`

**Forbidden in a normalized row:**
- Regex matches on `text` that decide what kind of message it is
- Heuristics like timestamp overlap or nearest-neighbor linking
- Any field that reads another session's rows to decide this session's value
- Classification labels (`is_skill_template`, `is_retro_trigger`, `session_kind`, etc.)
- Anything that requires a config file to interpret (other than the parser's own field mapping)

**Test of the invariant:** rebuilding the normalized layer from the raw layer produces identical rows. If changing a regex config changes normalized output, the regex belongs in Layer 3.

---

## Layer 3 — Classified `derived_*`

**Purpose:** per-item interpretation. One row per normalized item, annotated with what the item IS. This is where regex, heuristics, and LLM classification live.

This layer is new as of 2026-04-19. Previously, per-item interpretation was mixed into Layer 4 aggregates, which made it hard to re-classify without rebuilding aggregates and hard to compare two classifier versions against each other.

**Allowed in a classified row:**
- Per-item classification labels (`session_kind`, `message_kind`, `practice_type`)
- Parent/child linkage where it required inference (`parent_session_path`, `parent_source` = how we decided)
- Confidence levels (`explicit` | `overlap` | `template` | `fallback` | similar)
- `classifier_version` — freezes which rules produced this row
- `classified_at` — when the classification ran

**Forbidden in a classified row:**
- Aggregates (counts, sums, rollups) — that is Layer 4
- Facts that could have been extracted deterministically at normalize time
- Mutation of existing rows when a classifier version changes — new version writes new rows alongside the old ones

**Versioning rule:** every row carries the exact `classifier_version` that produced it. Bumping the version does NOT retroactively rewrite older rows — it writes a new set. Queries that want "current" classification filter by the latest version; comparison queries keep access to history.

**Test of the invariant:** running the same classifier version over the same normalized input produces identical rows (idempotent). Two different versions produce two co-existing sets of rows for the same items.

**Session-level vs message-level classification are separate tables.** Verified on the Claude Code warehouse (2026-04-19, see `docs/private/product-hypotheses/H-040.md`):

- **Session-level** (one row per `.jsonl` file): `kind ∈ {main, subagent, unknown}`. Detectable deterministically from the file path — main sessions are UUID-named, subagent sessions are `agent-*.jsonl` or `subagents/agent-acompact-*.jsonl`. Parent-child links are extractable from `Agent` tool_use events in the parent with sub-second timestamp accuracy. No regex, no LLM, no heuristics needed.
- **Message-level** (one row per normalized message): `kind ∈ {human_authored, skill_template, context_inject, continuation_prompt, interruption_marker, unknown}`. Detected by matching `Skill` tool_use events in the parent assistant payload, plus a small set of stable regex patterns for context/continuation markers. Skill invocations DO NOT spawn a new file — they inject templates into the parent session's `role='user'` slot.

The two layers must not be collapsed into one table: they describe different kinds of items (files vs messages), they use different signals (filename vs content), and they have different confidence profiles (filename is 100% deterministic; message content needs regex and may need LLM fallback). The classifier-version axis is also independent — a new skill added to the tool does not change session classification.

---

## Layer 4 — Aggregate `derived_*`

**Purpose:** rollups, cross-item relationships, and goal/attempt shape. This is the "metrics" layer and the main read path for reports.

**Allowed in an aggregate row:**
- Counts, sums, averages over classified + normalized rows
- Cross-item relationships (retry chains, parent-child rollups)
- Goal-level and project-level shape (attempt numbering, token totals, time bounds)
- `pipeline_version` — freezes which aggregate logic produced this row

**Forbidden in an aggregate row:**
- Per-item interpretation that isn't already in Layer 3
- Raw text or payload content (those stay in Layer 2)
- Field values that silently collapse partial-data (`None` tokens → `0`). Prefer an explicit coverage field and propagate NULL when coverage is incomplete.

**Test of the invariant:** aggregates equal exactly what their source rows say. E.g. `SUM(derived_projects.total_tokens) == SUM(derived_session_usage.total_tokens)`. These equalities are existing tests; new aggregates must add similar equality tests.

---

## Cross-layer invariants

These should be enforced by tests in `tests/public/` and by the validation code that runs at the end of each pipeline stage. Every invariant below is expressed so it can be checked with a single SQL query or a deterministic rebuild.

**Raw ↔ filesystem**
- For every source file on disk that was ingested, all `raw_events` rows from that file carry the same `file_sha256`, and that value equals `sha256(file_contents_on_disk)`.
- Raw does NOT filter malformed payloads. If a source file contains an invalid JSON line, that line is still captured in `raw_events.payload`. Validity is enforced at the normalize boundary, not at ingest. Rejecting malformed content at raw would be interpretation.

**Normalized ↔ raw**
- Every `normalized_*` row carries enough identifiers (`source_path` + stable per-item key, e.g. `message_id`, `session_id`) to locate its source line(s) in `raw_events`. Stated as a query: `SELECT COUNT(*) FROM normalized_messages nm LEFT JOIN raw_events re ON re.source_path = nm.source_path AND ... WHERE re.event_id IS NULL` must be zero.
- Deleting the normalized layer and rebuilding it from raw produces identical rows, modulo `normalized_at` timestamps and any `ingest_run_id` back-references.

**Classified ↔ normalized**
- `derived_session_kinds.session_path ⊆ normalized_sessions.session_path` (no orphans).
- For every `(session_path, classifier_version)` pair there is exactly one row.
- `kind = 'main' ⟺ parent_session_path IS NULL` (enforced as a CHECK constraint on the table).
- Re-running the same classifier version over the same normalized input produces identical rows (idempotent within a version).

**Aggregate ↔ classified + normalized**
- `SUM(derived_projects.total_tokens) == SUM(derived_session_usage.total_tokens)` (verified on current warehouse; already an implicit test).
- `derived_goals.attempt_count == COUNT(derived_attempts WHERE thread_id = derived_goals.thread_id)` (verified on current warehouse; 0 mismatches across 160 goals).
- After the classified layer lands: `derived_goals.main_attempt_count == COUNT(derived_session_kinds WHERE thread_id = derived_goals.thread_id AND kind = 'main' AND classifier_version = <current>)`.
- No orphans between aggregate and its sources: `derived_attempts.session_path ⊆ normalized_sessions.session_path`, `derived_goals.thread_id ⊆ normalized_threads.thread_id`, `derived_session_usage.session_path ⊆ normalized_sessions.session_path`. (All verified at 0 orphans on current warehouse.)

**Idempotency (across all layers)**
- Running the full pipeline twice on unchanged input produces byte-identical rows, modulo fields that track the run itself: `ingested_at`, `normalized_at`, `classified_at`, `derived_at`, and `ingest_run_id`. Any other column that changes between runs indicates non-determinism and is a bug.

---

## Versioning policy

Three version axes, one column per axis on the relevant layer:

| Column | Lives in | Changes when |
|---|---|---|
| `ingest_run_id` | raw | A new ingest pass starts (usually every run) |
| (implicit: schema version) | all layers | Table schema changes — bump via migration |
| `classifier_version` | classified | Classifier rules change (new template, new model) |
| `pipeline_version` | aggregate | Aggregate logic changes |

**Rule:** bumping a downstream version never requires upstream data to be rewritten. Layer 1 never cares about classifier versions; Layer 3 never cares about aggregate versions.

Rules that consume external config (regex files, pricing tables) embed the config hash in the version string — e.g. `classifier_version = 'v1-skills-' + sha8(skill_templates.yaml)`. Identical inputs → identical version → identical outputs.

---

## What happens when rules are violated

The most common violations are "fields leaked upstream":

- A regex in normalize → classification rules silently change normalized data when the config changes. Move the regex output to Layer 3.
- An aggregate written back into `normalized_*` — e.g. `normalized_threads.message_count`. These blur the line between Layer 2 and Layer 4; they are tolerable where cheap to compute and stable, but should be treated as a smell.
- A parse that writes typed fields into `raw_*` — these belong in Layer 2.

Known current violations of these rules (to be fixed as a separate refactor, not as part of new feature work) are tracked in `architecture/ARCH-018-layer-separation-cleanup.md`.

---

## Adding a new layer-crossing feature

Checklist when a change spans layers:

1. Identify the layer where each new fact belongs. A classifier's verdict is Layer 3, not Layer 2; a rollup is Layer 4, not Layer 3.
2. Add or extend the relevant table; do not append to a table in a different layer just because the column "fits".
3. Wire versioning: `classifier_version` if new classification, `pipeline_version` if new aggregate.
4. Add a cross-layer invariant test that would fail if the new column leaks upstream.
5. Update [history-pipeline.md](history-pipeline.md) if the table catalog changed.
