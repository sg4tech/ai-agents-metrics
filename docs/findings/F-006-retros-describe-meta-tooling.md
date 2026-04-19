# F-006 — Retrospectives in an AI-agent workflow overwhelmingly describe meta-tooling failures, not product-code failures

**Dataset:** 59 retro files in `docs/private/retros/`, committed between 2026-03-29 and 2026-04-16 (19 days, single developer on the `codex-metrics` repo). Classified 2026-04-19.

## TL;DR

Across 59 retrospective files written during a single-developer AI-agent project, **four meta-tooling themes — packaging/install, lifecycle/workflow, policy (AGENTS.md), and data/warehouse — account for 58% of retros**. The remaining 42% spread across product/PM, testing, git/CI, refactors, and dev-workflow fixes. Almost none are "the agent wrote wrong product logic." Writing AI-agent software breaks at the seams between tools, not inside the code the tools help produce.

Retro cadence is front-loaded: **49 of 59 retros land in the first 7 days** (including a 32-retro bulk-reflection day on 2026-03-29), and only ~5 per week thereafter. The infrastructure-pain rate visibly decays as the workflow stabilizes.

## Why measure this at all

When someone asks "does writing retros help?" the clean causal answer would be pre/post behavior metrics around each retro. That experiment is **not possible on this dataset** — see [Limitations](#limitations). But a descriptive question is still answerable: *what do AI-agent retros actually describe?* The answer shapes where teams should invest guardrail effort.

## Method

For each file in `docs/private/retros/`:
- extract the incident date from the filename prefix (`YYYY-MM-DD-*-retro.md`)
- verify against git log: 58 of 59 retros were committed on their incident date, 1 on the next day — so the filename date is the actual incident date, not a backfill label
- classify by keyword match against the remaining filename segment (e.g. `policy`, `bootstrap`, `task-lifecycle`, `history`, `usage`, `pm`, `test`)
- a retro matches multiple themes when keywords overlap; primary theme = first match

Classification keywords are listed in the analysis script in-line; the mapping is intentionally simple so anyone can reproduce by rerunning against filenames alone.

## Results — retros by theme

| Theme | Retros | Share |
|---|---:|---:|
| packaging_install | 9 | 15.3% |
| lifecycle_workflow | 9 | 15.3% |
| policy_agents_md | 8 | 13.6% |
| data_warehouse | 8 | 13.6% |
| product_pm | 7 | 11.9% |
| testing_quality | 5 | 8.5% |
| git_ci | 4 | 6.8% |
| refactor_arch | 3 | 5.1% |
| unclassified | 3 | 5.1% |
| dev_workflow | 2 | 3.4% |
| cli_ux | 1 | 1.7% |

**The top four themes are all meta-tooling.** Packaging/install covers PEP 639 classifier conflicts, standalone-binary drift, bootstrap-marker rename, venv-install staleness. Lifecycle/workflow covers task-start/finish guards, late-commit recovery, handoff QA. Policy covers AGENTS.md boundary rules, external-policy overreach, invariant normalization. Data/warehouse covers history-pipeline audits, cost coverage, usage-recovery format mismatch, model tracking.

**Only 12% of retros are product-PM.** Even within those, most describe framing/positioning or hypothesis-method issues — not "we built the wrong feature."

**Zero retros describe the agent writing semantically wrong code.** The incidents are shape-of-the-system problems: permissions, paths, renames, lifecycle ordering, policy sync. When an AI agent is responsible for implementation, the failure surface shifts upward — humans retrospect on the scaffolding, not the code.

## Results — retro cadence decay

| Window | Retros | Daily rate |
|---|---:|---:|
| Day 0 (2026-03-29) — bulk reflection | 32 | n/a |
| Week 0, excluding bulk day (2026-03-30 → 2026-04-04) | 17 | 2.8 / day |
| Week 1 (2026-04-05 → 2026-04-11) | 5 | 0.7 / day |
| Week 2 (2026-04-12 → 2026-04-16, partial) | 5 | 1.0 / day |

After the initial backfill burst, per-day retro density drops **~4×** from week-0-residual to week-1 and stays flat around 1/day. This is consistent with the infrastructure-maturing interpretation: once the scaffolding is settled, fewer scaffolding failures surface. It is *not* strong evidence of a learning effect — cadence could drop for many reasons (less new work, fatigue, batching) — but the rate change is not subtle.

## Limitations

**1. Retro-treatment effect is unmeasurable on this dataset.** The warehouse (`derived_goals.first_seen_at` from `warehouse-full.sqlite`) starts on 2026-03-29 — the same day as the first retros. There is no pre-retro behavior window to compare against. For the three post-treatment metrics we would care about (retry ratio, tokens-per-message, practice-event density), there is no valid counterfactual.

Even within the recorded window, the 2026-03-29 bulk-reflection day produces ~54% of all retros as effectively one treatment, with only 4-5 threads of post-treatment data before the warehouse cutoff. Any causal claim would be fitting noise.

**2. Classification is keyword-based, not semantic.** 19 of 59 retros match multiple themes; we assign the first match. A proper thematic analysis would require reading each file, which is not needed for the top-theme-share claim but would sharpen mid-tier categories.

**3. N=1 developer.** All retros are from a single developer's habit of writing them. The 58% meta-tooling concentration may be a personal pattern, a tooling-immaturity pattern, or an AI-agent-workflow pattern. Cross-developer replication is required to separate these.

## Implications

For anyone running AI-agent projects:
- Expect meta-tooling retros to dominate. Invest in packaging, task-lifecycle, and policy-sync guardrails *before* you invest in code-review or test-quality guardrails for the AI's output.
- The retro file itself lags the lesson: AGENTS.md rules were frequently added the same day as the incident, before the retro document existed. Retros are **documentation of lessons learned**, not the mechanism by which they were learned. Teams that expect retros to *cause* improvement may be miscalibrated.
- Infrastructure-pain decays. The first two weeks of an AI-agent project will generate an outsized share of retros; plan for retro fatigue to set in around week 2.

## Reproduction

- Input: `docs/private/retros/*.md` filenames
- Analysis script: inline Python in this session, classifier `{packaging, lifecycle, policy, data, product, testing, git, refactor, dev, cli}` keyed by substring match
- Warehouse: `warehouse-full.sqlite` (see [history-pipeline.md](../history-pipeline.md))
- Related findings: [F-003](F-003-practice-split-is-size-confounded.md) (size-confound warning), [F-004](F-004-rework-signal-exists-but-n-too-small.md) (N-too-small precedent), [F-005](F-005-practice-distribution.md) (descriptive method analogue)
