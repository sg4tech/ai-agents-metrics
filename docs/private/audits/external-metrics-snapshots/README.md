# External Metrics Snapshots

This directory stores read-only snapshots of `codex_metrics.json` from other repositories.

Purpose:

- preserve external comparison context inside this repository
- support cross-project audits without depending on live mutable files
- keep a raw-data trail for product analysis

Rules:

- these files are not the source of truth for the external repositories
- do not run mutating `codex-metrics` commands against these snapshots
- when referencing them in analysis, treat them as point-in-time captures
- prefer date-stamped filenames and include the source repository name
