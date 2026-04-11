# A polished HTML report may help a human quickly judge whether work is effective or inefficient

Single-hypothesis file.

### H-033 — A polished HTML report may help a human quickly judge whether work is effective or inefficient

- Status: `planned`
- Created: `2026-04-09`
- Updated: `2026-04-11`
- Statement:
  - The product may benefit from a human-facing HTML report or lightweight GUI that shows the current status of work and gives a short verdict about whether the work is progressing effectively, inefficiently, or somewhere in between.
  - The main goal is not to replace the agent-facing analysis layer, but to give a human sponsor a fast visual summary they can inspect without reading raw JSON or CLI output.
- Why it matters:
  - If true, the product would have a clearer human review surface for status, progress, retry pressure, and cost.
  - This could make the final verdict easier to understand for people who are not reading the raw metrics stream directly.
- Expected upside:
  - faster human inspection of current work health
  - clearer status signal for "healthy", "mixed", or "needs attention"
  - a more polished public-facing explanation of what the tool is telling the user
  - less dependence on CLI-only output for non-agent stakeholders
- Main risks or where this may be wrong:
  - could pull the product toward a human dashboard when the primary user is still the analyzing agent
  - may create duplicate reporting surfaces if it simply restates existing JSON/CLI summaries
  - if the verdict is too opinionated, it may overstate certainty or hide nuance
  - visual polish can become a distraction if the underlying decision signal is still weak
- Alternatives considered:
  - keep the product CLI-first and improve the text summary instead of adding HTML
  - generate a minimal static HTML export without interactive GUI behavior
  - build a richer local GUI only after the analysis verdict itself is clearly useful
- Current confidence:
  - `medium`
- Evidence status:
  - user confirmed the direction and specified the exact charts and metrics they want to see
  - not yet validated by testing whether a human actually makes better decisions with a visual verdict page
- Evaluation plan:
  - ship the static HTML report with the four charts below
  - verify that opening the file gives an immediate read on work health without any CLI knowledge
  - check whether the human reviewer uses it or falls back to CLI
- Next re-evaluation trigger:
  - after the first HTML report is generated and used in a real review session
- Related hypotheses:
  - complements H-007: markdown report is optional, but a human-facing HTML layer is still useful
  - complements H-024: public discoverability and human readability are related but not identical problems

---

## Implementation spec

### CLI command

```
./tools/ai-agents-metrics render-html [--output PATH] [--days N]
```

- Default output: `reports/report.html`
- Output path overridable via `--output`
- `reports/` is git-ignored; the file is not tracked
- Default time window: all available data (or `--days` to limit)

### Four charts (X axis = time, adaptive granularity)

**Granularity rule:** if the data window is ≤ 30 days → daily buckets; if > 30 days → weekly buckets. Applied uniformly across all charts.

#### Chart 1 — Closed successful tasks over time
- Type: bar chart
- Y: count of goals with `status=closed` and `outcome=success` per bucket
- Purpose: shows throughput trend

#### Chart 2 — Retry pressure over time
- Type: combo chart (line + bar)
- Y1 (bar): count of goals with `attempt_count > 1` per bucket (goals that needed at least one retry)
- Y2 (line): average `attempt_count` per closed goal per bucket
- Purpose: shows whether efficiency is improving or degrading

#### Chart 3 — Tokens spent over time
- Type: stacked bar chart
- Stacks: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cached_input_tokens`
- Y: token count per bucket
- Purpose: shows raw usage volume and cache efficiency trends

#### Chart 4 — Cost per successful task over time (key metric)
- Type: line chart
- Y: `sum(cost_usd for successful closed goals in bucket) / count(successful closed goals in bucket)`
- Only plotted for buckets that have at least one successful closed goal with known cost
- Purpose: the headline efficiency signal — is the product getting cheaper or more expensive per success

### Technical constraints

- Self-contained single HTML file (no external requests)
- Chart.js embedded inline
- Zero new Python dependencies (stdlib only)
- Data read directly from `events.ndjson` (same source as `show` and `render-report`)
- Goals without `cost_usd` are excluded from Chart 4 but counted in Charts 1–3

### Notes

- `2026-04-09`: added after the user proposed a GUI-like HTML report that gives a quick verdict on whether work is effective.
- `2026-04-11`: promoted to `planned`; full implementation spec written after design discussion. Confirmed: adaptive granularity, current-repo scope only, git-ignored output, retry metric = avg attempt_count per closed goal + count of multi-attempt goals.
