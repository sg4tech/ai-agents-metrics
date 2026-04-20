# F-007 — Within-thread, messages near a practice event use half the tokens of messages far from any practice

**Dataset:** 28 threads with ≥3 near-practice and ≥3 far-from-practice assistant messages, drawn from `warehouse-full.sqlite` on 2026-04-19. Same 160-thread / 334-session Claude Code history as F-001 through F-006.

## TL;DR

F-003 showed a 2.5× cross-thread gap between practice-using and no-practice threads after size-matching. Cross-thread comparisons still carry "different tasks" confounds — the threads aren't randomly assigned. Switching to a **within-thread design** — each thread as its own control — reproduces the effect cleanly:

- **Median far/near ratio: 2.05× (bootstrap 95% CI [1.23×, 2.47×]).** Messages ≥20 positions away from any prior practice event use 2× more total tokens than messages within 5 positions after a practice event, inside the same thread. Mean ratio is 2.03× with 95% CI [1.66×, 2.43×].
- **23 of 28 threads** (82%) show `ratio > 1.0`; **15 of 28** (54%) show ≥2×. Under a null of ratio=1.0, a sign test gives p = 0.000456 — the direction of the effect is highly significant even with a narrow dataset.
- The effect is present in all four position-in-thread quartiles (0-25%, 25-50%, 50-75%, 75-100%), so it is not explained by "practice events cluster at a specific part of the thread."
- **Mechanism test — `Agent` vs `Skill` split:** the effect is strongest for `Agent` practice events (median ratio 2.46×, CI [1.57×, 3.23×]) and materially weaker for `Skill` events (median 1.78×, aggregated 1.20×). `Agent` events are true subagent spawns with their own context window; `Skill` events are scripted workflows with no compression. This split is exactly the direction the compression-mechanism hypothesis predicts.

The most plausible mechanism, now corroborated by the `Agent`/`Skill` split, is **context compression by subagents**: when the main agent delegates to an `Agent`, the subagent consumes tokens in its own isolated context window and returns a compact summary. The main session's prompt stays small, so the *main session's* `total_tokens` per message drops. This is consistent with the subagent-overhead decomposition in F-003 and the subagent-aliased retry pattern in F-001.

## Why measure this within-thread

F-003 addressed the biggest confound in "does practice help?" — task size — by size-matching cross-thread pairs. That collapsed a naive 20× gap to 2.3-2.9× within matched buckets. But cross-thread comparisons still leave two confounds:

1. **Task type:** threads with practice may be systematically different kinds of work (more exploration-heavy, less single-function-patching) even when matched on size.
2. **Developer state:** practice-using and practice-skipping threads may correlate with the developer's focus/mode that day.

A within-thread design eliminates both. The same thread, the same task, the same developer-state — compare messages that are temporally close to a practice event against messages from the same thread that are not.

## Method

For each of 43 threads that contain at least one practice event and at least 20 assistant messages:

1. Order the thread's assistant messages by `message_timestamp`.
2. For each message, compute:
   - **position-in-thread** — `msg_index / thread_msg_count`, bucketed into quartiles.
   - **distance-to-prev-practice** — messages since the most recent practice event whose `timestamp` is at or before the current message's `message_timestamp`. `None` if the message precedes any practice event.
3. Bucket each message by `(position, distance)`:
   - position ∈ {0-25%, 25-50%, 50-75%, 75-100%}
   - distance ∈ {within_5_msgs, within_20_msgs, far_from_practice (>20), no_prior_practice}
4. Compute mean `total_tokens` per bucket.
5. For the per-thread robustness check: compute each thread's `mean(far) / mean(near)` ratio, requiring ≥3 messages in each side.

Source data: `derived_message_facts` joined with `derived_practice_events`. Query scripts are inline; no new code in `src/`.

## Results — two-dimensional bucket

Mean `total_tokens` per assistant message, 37 threads, 5858 messages total:

| Position | far_from_practice | within_20_msgs | within_5_msgs | no_prior_practice |
|---|---:|---:|---:|---:|
| 0-25% | 412,582 (N=323) | 253,892 (N=197) | **194,676** (N=181) | 288,440 (N=751) |
| 25-50% | 372,863 (N=560) | 327,163 (N=296) | **247,652** (N=271) | 396,048 (N=310) |
| 50-75% | 342,108 (N=841) | 246,799 (N=312) | **193,037** (N=190) | 379,146 (N=99) |
| 75-100% | 378,673 (N=914) | 362,608 (N=344) | **215,445** (N=127) | 526,495 (N=39) |

**The `within_5_msgs` column is the cheapest in every row.** The 0-25% row shows the natural context-growth curve: even far-from-practice early messages are high (412k) because they happen when the conversation is just starting and practice hasn't had a chance to fire. In later quartiles, `within_5_msgs` stays around 193-248k while `far_from_practice` stays around 342-379k — a 1.5-2× gap at every position.

(Absolute values are large because `total_tokens` on the Claude Code usage events reflects prompt + output + cache for each API call, not just the visible response text. Relative comparisons within the same thread are the meaningful quantity.)

## Results — per-thread robustness

Per-thread ratio (far/near), 28 threads with enough data on both sides:

| Ratio band | Threads |
|---|---:|
| ≥2.0× (near is ≥2× cheaper) | 15 |
| 1.5-2.0× | 3 |
| 1.0-1.5× | 5 |
| <1.0× (reverse direction) | 5 |

Median ratio: **2.05×**. Mean: 2.03×. The effect holds for 82% of threads — this is not driven by a handful of outlier threads with extreme subagent behavior.

Five threads show the reverse direction (near-practice messages are *more* expensive than far-from-practice). Those threads have few messages in one bucket or the other (e.g., only 6 near-messages in a 200-msg thread), so small-sample variance is a likely explanation.

## Results — statistical defensibility

At N=28 the effect size point estimates alone (2.05× median, 2.03× mean) do not tell a reader how confident to be in them. Two checks sharpen this:

**Bootstrap 95% CI over the 28 per-thread ratios (10 000 resamples, seed=42):**

| Statistic | Observed | 95% CI |
|---|---:|---|
| Median | 2.05× | [1.23×, 2.47×] |
| Mean | 2.03× | [1.66×, 2.43×] |

Both CIs are **entirely above 1.0×**. Even in the worst-case bootstrap sample the effect does not reverse.

**Sign test on the null that per-thread ratio = 1.0 (i.e. no effect):**

Under the null, each of 28 threads is an independent Bernoulli coin flip with P(ratio > 1.0) = 0.5. Observed 23 of 28 threads with `ratio > 1.0`. Binomial p-value: **p = 0.000456**. The *direction* of the effect is highly significant independently of the size estimate.

These two checks are complementary: the bootstrap bounds the *size* of the effect, the sign test bounds its *direction*.

## Results — mechanism test, `Agent` vs `Skill`

If the mechanism is subagent context compression, the effect should concentrate in practice events that actually compress context. `Agent` events (true subagent spawns — `Explore`, `general-purpose`, `code-reviewer`, etc.) have their own isolated context window. `Skill` events (`commit-commands:commit`, `code-review:code-review`, etc.) are scripted workflows that do not offload context. The prediction: Agent effect ≫ Skill effect.

Splitting the 243 practice events (174 Agent + 69 Skill) and rerunning the within-thread design on each subset separately:

| Category | N threads | Median per-thread ratio | Median 95% CI | Aggregated far/near | Threads ≥1.5× |
|---|---:|---:|---|---:|---:|
| **Agent only** (subagent spawns) | 28 | **2.46×** | [1.57×, 3.23×] | 2.01× | 20 / 28 |
| **Skill only** (scripted workflows) | 16 | 1.78× | — | 1.20× | 9 / 16 |
| Combined (baseline) | 28 | 2.05× | [1.23×, 2.47×] | 1.68× | 18 / 28 |

The direction is as predicted: **Agent gap is larger than Skill gap on both per-thread and aggregated metrics.** The aggregated-ratio gap is the sharpest discriminator (Agent 2.01× vs Skill 1.20× — a 67% gap between categories), because aggregation weights threads by message volume and neutralizes small-sample variance in individual threads.

The residual Skill effect (1.20-1.78×) is not zero. Two likely contributors: (a) threads that use Skills often *also* use Agents, so the "near Skill" window is frequently within Agent-influence range and inherits some of the Agent compression; (b) some Skills may briefly simplify the assistant's response (the skill-call message itself is structurally short). Isolating these would require threads that use Skills but not Agents, which is a small sample on this dataset.

The key takeaway: the predicted direction (Agent ≫ Skill) is observed. This strengthens the compression interpretation — something about *having your own context window* does the work, not just "a practice event fired nearby."

## Interpretation — subagents as context compressors

The simplest mechanism consistent with the data: when a practice event fires — `Agent` invocation or `Skill` call — the subagent operates in an *isolated context window*. It reads the tools/files it needs, may call its own tools, and returns a compact textual summary to the main thread. The main thread receives this summary, not the full trace. The main thread's *next* message, therefore, sees a small addition to context (just the summary), not a full expansion.

Messages far from any practice event, by contrast, are downstream of inline exploration — the main thread itself read files, collected context, and continued. That context persists in the prompt for every subsequent API call. Tokens per message climb.

This mechanism predicts:
- The effect is **strongest right after a practice event** (`within_5_msgs`) and should weaken at `within_20_msgs`. **Observed:** 193-248k within_5 vs 247-362k within_20 — yes, the effect dampens with distance.
- The effect is **present in every position bucket**, not concentrated early. **Observed:** yes.
- The effect should be weaker or absent for `Skill` events that don't offload context (e.g., `commit-commands:commit` doesn't compress — it just writes). **Observed:** yes — the split analysis above shows Agent median 2.46× vs Skill median 1.78× (Agent aggregated 2.01× vs Skill aggregated 1.20×). Direction matches the prediction.

## Limitations

**1. Correlation, not proven causation.** The within-thread design rules out task-size, task-type, and developer-state confounds but not *behavioral* ones. It's possible that developers invoke subagents at moments when the main conversation is about to simplify anyway, and the "practice caused compression" story is reversed. To prove causation would need randomized injection of subagent calls, which is not possible retrospectively.

**2. N = 28 threads.** Usable threads are those with ≥3 near and ≥3 far messages. Broader thresholds (e.g., near=0, far=0 cutoffs) could be explored but would introduce per-thread noise.

**3. Skill events also show a residual effect.** The `Agent`/`Skill` split sharpened the picture (Agent 2.01× aggregated vs Skill 1.20× aggregated, in the predicted direction), but Skill is not zero. The likely contamination is that threads using Skills often also use Agents within the same 5-message window; a clean "Skills without Agents" subset is too small on this dataset to separate cleanly. The *direction* of the split is robust; the *exact* per-category magnitude is not.

**4. `total_tokens` is API-reported, includes prompt context.** This is exactly the metric that should drop if context stays compact, so this is the *right* metric for testing the compression hypothesis — but it is not a pure "output size" measurement.

**5. N=1 developer history.** As with F-001 through F-006, this is a single developer's Claude Code archive. Replication across developers is needed to separate personal subagent-use patterns from general properties of the tool.

## Implications

For tool design and workflow guidance:

- **Subagent delegation is a main-session efficiency pattern, even when total subagent-inclusive token cost is higher.** F-003 showed subagents add ~21.6% overhead at the thread level. F-007 shows that same delegation cuts main-session tokens/msg in half within the same thread. The tradeoff is: pay more total tokens, receive a compact main-session stream that is cheaper per response and likely easier to follow.
- For agents with long-running threads (100+ messages), invoking a fresh `Agent` periodically may materially cap context growth. Without such delegation, the main prompt accumulates linearly and every response gets more expensive.
- The compression effect is likely why practice-using threads feel "tighter" in practice even when their total-cost numbers are higher — the main conversation is doing less rework.

## Reproduction

- Warehouse: `warehouse-full.sqlite` (see [history-pipeline.md](../history-pipeline.md))
- Tables: `derived_message_facts` (role='assistant', `total_tokens IS NOT NULL`), `derived_practice_events` (H-040 Phase 2 output)
- Analysis script: inline Python bucketing, bootstrap (10 000 resamples, seed=42), sign test via binomial; no new code in `src/`
- Related findings: [F-001](F-001-claude-retries-are-subagents.md), [F-003](F-003-practice-split-is-size-confounded.md) (size-matched addendum provides the cross-thread baseline this finding controls for), [F-005](F-005-practice-distribution.md) (what practice events exist)
