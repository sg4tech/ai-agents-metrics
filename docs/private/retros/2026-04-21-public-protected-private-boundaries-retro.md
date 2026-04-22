# Retro: public / protected / private boundaries were implicit instead of enforced

**Date:** 2026-04-21

## Situation

We revisited a sequence of architecture fixes around pricing resolution and command runtime wiring:

- `render-html` was reading bundled pricing directly instead of using the workspace-aware pricing resolution path.
- `pricing_runtime.py` was extracted to create one sanctioned application-level pricing entrypoint.
- `runtime_facade.py` was then extracted so `commands.py` no longer depends on `cli.py` as a broad re-export container.

This led to a deeper question: how well had we actually been using `public`, `protected`, and `private` boundaries in this codebase, and why were they not applied correctly from the start?

## What Happened

The codebase had partial boundary signals, but not a complete boundary model.

What was reasonably good already:

- low-level helpers often used `_private` naming
- recent fixes introduced a clearer application-layer entrypoint for pricing
- `CommandRuntime` already existed as a protocol seam for command handlers

What was still wrong:

- `cli.py` acted as both the CLI entrypoint and a large service-locator-style runtime surface
- runtime consumers could choose between multiple pricing-loading paths
- tests often patched convenient module-level exports rather than a clearly sanctioned runtime API
- the term `protected` existed mostly as an architectural intuition, not as an explicit code boundary

In practice, we had:

- some real `private` internals
- some real `public` entrypoints
- a large ambiguous middle that was treated as “kind of public, but please do not use it that way”

That ambiguous middle is where the bug came from.

## Root Cause

The real root cause was not “one wrong import” or “one missed refactor.”

The real root cause was that the codebase did not encode boundary intent strongly enough in module structure.

We had reusable primitives, but not one clearly sanctioned application-level surface for all runtime consumers. As a result, developers and agents could still make local choices that looked reasonable:

- import the bundled constant directly
- call the low-level loader directly
- patch `cli.py` because it already exports everything

Those choices were individually understandable and collectively harmful.

## 5 Whys: Why were public / protected / private used incorrectly?

1. **Why did `render-html` and other consumers drift from the intended pricing contract?**  
   Because multiple modules exposed overlapping ways to load pricing and runtime helpers.

2. **Why were multiple overlapping access paths available?**  
   Because the codebase had low-level primitives and convenience re-exports, but not one clearly mandatory application-layer gateway.

3. **Why was there no clearly mandatory gateway?**  
   Because earlier refactors improved local structure without fully converting boundary intent into module boundaries and sanctioned imports.

4. **Why did those earlier refactors stop short of that boundary conversion?**  
   Because the local objective was usually “fix the current behavior safely” rather than “formalize the full visibility model.”

5. **Why was that local objective allowed to dominate repeatedly?**  
   Because the bottleneck was not identified explicitly enough: the main constraint was architectural ambiguity, not implementation effort.

## 5 Whys: Why did I not use the boundaries correctly immediately?

1. **Why did I not jump straight to the final public/protected/private split?**  
   Because I started from the immediate symptom and chose the smallest safe fix path first.

2. **Why did I choose the smallest safe fix path first?**  
   Because this repository values compatibility, reversible changes, and preserving working imports during refactors.

3. **Why did that still lead to delayed boundary cleanup?**  
   Because I accepted the existing module layout as more legitimate than it really was and initially optimized around it instead of challenging it.

4. **Why did I accept the existing module layout too readily?**  
   Because `cli.py` already functioned as the runtime surface in tests and command dispatch, so the architectural smell was easy to normalize.

5. **Why is that important to admit?**  
   Because the miss was not only in the codebase; it was also in my judgment. I should have escalated earlier from “fix the bug” to “the boundary model itself is the bug” once the pattern repeated.

## Theory of Constraints

The system bottleneck was not lack of implementation capacity.

The bottleneck was **boundary ambiguity**:

- developers could not tell at a glance which imports were sanctioned for runtime use
- tests reinforced convenience imports instead of boundary imports
- the code allowed several “almost right” paths instead of one obviously correct path

Once that bottleneck existed, more local fixes only reduced symptoms. They did not remove the throughput constraint.

The highest-leverage fix was therefore not “one more bug fix,” but “make the sanctioned runtime boundary unmistakable.”

## Assessment: How right or wrong was the previous usage?

### What was right

- Using `_private` helpers for obvious implementation details was correct.
- Extracting `pricing_runtime.py` was a correct move toward a public application API.
- Keeping compatibility while refactoring was the right default for this repository.

### What was wrong

- Treating `cli.py` as both entrypoint and reusable runtime API was wrong.
- Relying on “team convention” for the middle layer was too weak.
- Using the idea of `protected` without a concrete module boundary made it effectively unenforceable.
- Allowing tests to patch convenience exports instead of sanctioned surfaces made the architecture harder to stabilize.

### Most important nuance

The previous usage was not “totally wrong.” It was **partially right but under-specified**.

That is why it survived for a while: it was good enough to function, but not explicit enough to prevent drift.

## Permanent Changes

- Extracted `pricing_runtime.py` as the sanctioned pricing runtime API.
- Extracted `runtime_facade.py` as the sanctioned runtime surface for `commands.py`.
- Switched command dispatch to use `runtime_facade` instead of `cli.py` as the runtime object.
- Added regression coverage that pins the `main() -> runtime_facade` dispatch contract.
- Updated fake runtimes and subprocess fixtures so tests align with the explicit boundary instead of ambient convenience.

## Classification of Follow-up

| Follow-up | Scope | Decision |
| --- | --- | --- |
| Keep `runtime_facade.py` as the only sanctioned runtime surface for command handlers | code / architecture | **done** |
| Keep `pricing_runtime.py` as the only sanctioned application pricing API | code / architecture | **done** |
| Continue reducing direct runtime re-export use from `cli.py` | code / architecture | **deferred** |
| Add a reusable rule: when introducing a “protected” layer, encode it as a module boundary rather than convention only | local `AGENTS.md` candidate | **deferred** |
| Treat repeated convenience-import patching in tests as an architecture smell | tests / review practice | **done in practice**, not yet promoted to policy |
| This retrospective | retrospective only | **done** |

## Conclusions

The most honest summary is:

- we were not using `public / protected / private` badly everywhere
- we were using them too informally where precision mattered most
- I initially followed the existing shape of the code too closely
- the user push on root cause was correct and high leverage

The lesson is not “refactor more aggressively by default.”

The lesson is:

> when a layer is described as sanctioned, protected, or internal, the code should make that visible without requiring memory, convention, or chat context.

