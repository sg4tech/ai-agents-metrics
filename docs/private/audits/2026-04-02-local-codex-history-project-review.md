# Local Codex History Project Review

Date: 2026-04-02
Repository: `codex-metrics`
Review type: local history analysis over `~/.codex`

## Scope

This review is based on the freshly rebuilt local history warehouse at `/tmp/codex_history_report.sqlite`, populated from `~/.codex` and then normalized and derived into analysis marts.

Coverage in this snapshot:

- 25 threads
- 25 sessions
- 39,131 derived timeline events
- 6,165 messages
- 47,535 logs
- history range from `2026-03-26T13:26:18.334Z` to `2026-04-02T17:21:38.312Z`

This is a local history slice, not the entire lifetime of the broader project.

## Executive Summary

The history shows a project that is strongly self-referential and operationally disciplined.

Most of the local work is concentrated in `codex-metrics` itself. The dominant themes are metrics bookkeeping, workflow hardening, hypothesis framing, reporting discipline, and the new history ingestion pipeline. That makes the project look less like a generic end-user product and more like a tooling system that is actively building its own analytical substrate.

The strongest signal in the history is not product throughput. It is process consistency:

- single-pass sessions dominate
- there are no retry chains in this local slice
- the work is heavily clustered into a few large sessions
- the biggest sessions are the ones that improve the project's own measurement and workflow machinery

The main product-level conclusion is that the repository is now mature enough to support retrospective analysis of its own work history, but the project's center of gravity still sits in meta/tooling work rather than in a stable external product loop.

## Verified Facts

### Workspace distribution

The local history spans four workspaces:

- `codex-metrics`: 16 goals
- `hhsave`: 5 goals
- `invest`: 3 goals
- `spendsave`: 1 goal

`codex-metrics` is the clear majority of the observed local history.

### Session shape

- All 25 sessions were sourced from `vscode`
- Every derived goal has `attempt_count = 1`
- Every derived retry chain has `retry_count = 0`
- There is no evidence of multi-session retry pressure in this slice

### Workload shape

Message counts are very skewed:

- median messages per goal: 69
- mean messages per goal: 246.6
- maximum messages in one goal: 1,594

Usage-event counts are similarly skewed:

- median usage events per goal: 103
- mean usage events per goal: 317.64
- maximum usage events in one goal: 2,183

### Temporal shape

The work is clustered rather than evenly distributed.

By day, the heaviest observed activity was:

- `2026-03-29`: 3 goals, 2,554 messages, 3,413 usage events
- `2026-04-02`: 14 goals, 1,178 messages, 1,601 usage events

### Heavy sessions

The largest sessions by message count are:

1. `codex-metrics` update-script overhaul task, 1,594 messages
2. `hhsave` Chrome/Google Sheets automation task, 1,015 messages
3. `invest` project-onboarding / PM-style review task, 783 messages
4. `codex-metrics` bootstrap-residue cleanup task, 769 messages
5. `hhsave` fixture reorganization task, 379 messages

## Inferred Conclusions

These are interpretations, not direct facts.

### 1. The project is process-heavy by design

The history suggests that `codex-metrics` is not just building a product; it is building the machinery for trustworthy analysis of agent work.

That aligns with the recent ingest/normalize/derive pipeline and with the history of tasks focused on policy, metrics semantics, reporting, and workflow guardrails.

### 2. Meta work still dominates the center of gravity

From the titles alone, the `codex-metrics` threads are overwhelmingly about:

- bookkeeping and reporting
- product hypotheses
- CLI and workflow hardening
- documentation and policy alignment
- history analysis infrastructure

That does not mean product work is absent. It does mean the project is still spending most of its energy on the system that measures the work, not on a clearly separated downstream product loop.

### 3. The local workflow is stable, but not yet deeply iterative

The lack of retries in this slice is interesting.

It may mean:

- the local sessions are usually started only when the task boundary is already clear
- the workspace history is being captured as one coherent pass per task
- or the current history model is better at capturing session boundaries than at capturing reopen/retry semantics

The safest conclusion is that the observed local workflow is mostly single-pass and low-retry.

### 4. Retrospective reconstruction looks viable

The local history is rich enough to support the hypothesis behind `H-008`:

- threads are identifiable
- sessions are identifiable
- messages, logs, and usage events are plentiful
- derived marts can reconstruct timelines and attempt structure

That is strong evidence that a retrospective layer is practical and useful.

## What This Means For The Project

The project appears to be in a healthy but still self-building stage.

The most credible near-term path is:

1. keep the raw history pipeline as the source of truth for analysis
2. use derived marts for reusable review and reporting
3. keep live capture minimal and invariant-focused
4. use the project's own history to decide where the process is still too expensive or too ambiguous

In other words: the project has now reached the point where it can analyze itself in a structured way, but it still needs a sharper boundary between infrastructure work and the actual product loop it is trying to enable.

## Recommendations

1. Keep building on the derived history layer instead of re-deriving joins ad hoc for every question.
2. Add a thin classification layer for workspace/topic if we want a better product-vs-meta split later.
3. Use future audits to compare:
   - message-heavy work vs outcome quality
   - workspace concentration vs delivery spread
   - retry pressure vs task clarity
4. Treat the current report as a baseline, not a final verdict.

## Bottom Line

This local history strongly supports the idea that `codex-metrics` should analyze conversation history retrospectively rather than rely on manual live metric writing alone.

The project is already behaving like an internal analysis tool that is learning to measure itself. The next leverage point is to turn that self-measurement into a sharper product boundary and a clearer picture of which work is truly moving the project forward.
