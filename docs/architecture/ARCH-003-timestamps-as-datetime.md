# ARCH-003: Store timestamps as datetime in dataclasses

**Priority:** medium
**Complexity:** medium
**Status:** open

## Problem

`GoalRecord` and `AttemptEntryRecord` store timestamps as strings:

```python
@dataclass
class GoalRecord:
    started_at: str | None
    finished_at: str | None
```

Consequences:
- Parsing (`parse_iso_datetime`, `parse_iso_datetime_flexible`) is scattered throughout the codebase
- Two separate parsing functions exist instead of one — because the input format is not normalised at the boundary
- Timezone errors surface at runtime; mypy cannot catch them
- Date arithmetic requires parsing first rather than using native datetime operations

## Desired state

- Inside dataclasses: `started_at: datetime | None`
- String → datetime conversion happens only in `serde.py` when reading from JSON
- datetime → string conversion happens only in `serde.py` when writing to JSON
- All domain and aggregation code uses native `datetime` operations

## Acceptance criteria

- [ ] `GoalRecord.started_at` and `finished_at` are typed as `datetime | None`
- [ ] Same for `AttemptEntryRecord`
- [ ] `parse_iso_datetime_flexible` is used in exactly one place (the serde layer)
- [ ] mypy passes without new `# type: ignore` suppressions on datetime code
- [ ] `make verify` passes

## Notes

- Best done after ARCH-002 (dedicated serde.py needed); otherwise changes scatter across all of domain.py
- Audit all places where `started_at` flows into JSON output — each will need `.isoformat()`
