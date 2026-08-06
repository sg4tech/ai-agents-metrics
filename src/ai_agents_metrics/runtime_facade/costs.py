"""Model-based usage-cost resolution."""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from ai_agents_metrics.domain import (
    round_usd,
    validate_non_negative_int,
)
from ai_agents_metrics.usage.resolution import (
    load_pricing,
    resolve_pricing_model_alias,
)

if TYPE_CHECKING:
    from pathlib import Path



def resolve_usage_costs(
    *,
    pricing_path: Path,
    model: str | None,
    input_tokens: int | None,
    cached_input_tokens: int | None,
    output_tokens: int | None,
    explicit_cost_fields_used: bool,
    explicit_token_fields_used: bool,
) -> tuple[float | None, int | None, int | None, int | None, int | None, str | None]:
    usage_fields_used = any(value is not None for value in (input_tokens, cached_input_tokens, output_tokens))
    if model is None and not usage_fields_used:
        return None, None, None, None, None, None
    if model is None:
        raise ValueError("model is required when usage token flags are provided")
    if not usage_fields_used:
        raise ValueError("At least one usage token field is required when model is provided")
    if explicit_cost_fields_used or explicit_token_fields_used:
        raise ValueError("model-based usage pricing cannot be combined with explicit cost/token flags")

    input_tokens_value = input_tokens or 0
    cached_input_tokens_value = cached_input_tokens or 0
    output_tokens_value = output_tokens or 0
    validate_non_negative_int(input_tokens_value, "input_tokens")
    validate_non_negative_int(cached_input_tokens_value, "cached_input_tokens")
    validate_non_negative_int(output_tokens_value, "output_tokens")

    pricing = load_pricing(pricing_path)
    pricing_model = resolve_pricing_model_alias(model, pricing)
    if pricing_model is None:
        raise ValueError(f"Unknown model: {model!r} — not found in pricing file {pricing_path}")
    model_pricing = pricing[pricing_model]
    cached_rate = model_pricing["cached_input_per_million_usd"]
    if cached_input_tokens_value > 0 and cached_rate is None:
        raise ValueError(f"Model {model} does not support cached input pricing")

    input_cost = Decimal(str(model_pricing["input_per_million_usd"])) * Decimal(input_tokens_value) / Decimal(1_000_000)
    cached_input_cost = Decimal(0)
    if cached_rate is not None:
        cached_input_cost = Decimal(str(cached_rate)) * Decimal(cached_input_tokens_value) / Decimal(1_000_000)
    output_cost = Decimal(str(model_pricing["output_per_million_usd"])) * Decimal(output_tokens_value) / Decimal(1_000_000)
    total_cost = round_usd(input_cost + cached_input_cost + output_cost)
    total_tokens = input_tokens_value + cached_input_tokens_value + output_tokens_value
    return total_cost, total_tokens, input_tokens_value, cached_input_tokens_value, output_tokens_value, model
