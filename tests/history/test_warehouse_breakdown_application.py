"""Application tests for warehouse breakdown orchestration through fake ports."""

from __future__ import annotations

from pathlib import Path

from ai_agents_metrics.warehouse.application import (
    LoadWarehouseBreakdown,
    WarehouseScope,
    WarehouseState,
)
from ai_agents_metrics.warehouse.domain import (
    BreakdownDimension,
    BreakdownRow,
    BreakdownTokenRecord,
)


class FakeGate:
    def __init__(self, state: WarehouseState) -> None:
        self.state = state

    def resolve(self, warehouse_path: Path, project_cwd: Path) -> WarehouseState:
        return self.state


class FakeQuery:
    def __init__(self, records: list[BreakdownTokenRecord]) -> None:
        self.records = records

    def load_records(
        self, warehouse_path: Path, dimension: BreakdownDimension
    ) -> list[BreakdownTokenRecord]:
        return self.records


class FakeAggregator:
    def __init__(self) -> None:
        self.received: list[BreakdownTokenRecord] = []

    def validate(self, dimension: BreakdownDimension, top: int | None) -> None:
        return None

    def __call__(
        self,
        records: list[BreakdownTokenRecord],
        dimension: BreakdownDimension,
        top: int | None,
    ) -> tuple[BreakdownRow, ...]:
        self.received = records
        return ()


def _record(project_cwd: str) -> BreakdownTokenRecord:
    return BreakdownTokenRecord(
        key="model",
        project_cwd=project_cwd,
        input_tokens=1,
        cache_creation_input_tokens=0,
        cached_input_tokens=0,
        output_tokens=0,
        total_tokens=1,
    )


def test_use_case_filters_records_to_gate_scope() -> None:
    aggregator = FakeAggregator()
    use_case = LoadWarehouseBreakdown(
        FakeGate(WarehouseState.ok(WarehouseScope("/selected", is_all_projects=False))),
        FakeQuery([_record("/selected"), _record("/foreign")]),
        aggregator,
    )

    result = use_case(
        Path("warehouse.db"), Path("/selected"), BreakdownDimension.MODEL, top=1
    )

    assert aggregator.received == [_record("/selected")]
    assert result.scope == WarehouseScope("/selected", is_all_projects=False)
    assert result.rows == ()


def test_use_case_preserves_all_project_records() -> None:
    aggregator = FakeAggregator()
    records = [_record("/first"), _record("/second")]
    use_case = LoadWarehouseBreakdown(
        FakeGate(WarehouseState.ok(WarehouseScope("/missing", is_all_projects=True))),
        FakeQuery(records),
        aggregator,
    )

    use_case(Path("warehouse.db"), Path("/missing"), BreakdownDimension.PROJECT, top=None)

    assert aggregator.received == records
