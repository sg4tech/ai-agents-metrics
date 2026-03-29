# High-Level Task Commands Policy Gap Retrospective

## Situation

We added `start-task`, `continue-task`, and `finish-task` to make the metrics workflow easier for agents to follow.

The commands were implemented, tested, and documented in the README, but the main agent-facing instruction path still did not mention them.

The user correctly pointed out that an agent would not reliably discover the new commands from the places that actually govern agent behavior.

## What Happened

The implementation work focused on:

- adding the high-level commands
- proving that they worked
- documenting them in the README

That part succeeded.

But the agent-facing contract still lived primarily in:

- `AGENTS.md`
- `docs/codex-metrics-policy.md`

And those files were not updated in the same pass.

As a result, the product surface improved, but the operational guidance did not improve at the same time.

## Root Cause

The rollout path treated README updates as sufficient documentation for a CLI feature that mainly exists to guide agent behavior.

That was the wrong documentation tier.

For this tool, the critical question is not “is the feature documented somewhere?” The critical question is “does the agent-facing policy now recommend the new path?”

Without that check, it is easy to ship a better workflow that agents still do not naturally use.

## Retrospective

This is a distribution-of-instructions bug.

The feature itself was good. The gap was in where the instructions landed.

For `codex-metrics`, the right order of importance is:

1. `AGENTS.md`
2. `docs/codex-metrics-policy.md`
3. CLI help
4. README

If a workflow change is meant to change how agents behave, then updating only the lower-priority surfaces is incomplete.

## Conclusions

- Agent-facing workflow changes must be documented in the agent-facing policy, not only in README/help.
- README is useful for humans, but it is not the primary operating contract for agents.
- High-level convenience commands should be reflected in the recommended workflow as soon as they become the preferred path.

## Permanent Changes

- Keep the compact policy, but include a short `Recommended Commands` section for the preferred workflow.
- When adding new workflow-shaping CLI commands, update:
  - policy
  - packaged policy mirror
  - tests that validate exported scaffold content
- Treat README-only documentation as insufficient for agent-behavior changes.
