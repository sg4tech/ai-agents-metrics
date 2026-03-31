# Product Hypotheses

Use this file to track active product and metrics hypotheses for `codex-metrics`.

Purpose:

- make PM reasoning explicit instead of letting it live only in chat
- separate confirmed product truths from working hypotheses
- preserve why a hypothesis existed, not just the latest opinion
- force periodic re-evaluation when new evidence appears

Rules:

- Treat every non-confirmed product proposal as a hypothesis, not as settled truth.
- For each meaningful hypothesis, record:
  - statement
  - why it matters
  - expected upside
  - main risks or where it may be wrong
  - alternatives considered
  - current confidence
  - evidence status
  - next re-evaluation trigger
- When new evidence appears, update the existing hypothesis entry with a dated note instead of deleting the old reasoning.
- Move ideas into `docs/product-framing.md` only after they are confirmed enough to act as stable framing.
- Keep this file focused on decision-relevant hypotheses, not general brainstorming noise.

## Status Labels

- `active` for current working hypotheses
- `validated` for hypotheses with strong enough evidence to guide default product decisions
- `rejected` for hypotheses that no longer fit the evidence
- `superseded` for hypotheses replaced by a better-framed successor

## Current Hypotheses

### H-001 — Exact outcome fit should be treated as the primary product-quality signal

- Status: `active`
- Created: `2026-03-31`
- Statement:
  - The most decision-useful product metric for `codex-metrics` is closer to exact outcome fit than to raw goal success rate or raw total cost.
- Why it matters:
  - If true, the product should prioritize quality signals such as `result_fit` over top-line closure metrics.
- Expected upside:
  - reduce false confidence from inflated success summaries
  - align reporting with the operator's real pain: "did Codex produce what was actually wanted?"
  - improve evaluation of workflow changes
- Main risks or where this may be wrong:
  - `exact_fit` is operator-judged and may be noisy
  - time-to-acceptable-result may matter more than fit alone
  - a broader acceptance metric may be more useful than strict exact fit
- Alternatives considered:
  - `time to acceptable result` as the north-star metric
  - `rework pressure` as the primary proxy
  - a broader `accepted / accepted-after-rework / not-accepted` model
- Current confidence:
  - `medium`
- Evidence status:
  - supported by this repository's history, where raw success often looked too optimistic and `result_fit` added important truth
  - not yet validated across external projects because their `result_fit` fields are still mostly unreviewed
- Next re-evaluation trigger:
  - after more cross-project reviewed `result_fit` data exists
  - or after a summary redesign is tested against real operator decisions
- Notes:
  - `2026-03-31`: promoted from chat into explicit product hypothesis after repeated concern that success metrics looked too successful.

### H-002 — Retry pressure is likely the strongest secondary metric after quality fit

- Status: `active`
- Created: `2026-03-31`
- Statement:
  - Attempts, failed entries, and continuation chains may be a better second-order operating metric than raw cost.
- Why it matters:
  - If true, summary and audits should highlight rework pressure before aggregate spend.
- Expected upside:
  - improve process decisions around requirements, lead mediation, and guardrails
  - make false "success" patterns easier to spot
- Main risks or where this may be wrong:
  - retry pressure can still miss slow but single-pass bad outcomes
  - some rework is cheap and acceptable, so the metric can overstate pain
- Alternatives considered:
  - speed-first metrics
  - cost-first metrics
  - pure acceptance metrics without retry context
- Current confidence:
  - `medium`
- Evidence status:
  - supported by local history and `audit-history`
  - not yet validated as the best secondary metric across multiple repositories
- Next re-evaluation trigger:
  - after cross-project comparison includes more reviewed quality signals
  - or after speed tracking becomes stronger
- Notes:
  - `2026-03-31`: added during PM review after seeing that retry pressure explained more than raw success in local history.

### H-003 — Raw total cost is a guardrail metric, not the primary north star

- Status: `active`
- Created: `2026-03-31`
- Statement:
  - `Known total cost (USD)` is useful for budget awareness, but it is too coarse to be the main product metric for workflow decisions.
- Why it matters:
  - If true, the product should keep total cost visible but avoid centering product decisions on it.
- Expected upside:
  - reduce over-optimization for cheapness
  - keep quality-first framing intact
  - push analysis toward cost-in-context metrics, such as cost by goal type or by accepted quality outcome
- Main risks or where this may be wrong:
  - in some projects cost may become the dominant business constraint
  - underweighting cost too much could hide profit erosion
- Alternatives considered:
  - total cost as the top-line metric
  - cost per product success
  - cost per exact-fit product goal
- Current confidence:
  - `high` that total cost alone is insufficient
  - `medium` on the best replacement cost view
- Evidence status:
  - supported by current cross-project comparison, where raw totals are not very comparable because goal-type mixes differ substantially
- Next re-evaluation trigger:
  - after cost-by-goal-type or cost-by-quality slices are available
- Notes:
  - `2026-03-31`: derived from comparing `codex-metrics`, `invest`, and `hhsave` snapshots.
