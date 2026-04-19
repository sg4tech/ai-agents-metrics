# Marketing Measurement

How to know if marketing is working, and what to measure at each stage.

## Canonical sources

- **David Sacks** — the SaaS metrics canon: CAC, LTV, payback period, NRR. The most widely shared framework for B2B SaaS unit economics.
- **Patrick Campbell** (ProfitWell / Paddle) — largest public SaaS pricing and retention research corpus. Churn, expansion revenue, NRR benchmarks.
- **Fred Reichheld** (Bain) — Net Promoter Score (NPS). *The Ultimate Question*. A single question that predicts organic growth: "How likely are you to recommend us to a friend or colleague?"
- **Andrew Chen** — viral coefficient and the math of organic spread.
- **Sean Ellis** — the 40% rule for product-market fit: "What would you feel if you could no longer use this product?" If <40% say "very disappointed," PMF is not yet real.
- **Avinash Kaushik** — *Web Analytics 2.0*. The distinction between metrics (numbers) and KPIs (numbers that matter for decisions). "Every metric must have a target and an owner."

## Core metrics framework

### Unit economics — the foundation

| Metric | What it measures | Healthy target (B2B SaaS) |
|---|---|---|
| **CAC** (Customer Acquisition Cost) | Total sales + marketing spend ÷ new customers acquired | Depends on ACV; track trend |
| **LTV** (Customer Lifetime Value) | Average revenue per customer × gross margin ÷ churn rate | LTV:CAC ≥ 3:1 |
| **CAC Payback Period** | CAC ÷ (monthly revenue × gross margin) | < 12 months for healthy growth |
| **NRR** (Net Revenue Retention) | Revenue from existing customers next period ÷ this period (including expansion, contraction, churn) | > 100% = growth without new customers; > 120% = exceptional |
| **Gross margin** | (Revenue − COGS) ÷ Revenue | SaaS: > 70% |

**LTV:CAC ratio interpretation:**
- < 1:1 — losing money on every customer
- 1–3:1 — margin exists but growth is expensive
- 3:1 — commonly cited healthy target
- > 5:1 — possibly under-investing in growth; check whether you're leaving market share on the table

### Funnel metrics

Track at each stage from first touch to retained customer:

| Stage | Metric |
|---|---|
| Awareness | Impressions, reach, organic search traffic, brand search volume |
| Acquisition | Visits, sign-ups, install rate, CPL (cost per lead) |
| Activation | % reaching value moment within N days (define the value moment first) |
| Retention | Day 1 / Day 7 / Day 30 retention; churn rate |
| Revenue | MRR, ARR, ACV, expansion revenue |
| Referral | NPS, viral coefficient (K), referral rate |

The **pirate metrics** (AARRR — Acquisition, Activation, Retention, Revenue, Referral) are the standard shorthand. Identify which stage is the current bottleneck before optimizing any other stage.

### NPS — Net Promoter Score

Single question: "On a scale of 0–10, how likely are you to recommend this to a friend or colleague?"
- **Promoters** (9–10): active ambassadors
- **Passives** (7–8): satisfied but won't promote
- **Detractors** (0–6): at risk of negative word of mouth

NPS = % Promoters − % Detractors.

Useful for: tracking organic growth potential, identifying churn risk, benchmarking over time.

**Limitation:** NPS is a lagging indicator and aggregates very different problems. Always ask a follow-up: "What's the main reason for your score?"

### Viral coefficient (K)

K = (number of invitations sent per user) × (conversion rate of those invitations)

- K > 1: viral growth — each user brings in more than one new user
- K = 1: replacement growth only
- K < 1: requires paid or owned acquisition to grow

For developer tools, K is mostly organic (recommendation in a Slack, mention in a post, GitHub link). Measure it via referral tracking and attribution.

### PMF signal (Sean Ellis)

Survey active users: "How would you feel if you could no longer use this product?"
- Very disappointed / Somewhat disappointed / Not disappointed / N/A

**If ≥ 40% say "very disappointed," you have product-market fit.** Below 40%, the product is not yet must-have. Distribution investment on top of a sub-40% PMF score is premature and wasteful.

## Practical principles

- **Metrics must have targets and owners (Kaushik).** A metric without a target is decoration. A metric without an owner is unactionable.
- **Measure outcomes, not activity.** "Published 12 posts" is activity. "Organic traffic grew 30% MoM from content" is an outcome. Activity metrics are easy to report and easy to game.
- **One north-star metric per stage.** Multiple KPIs at the same stage produce divided attention and conflicting optimizations. Pick one. Report others as context.
- **Attribution is always approximate.** Multi-touch attribution models (first touch, last touch, linear, time-decay) each make assumptions that are wrong. Use them directionally, not as truth. First-party data beats third-party attribution.
- **NRR > CAC optimization for retention-heavy products.** Improving NRR from 95% to 110% is worth more than halving CAC. Retained and expanded customers are cheaper to keep than new customers are to acquire.
- **The 40% PMF test before distribution.** Run the Ellis survey before investing in distribution. A score below 40% means the product needs work, not marketing.
- **Benchmark against yourself, not the industry.** Industry benchmarks are lagging averages across heterogeneous companies. Your own trend (this month vs last quarter) is more actionable.
- **Churn is the most honest marketing metric.** You can buy acquisition; you cannot buy retention. If churn is high, no acquisition strategy fixes the business. Diagnose churn before scaling spend.
