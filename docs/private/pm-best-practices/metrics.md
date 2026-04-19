# Metrics and Analytics

How to measure progress without deceiving yourself.

## Canonical sources

- **Sean Ellis** — the North Star Metric concept; the PMF 40% survey ("How would you feel if you could no longer use this? — very disappointed / somewhat disappointed / not disappointed"). The 40%-very-disappointed threshold is the most widely cited PMF heuristic.
- **Rahul Vohra** — "How Superhuman Built an Engine to Find Product/Market Fit" (First Round Review). Operationalized Ellis's survey into a continuous PMF process.
- **Amplitude** — *The North Star Playbook* (free). Canonical NSM framework: NSM = f(input metrics); guardrail/counter metrics alongside.
- **Alistair Croll / Benjamin Yoskovitz** — *Lean Analytics*. One Metric That Matters (OMTM) per stage of growth; stage-appropriate metrics.
- **Dave McClure** — AARRR "pirate metrics" (Acquisition, Activation, Retention, Referral, Revenue). Dated for B2B but still the ur-funnel.
- **Kerry Rodden et al. (Google)** — HEART framework: Happiness, Engagement, Adoption, Retention, Task success. Goals → Signals → Metrics method.
- **Avinash Kaushik** — *Web Analytics 2.0*. Digital analytics fundamentals; "don't measure, learn."

## Core concepts

- **North Star Metric.** A single leading indicator of long-term customer value. Not revenue (lagging); not activity (too cheap). Good NSMs typically combine breadth × depth × frequency.
- **Multiple North Stars (evolution).** For products with multiple distinct value axes, a single NSM can narrow visibility and create misaligned incentives. The advanced pattern: 2–3 NSMs, each covering a different dimension (e.g., engagement depth, activation breadth, retention), with explicit hierarchy (one primary; others as co-constraints). Not a license for metric sprawl — requires more discipline, not less.
- **Input metrics.** 3–5 metrics you believe causally drive the NSM. These are where teams actually act.
- **Guardrail / counter metrics.** Numbers that should *not* move adversely when the NSM moves. Prevents Goodhart's Law gaming.
- **Leading vs lagging.** Leading indicators move first and are actionable; lagging indicators confirm but arrive too late to intervene.
- **PMF survey (Ellis/Vohra).** Recurring survey of engaged users; track the 40% threshold by segment. Segments below 40% reveal positioning leaks.
- **PMF convergence model (2025 practice).** No single signal is sufficient. Modern B2B PMF is the convergence of five: (1) ≥40% "very disappointed" (Ellis), (2) strong D30 cohort retention, (3) NPS >50, (4) CAC payback <12 months, (5) rising organic growth / referrals. All five pointing the same direction is signal; divergence between them is information about what's broken. **For OSS / free tools:** CAC and payback don't apply; replace with (4) unprompted public mentions / shares, (5) return installs or repeat runs after first use. The qualitative Ellis signal remains valid even without a formal survey — two or three unsolicited "I can't work without this" comments from people you didn't prompt are the equivalent of a 40% score at early stage.
- **HEART.** Pick among Happiness / Engagement / Adoption / Retention / Task-success per product or feature; don't use all five for everything.
- **OMTM per stage.** Different business stages (empathy → stickiness → virality → revenue → scale) have different constraining metrics.

## Practical principles

- **Own one number.** A PM without a primary metric is a project manager.
- **Activity metrics are not outcome metrics.** "Launched four features" is output. "30% of new users reached aha moment in week 1" is outcome.
- **Ratios and rates over raw counts** once past earliest stage. Raw counts hide dilution and churn.
- **Segment first, aggregate second.** Aggregate PMF scores can be 35% while the best-fit segment is at 65%.
- **Counter-metric every KPI.** Every metric gameable without a guardrail will eventually be gamed, including accidentally.
- **Define `n/a` policy explicitly.** For partial-coverage metrics, either report covered-subset averages with coverage %, or the metric collapses under noise.
