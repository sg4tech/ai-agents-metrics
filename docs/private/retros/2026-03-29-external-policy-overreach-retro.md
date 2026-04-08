# External Policy Overreach Retrospective

## Situation

After the bootstrap QA hardening work, useful lessons were extracted and we started codifying them.

During that follow-through, a local repository-development lesson was temporarily written into the reusable external policy document instead of staying in local repository rules.

The user had to explicitly point out that this was the wrong scope.

## What Happened

The lesson was real:

- bootstrap or initializer commands need stronger validation than an ordinary local helper
- they should be checked for reruns, partial scaffold states, conflict handling, `--dry-run`, and real installed entrypoints

But the first codification step placed that lesson into `docs/codex-metrics-policy.md`, even though the policy is meant to stay reusable for external consumers and not absorb every local development workflow lesson from this repository.

The result was overreach:

- the content itself was useful
- the destination was wrong

## Root Cause

The problem was not lack of insight. The problem was lack of scope discipline after the retrospective.

We did not apply an explicit gate like:

1. Is this lesson reusable outside this repository?
2. Or is it only a local engineering rule for how we build and validate this repo?

Without that gate, useful local guidance drifted upward into external policy.

## Retrospective

This matters because external policy carries a different promise than local `AGENTS.md`.

- External policy should be stable, reusable, and intentionally generalized.
- Local `AGENTS.md` can and should capture repository-specific development guardrails.

If those layers blur, two bad things happen:

1. The external policy gets heavier and less reusable.
2. The user must manually correct scope mistakes that the process should catch automatically.

## Conclusions

- A good improvement can still be codified incorrectly if its destination is not classified.
- External policy changes need a stricter bar than local repo-rule changes.
- Local engineering lessons should default to local rules unless reusability is explicit and justified.

## Permanent Changes

- Treat reusable external policy as opt-in, not default.
- Before editing external policy after a retrospective, explicitly answer: “Is this genuinely reusable outside this repository?”
- If that answer is not clearly yes, keep the lesson in local `AGENTS.md`, tests, code guardrails, or retrospective history instead.
- Preserve an incident record when this scope boundary is crossed incorrectly, so future reviewers can spot the pattern faster.
