"""Pure token-breakdown value objects and aggregation rules."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum


class BreakdownDimension(StrEnum):
    MODEL = "model"
    PROJECT = "project"
    CATEGORY = "token-type"


@dataclass(frozen=True)
class BreakdownTokenRecord:
    key: str
    project_cwd: str
    input_tokens: int | None
    cache_creation_input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


@dataclass(frozen=True)
class BreakdownRow:
    key: str
    input_tokens: int | None
    cache_creation_input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    share_of_total: float
    grouped_row_count: int = 1
    is_remainder: bool = False


class BreakdownAggregator:
    def __call__(
        self,
        records: list[BreakdownTokenRecord],
        dimension: BreakdownDimension,
        top: int | None,
    ) -> tuple[BreakdownRow, ...]:
        self.validate(dimension, top)
        rows = self._aggregate_records(records)
        if dimension is BreakdownDimension.CATEGORY:
            rows = self._token_type_rows(rows)
        rows = self._with_shares(rows)
        if top is not None:
            rows = self._apply_top(rows, top)
        return tuple(rows)

    @staticmethod
    def validate(dimension: BreakdownDimension, top: int | None) -> None:
        if top is not None and top <= 0:
            raise ValueError("--top must be a positive integer")
        if dimension is BreakdownDimension.CATEGORY and top is not None:
            raise ValueError("--top is not supported with --by token-type")

    @classmethod
    def _aggregate_records(cls, records: list[BreakdownTokenRecord]) -> list[BreakdownRow]:
        grouped: dict[str, list[BreakdownTokenRecord]] = {}
        for record in records:
            grouped.setdefault(record.key, []).append(record)
        return sorted(
            (
                BreakdownRow(
                    key=key,
                    input_tokens=cls._sum_optional([record.input_tokens for record in group]),
                    cache_creation_input_tokens=cls._sum_optional(
                        [record.cache_creation_input_tokens for record in group]
                    ),
                    cached_input_tokens=cls._sum_optional(
                        [record.cached_input_tokens for record in group]
                    ),
                    output_tokens=cls._sum_optional([record.output_tokens for record in group]),
                    total_tokens=cls._sum_optional([record.total_tokens for record in group]),
                    share_of_total=0.0,
                )
                for key, group in grouped.items()
            ),
            key=lambda row: (-(row.total_tokens or 0), row.key),
        )

    @classmethod
    def _token_type_rows(cls, rows: list[BreakdownRow]) -> list[BreakdownRow]:
        totals = cls._total_row(rows)
        token_rows = [
            cls._category_row("input", totals.input_tokens),
            cls._category_row("cache_creation", totals.cache_creation_input_tokens),
            cls._category_row("cached", totals.cached_input_tokens),
            cls._category_row("output", totals.output_tokens),
        ]
        return sorted(token_rows, key=lambda row: (-(row.total_tokens or 0), row.key))

    @classmethod
    def _total_row(cls, rows: list[BreakdownRow]) -> BreakdownRow:
        return BreakdownRow(
            key="totals",
            input_tokens=cls._sum_optional([row.input_tokens for row in rows]),
            cache_creation_input_tokens=cls._sum_optional(
                [row.cache_creation_input_tokens for row in rows]
            ),
            cached_input_tokens=cls._sum_optional([row.cached_input_tokens for row in rows]),
            output_tokens=cls._sum_optional([row.output_tokens for row in rows]),
            total_tokens=cls._sum_optional([row.total_tokens for row in rows]),
            share_of_total=0.0,
        )

    @staticmethod
    def _category_row(key: str, value: int | None) -> BreakdownRow:
        return BreakdownRow(
            key=key,
            input_tokens=value if key == "input" else None,
            cache_creation_input_tokens=value if key == "cache_creation" else None,
            cached_input_tokens=value if key == "cached" else None,
            output_tokens=value if key == "output" else None,
            total_tokens=value,
            share_of_total=0.0,
        )

    @staticmethod
    def _with_shares(rows: list[BreakdownRow]) -> list[BreakdownRow]:
        grand_total = sum(row.total_tokens or 0 for row in rows)
        return [
            replace(
                row,
                share_of_total=((row.total_tokens or 0) / grand_total if grand_total else 0.0),
            )
            for row in rows
        ]

    @classmethod
    def _apply_top(cls, rows: list[BreakdownRow], top: int) -> list[BreakdownRow]:
        if len(rows) <= top:
            return rows
        visible = rows[:top]
        hidden = rows[top:]
        remainder = BreakdownRow(
            key="other",
            input_tokens=cls._sum_optional([row.input_tokens for row in hidden]),
            cache_creation_input_tokens=cls._sum_optional(
                [row.cache_creation_input_tokens for row in hidden]
            ),
            cached_input_tokens=cls._sum_optional([row.cached_input_tokens for row in hidden]),
            output_tokens=cls._sum_optional([row.output_tokens for row in hidden]),
            total_tokens=cls._sum_optional([row.total_tokens for row in hidden]),
            share_of_total=sum(row.share_of_total for row in hidden),
            grouped_row_count=len(hidden),
            is_remainder=True,
        )
        return [*visible, remainder]

    @staticmethod
    def _sum_optional(values: list[int | None]) -> int | None:
        known_values = [value for value in values if value is not None]
        return sum(known_values) if known_values else None
