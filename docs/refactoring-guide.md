# Architectural Refactoring Guide

**Purpose:** Prevent large-file splits from moving mixed responsibilities into smaller files
without correcting ownership and dependency boundaries.

**Use this guide when:** A task splits a large file or package, extracts a subsystem, moves a
cluster of functions, or claims to resolve structural or architectural debt.

## Core rule

A smaller file is not evidence of architectural improvement. A refactor improves architecture
only when every reason to change has one explicit owner and dependencies point from outer layers
toward inner layers.

Do not group functions merely because they are adjacent or serve the same CLI command. Assign
them according to the responsibility they own.

## Owner vocabulary

| Owner | Owns | Must not own |
|---|---|---|
| Controller | Input parsing, use-case invocation, final delivery side effect | Business rules, SQL, persistence mapping |
| Use case | Application workflow and coordination of domain behavior | Concrete infrastructure, raw external records |
| Domain service | Pure business rules and transformations | Filesystem, database, network, CLI behavior |
| Port | Typed capability required by an inner layer | Concrete implementation details |
| Adapter | I/O, external schema knowledge, raw-record mapping | Application policy or cross-use-case orchestration |
| Presenter | Conversion of typed results into a user-facing representation | Persistence queries or business decisions |
| Composition root | Construction and wiring of concrete implementations | Business rules or data transformation |

## Mandatory preflight

Complete this table before editing implementation:

| Responsibility | Current location | Reason to change | Target owner | Typed boundary | Public test surface |
|---|---|---|---|---|---|
| `<behavior>` | `<module>` | `<independent change driver>` | `<owner>` | `<request/result/port>` | `<test module and public symbol>` |

Then write the intended dependency graph:

```text
controller
    -> typed application request
use case
    -> port
adapter

composition root
    -> use case + concrete adapters
```

List forbidden edges explicitly. Typical examples are:

```text
controller -X-> database adapter
application -X-> concrete adapter
domain -X-> I/O
adapter -X-> controller
presenter -X-> repository
```

### Stop conditions

Do not begin the split when any of these is true:

- A responsibility has no single target owner.
- Two target modules own the same rule or transformation.
- The direction of an import is unresolved.
- Raw external data would cross into application or domain logic.
- The only stated completion condition is file size or line count.
- The tests cannot be assigned to one public layer surface.

Resolve the design first or narrow the task to a safe preparatory change.

## Implementation order

1. Define typed request, result, value-object, and port contracts.
2. Add application tests using typed fakes for the ports.
3. Move pure domain and application behavior behind those contracts.
4. Implement adapters that map raw external data into typed boundary objects.
5. Add adapter tests against temporary or in-memory infrastructure.
6. Add the composition root that wires concrete adapters to the use case.
7. Reduce controllers to parsing, invocation, final output, and status rendering.
8. Add import-linter contracts for enforceable dependency directions.
9. Preserve or deliberately migrate public imports and compatibility surfaces.
10. Run the complete verification gate.

Ports precede adapters. Creating a concrete adapter first and calling it from existing outer
layers establishes the adapter as a de facto public dependency and recreates the coupling the
refactor is intended to remove.

## Test ownership

Follow the detailed matrix in [testing-guide.md](testing-guide.md#testing-architectural-boundaries).
Each test module imports the public surface of the layer it tests.

The boundary is wrong when:

- a controller test needs a database;
- an application test instantiates a concrete adapter;
- an adapter test asserts console or presentation text;
- a domain test needs mocks for I/O;
- a test imports a private helper from another layer;
- a typed fake requires `type: ignore` to satisfy the consumer.

## Post-refactor audit

Repeat the responsibility inventory for every resulting module:

| Resulting module | Single owner | Reason to change | Allowed imports | Public test |
|---|---|---|---|---|
| `<module>` | `<owner>` | `<one change driver>` | `<inner layers or ports>` | `<test>` |

Search the resulting tree for the old responsibility markers, including I/O imports, schema or
table names, raw record aliases, duplicated transformations, and private-helper imports. The
search must show that each responsibility has one canonical home.

## Acceptance checklist

- [ ] Every responsibility has exactly one owner.
- [ ] Every resulting module has one reason to change.
- [ ] Typed objects cross application boundaries.
- [ ] Raw external data is normalized inside an adapter.
- [ ] Application and domain code do not import concrete infrastructure.
- [ ] Composition happens in one explicit composition root.
- [ ] Controllers contain no business, persistence, or mapping logic.
- [ ] Tests target the public surface of exactly one layer.
- [ ] Enforceable dependency directions have import-linter contracts.
- [ ] Compatibility surfaces are preserved or intentionally migrated.
- [ ] The post-refactor inventory has been completed.
- [ ] The complete verification gate passes.

## Structural split versus architectural split

A structural split relocates code into smaller files while preserving responsibility ownership
and dependencies. It can be useful, but it must be described as structural work.

An architectural split changes ownership, introduces explicit boundaries, and makes invalid
dependencies harder or impossible. Do not claim that architectural debt is resolved when only a
structural split was performed.
