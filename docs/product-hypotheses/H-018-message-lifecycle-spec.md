# Feature Spec: Message-Level Task-Lifecycle Recommendations From Historical Conversations

## Status

- Draft date: `2026-04-03`
- Owner: `product / metrics`
- Intended audience: `development team`
- Related hypothesis: [H-018](/Users/viktor/PycharmProjects/codex-metrics/docs/product-hypotheses/H-018.md)

## Problem

`codex-metrics` can already reconstruct historical conversations and analyze them by segment, but that is still one step removed from the workflow decision that often matters most:

- should this stretch of conversation continue the current task
- should it start a new task
- should it close the current task
- should it reopen a task that was closed too early

Without an explicit recommendation layer, a human or agent still has to infer task-boundary intent manually from the transcript.

That creates a gap between:

- retrospective analysis of what happened
- and operational guidance about which task command should have been used

## Goal

Build a conservative historical analysis layer that reads conversation text and emits a suggested task-lifecycle action for each message or short window of messages.

The first version should support at least:

- `continue`
- `start-new-task`
- `close-task`
- `reopen-task`
- `uncertain`

The output should help an analyzing agent answer:

1. where the conversation clearly stayed inside one task
2. where the conversation drifted into a new task boundary
3. where the work should have been closed earlier
4. where a previously closed task should have been reopened instead of treated as a fresh task

## Non-Goals

This feature should not:

- automatically mutate `metrics/codex_metrics.json`
- replace human judgment for ambiguous cases
- require provider-specific public commands or telemetry surfaces
- guess lifecycle intent when the transcript evidence is weak
- solve the full segmentation problem before the recommendation problem is understood

## Product Intent

The product should help agents move from:

- "this conversation looks messy"

to:

- "this message probably means continue the current task"
- "this stretch should likely have started a new task"
- "this looks like a close boundary"
- "this looks like a reopen boundary"

That makes the history layer more actionable, because it can point to a concrete workflow decision instead of only describing efficiency or outcome quality.

The public contract must remain agent-agnostic.

## Scope

In scope for the first implementation:

- read historical transcript text from the existing history pipeline
- score each message or short message window with a lifecycle label
- attach a confidence or uncertainty signal
- preserve enough supporting text to make the recommendation reviewable
- keep the output read-only and analysis-oriented
- add tests around stable label output and conservative rejection of weak cases

Out of scope for the first implementation:

- automatic task creation or closure
- live chat interception
- provider-specific UI or agent-specific public commands
- full conversation understanding
- retraining a custom model before a narrow heuristic baseline exists

## Target User

Primary user:

- AI agents that analyze metrics and workflow history

Secondary user:

- the human sponsor who receives the synthesized conclusion later

Why this is useful:

- the agent can point to the exact moment a task boundary looked wrong
- the recommendation layer can surface recurring boundary mistakes across histories
- the output can be used to compare manual task classification against transcript-derived suggestions

## Recommendation Model

### Labels

Use a small label set first:

- `continue`
- `start-new-task`
- `close-task`
- `reopen-task`
- `uncertain`

### Output Shape

Each scored unit should ideally include:

- the message or window identifier
- the suggested label
- a confidence or strength score
- a short rationale
- the source text span used to make the suggestion

### Conservative Rule

If the evidence is weak, choose `uncertain` rather than forcing a boundary label.

This is important because false-positive lifecycle recommendations are worse than a small amount of missed opportunity in the first pass.

### Recommended Operating Principle

Prefer:

- fewer, more defensible boundary calls

over:

- many shaky labels that look precise but are not trustworthy

## Functional Requirements

### 1. Historical input

The feature should consume the transcript history already reconstructed by the history pipeline.

It should work on:

- full conversations
- phase-segmented windows
- shorter message windows around candidate boundaries

### 2. Lifecycle classification

For each target unit, the system should emit one recommended lifecycle label.

The classifier should be able to distinguish at least:

- continuation inside the same task
- task boundary introduction
- task closure language
- task reopening or correction of a prior closure
- ambiguous or insufficient evidence

### 3. Reviewable evidence

Every recommendation should remain explainable enough for retrospective review.

At minimum, the analysis output should preserve:

- the local text span that triggered the suggestion
- the label
- the confidence or uncertainty level

### 4. Boundary comparison

The output should be comparable against manual retrospective judgment.

That means the feature should support:

- spot-checking against human boundary review
- counting likely true positives, false positives, and uncertain cases
- comparing lifecycle suggestions across different task types or phase segments

### 5. Read-only behavior

The feature must not mutate the ledger automatically.

It should only produce analysis output that can inform later decisions about:

- whether a task should be started
- whether an existing task should be closed
- whether a closed task should be reopened

## Suggested Analysis Strategy

### Stage 1: Conservative heuristic baseline

Start with a narrow, rule-friendly baseline if possible.

Good first signals may include:

- explicit phrases about starting, continuing, closing, or reopening work
- task-boundary language around scope changes
- evidence of user correction or task pivot
- closure language followed by clear continuation of the same problem

### Stage 2: Windowed scoring

Score short windows around each candidate boundary instead of scoring the whole conversation as one opaque unit.

This should help keep the recommendation localized and reviewable.

### Stage 3: Segment alignment

Align the lifecycle labels with the existing phase segmentation work from H-018 so the analysis can explain both:

- what phase the conversation is in
- what lifecycle action that phase suggests

## Validation Requirements

At minimum, add or update automated tests for:

1. stable label emission for simple boundary cases
2. conservative `uncertain` behavior on weak evidence
3. reviewable output shape with text spans and rationale
4. read-only behavior with no mutation of the metrics ledger
5. comparison against a small manually reviewed sample

## Acceptance Criteria

The feature is useful when:

1. historical transcript windows can be labeled with a lifecycle recommendation
2. ambiguous cases are left as `uncertain` instead of guessed
3. the output is reviewable by an agent without raw transcript spelunking
4. the recommendation layer helps identify task-boundary mistakes earlier than final outcome review alone
5. the feature stays read-only and agent-agnostic

## Risks

- transcripts may be too ambiguous for reliable boundary classification
- a naive classifier may over-suggest boundary changes
- lifecycle labels can become a false sense of precision if confidence is not handled carefully
- the feature may add complexity without enough decision value unless it stays narrow

## Guardrails

- prefer `uncertain` when the transcript is not explicit
- keep the output read-only
- keep the public contract universal
- do not replace human judgment for boundary decisions
- keep the label set small until evidence justifies expansion

## Open Questions For Implementation

- whether the first output should be per-message or per-short-window
- whether confidence should be numeric, ordinal, or both
- whether the first baseline should be purely heuristic or LLM-assisted on top of segmentation
- how much rationale text is enough to make a recommendation reviewable without turning it into a noisy report
