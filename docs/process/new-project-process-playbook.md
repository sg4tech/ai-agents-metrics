# New Project Process Playbook

Use this file as a lightweight operating model for AI-assisted development on a new project.

The purpose is to reduce:

- wrong problem selection
- adjacent implementation
- unclear ownership
- hidden acceptance criteria
- expensive rework

This is a process playbook, not an engineering coding standard.

## Core Principle

Development should start from a clarified task, not from a raw request.

That means:

- product intent is clarified first
- technical scope is clarified second
- implementation starts only after a lead-owned task exists

## Roles

One person may temporarily play multiple roles.

What matters is that the responsibilities stay distinct.

### PM

Responsible for:

- clarifying what outcome is wanted
- clarifying who it is for
- clarifying why it matters
- clarifying what acceptance means

PM should answer:

- who is the user
- what is the job to be done
- what outcome is wanted
- what is the pain today
- what is out of scope
- what makes the result accepted

### Team Lead

Responsible for:

- translating the clarified outcome into an executable task
- narrowing scope
- choosing the next stage
- deciding what the implementer should do now
- rejecting adjacent work that is not the requested outcome

The lead is the orchestration point between intent and implementation.

### Developer

Responsible for:

- implementing the current task
- staying inside the agreed scope
- reporting blockers and uncertainties clearly
- not silently redefining the problem

The developer should work from the lead-owned task, not directly from drifting conversation context.

### QA / Reviewer

Responsible for:

- verifying that the change actually works
- checking regressions and missing cases
- checking whether the delivered result matches the requested outcome

### Demo / Client Acceptance

Responsible for:

- confirming whether the result is actually acceptable
- surfacing “technically done but not what was wanted”

### Retro

Responsible for:

- capturing what failed
- capturing what worked
- classifying follow-up action

## Delivery Flow

Preferred flow:

1. PM discovery
2. lead analysis and task creation
3. implementation
4. code review
5. QA
6. demo / acceptance
7. retrospective

Small tasks may move quickly through these stages.

The point is not ceremony.

The point is to stop mixing all modes of work at once.

## PM Discovery Checklist

Before development starts, answer:

- Who is the primary user?
- What job is the user trying to get done?
- What exact outcome is wanted?
- What pain exists now?
- What would count as success?
- What is explicitly out of scope?
- What tradeoff matters most:
  - quality
  - speed
  - cost

If these are unclear, implementation should not begin yet.

## Lead Task Creation Checklist

Before handing work to development, the lead should produce a task with:

- task title
- requested outcome
- why this task exists
- in-scope work
- out-of-scope work
- constraints
- acceptance criteria
- current stage
- next expected deliverable

Minimal task template:

```md
Title:

Requested outcome:

Why this matters:

Scope:

Out of scope:

Constraints:

Acceptance criteria:

Current stage:

Next deliverable:
```

## Rules For Developers

- Do not start from raw user chat if a clarified task is missing.
- Do not silently redefine the task.
- Do not replace the requested outcome with adjacent technical work.
- Raise ambiguity early.
- If the task needs to change, hand it back to the lead instead of quietly changing scope.

## Rules For Lead-Mediated Development

- The lead owns stage transitions.
- The developer executes the current stage.
- Acceptance is explicit, not implied.
- Rework should be visible.
- If a task outcome changes materially, create a new task or linked continuation instead of pretending it was the same task all along.

## What To Watch For

These are signals the process is working:

- fewer “we solved the wrong problem” incidents
- fewer adjacent implementations
- easier acceptance decisions
- clearer handoffs
- cleaner retrospectives

These are signals the process is becoming too heavy:

- lots of task writing with little delivery value
- repeated bureaucracy on tiny obvious fixes
- lead becoming a bottleneck without improving clarity
- stage labels existing only on paper and not helping decisions

## Recommended Adoption

Do not force the full process on day one.

Recommended rollout:

1. Use PM discovery checklist.
2. Have the lead create explicit tasks before implementation.
3. Use the delivery flow manually on 2-5 real tasks.
4. Keep what clearly improves quality and clarity.
5. Automate only after the manual flow proves useful.

## Key Rule

The system should optimize for:

- clarified intent first
- implementation second

If that order is reversed, the team will often produce technically competent work that still misses the requested outcome.
