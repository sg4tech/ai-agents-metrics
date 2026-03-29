# Retro Output Classification Retrospective

## Situation

We wrote a retrospective after the bootstrap QA hardening work and correctly identified useful improvements.

However, the follow-through was incomplete: the improvements were not automatically classified by scope, and at least one of them was pushed into the reusable external policy even though it belonged only to local repository development rules.

The user had to call this out explicitly and ask for the scope to be corrected.

## What Happened

The retrospective did produce good conclusions, but the execution loop after the retrospective was too loose.

Instead of explicitly deciding where each improvement should live, the flow effectively treated “this sounds useful” as enough reason to codify it.

That created two problems:

1. Improvements were not translated into the right permanent layer automatically.
2. The user had to spend additional attention correcting something the retrospective process should have handled on its own.

## Root Cause

The retrospective workflow lacked an explicit output-classification step.

We had:

- incident analysis
- conclusions
- permanent changes

But we did not require a final decision for each proposed change:

- local `AGENTS.md`
- reusable external policy
- tests/code guardrails
- retrospective only
- no action

Without that decision gate, the process drifted toward over-codifying.

## Retrospective

This is a process bug, not just a wording mistake.

The point of a retrospective is not only to produce insights. It is to turn those insights into the right kind of improvement with the right scope.

If the scope classification is missing, the retrospective can still feel productive while leaving two bad outcomes:

- important changes do not get applied automatically
- inappropriate changes get applied to the wrong layer

That is exactly what happened here.

## Conclusions

- Retros need an explicit “output classification” step before any rule or policy change is written.
- Not every lesson belongs in a reusable external policy.
- Local development lessons should default to `AGENTS.md`, tests, or code guardrails unless there is a clear reason to generalize them.
- A retrospective is not complete when conclusions exist; it is complete when the conclusions are correctly mapped to their durable destination.

## Permanent Changes

- Add a local rule that every retrospective with proposed improvements must classify each improvement before codifying it.
- Use the following buckets:
  - local `AGENTS.md`
  - reusable external policy
  - tests or code guardrails
  - retrospective only
  - no action
- Default to the narrowest correct scope.
- Do not promote a lesson into reusable policy unless it is actually reusable beyond this repository's local development workflow.
