"""Small shared primitives used by the history and usage pipelines."""
from decimal import ROUND_HALF_UP, Decimal

from ai_agents_metrics.domain.time_utils import (
    now_utc_datetime,
    now_utc_iso,
    parse_iso_datetime,
    parse_iso_datetime_flexible,
)


def round_usd(value: Decimal | float) -> float:
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    return float(decimal_value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def validate_non_negative_int(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")


__all__ = [
    "now_utc_datetime",
    "now_utc_iso",
    "parse_iso_datetime",
    "parse_iso_datetime_flexible",
    "round_usd",
    "validate_non_negative_int",
]
