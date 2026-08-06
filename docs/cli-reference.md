# CLI reference

`ai-agents-metrics` analyzes local Claude Code and Codex history without manual instrumentation.

## Primary workflow

```bash
ai-agents-metrics history-update
ai-agents-metrics show
ai-agents-metrics render-html
```

### `history-update`

Runs ingest, normalization, classification, and derivation for local agent history. Use `--source codex`, `--source claude`, or `--source all`; `--source-root` overrides a source directory and `--warehouse-path` overrides the SQLite warehouse.

### `show`

Prints a warehouse-native summary of threads, attempts, retry pressure, messages,
token usage, coverage, and the observed time window. Pass `--json` for the stable,
versioned machine-readable output or `--warehouse-path` to select a warehouse.
The command does not read the legacy manual-tracking ledger.

### `render-html`

Generates a self-contained HTML report. `--output` selects the destination, `--days N` limits the time window, and `--cwd PATH` selects a project in a shared warehouse.

## Pipeline stages

The individual `history-ingest`, `history-normalize`, `history-classify`, and `history-derive` commands expose each pipeline stage for debugging and automation.

## Analysis and maintenance

- `history-audit`, `history-compare`, `derive-retro-timeline`, `audit-cost-coverage` — advanced analysis and diagnostics.
- `completion {bash,zsh}` — shell completion output.
- `install-self` — install the executable in a stable local path.
- `verify-public-boundary` — check a public repository tree against boundary rules.
- `security` — scan staged changes for sensitive data.
