# Product Framing

This document describes the current best confirmed framing for the product.

Working product and metrics hypotheses that are not yet fully confirmed belong in:

- `docs/product-hypotheses.md`

## Product

`codex-metrics` is an internal local operator tool for managing the effectiveness and economics of Codex-assisted engineering work.

It is not a general analytics platform and not a public SaaS product.

Current intended category:

- internal operator tool

## Primary User

The primary user is the Codex operator: the person directly using Codex to do real engineering work and adjusting their own process over time.

Secondary users:

- PM or engineering manager reviewing the results later
- future contributors trying to understand why the workflow evolved the way it did

## Job To Be Done

When I work through Codex, I want to see whether the changes I make to my workflow are actually improving development quality and speed without letting AI cost eat the profit from my engineering work, so that I can keep what works and cut what does not.

## Core User Problem

Without this tool:

- it is hard to tell whether workflow changes create real leverage or just extra activity
- quality and speed are easy to judge emotionally instead of from history
- AI usage cost is easy to ignore until it starts eating margin
- retries and failed paths get lost, which makes process improvement weaker

The tool exists to make the relationship between outcome quality, delivery effort, and AI cost explicit enough to manage.

## Confirmed Context So Far

The following product truths are already confirmed:

- the primary user is the Codex operator
- quality matters more than speed
- cost matters because AI is paid usage and should not eat engineering profit
- the product should help decide what workflow changes actually work and what should be changed again

The following product questions are still intentionally open and should be treated as active hypotheses until better evidence exists:

- the final best quality metric
- the final best cost metric
- the exact long-term balance between delivery optimization and cost optimization

## Main Workflow

1. Use Codex to work on a real engineering goal.
2. Record goals, attempts, failures, and cost signals as the work happens.
3. Review goal-level and entry-level metrics together.
4. Decide which workflow changes improved the result and which should be rolled back or adjusted.
5. Iterate on the way Codex is being operated.

## Core Decisions Supported

The tool should help the operator answer:

1. Are my workflow changes making the output closer to what I wanted on the first try?
2. Is development getting faster without lowering quality?
3. Which usage patterns create too much retry pressure?
4. Is AI cost still small enough relative to the value of the work?
5. What should I change next in how I operate Codex?

## North Star

Primary north star:

- accepted product outcomes with minimal retry pressure and controlled cost

This is not meant to optimize for cheapness alone.

The intended priority order is:

1. quality
2. speed
3. cost control

Cost matters because AI is paid usage and should not eat engineering profit, but cost optimization must not degrade the result.

## Quality Priority

Quality matters more than speed.

The current practical proxy for quality is:

- how often the result that was wanted is produced without extra corrective passes

In plain terms:

- “got what I wanted right away” is the strongest current signal of quality
- the clearest current symptom of bad quality is “the output is not actually what was requested”

Examples of bad quality for this product:

- adjacent technical work instead of the requested outcome
- partial completion presented as if the goal were solved
- a lot of engineering motion while the core requested result is still missing

These signals should be treated as working proxies, not final truth.

The product is also meant to help discover a better long-term quality metric through real usage history, rather than pretending that the perfect metric is already known.

## Cost Priority

Cost is secondary to outcome quality, but still strategically important.

The desired state is:

- keep AI cost from eating engineering profit
- then progressively reduce token and cost waste without hurting outcomes

So cost should be optimized under a “do not reduce result quality” constraint.

At the moment, the exact best cost-view is still open:

- cost per success
- cost per miss
- cost per attempt
- total cost over time

The system should preserve enough raw cost context to let that be decided later from real use.

## Key Metrics

Current primary metrics:

- product goal success rate
- attempts per closed goal
- entry failure reasons
- known total cost and known total tokens

Current interpretation rule:

- goal-level success must always be read together with entry-level retry pressure
- current quality-related metrics are provisional operator proxies and should be refined empirically over time
- cost is a business signal for how painful success or miss was
- failure reasons are primarily a debugging signal for what to change next

Future direction:

- improve the connection between outcome quality and cost efficiency

## Current Scope

In scope now:

- local JSON source of truth
- local markdown reporting
- goal and attempt history
- retry and failure visibility
- partial automatic usage and cost ingestion from local Codex telemetry
- operator-facing process discipline for retros and verification

Out of scope for now:

- hosted multi-user dashboards
- centralized team analytics
- polished end-user UI
- perfect historical cost completeness

## Product State

Current state:

- internal alpha

That means:

- technically credible
- already useful for internal operator decision-making
- still improving framing, UX, and cost clarity

## One-Month Success

In one month, success should look like:

- the framing remains stable around operator value
- the metrics help decide which Codex workflow changes to keep
- quality signals are trusted more than intuition alone
- cost visibility is good enough to spot obviously wasteful patterns

## One-Quarter Success

In one quarter, success should look like:

- the tool is routinely used to refine Codex operating practice
- the operator can point to concrete workflow changes that improved output quality
- token and cost waste are being reduced without hurting result quality
- the system is helping protect engineering profit, not just describe engineering history
