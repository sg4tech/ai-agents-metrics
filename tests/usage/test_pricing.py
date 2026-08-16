"""Tests for bundled model pricing."""
from __future__ import annotations

from pathlib import Path

import pytest

from ai_agents_metrics.usage.resolution import default_pricing_path, load_pricing


def test_gpt_5_6_family_uses_official_token_prices() -> None:
    pricing = load_pricing(default_pricing_path())

    expected = {
        "gpt-5.6": {
            "input_per_million_usd": 5.0,
            "cached_input_per_million_usd": 0.5,
            "cache_creation_per_million_usd": 6.25,
            "output_per_million_usd": 30.0,
        },
        "gpt-5.6-sol": {
            "input_per_million_usd": 5.0,
            "cached_input_per_million_usd": 0.5,
            "cache_creation_per_million_usd": 6.25,
            "output_per_million_usd": 30.0,
        },
        "gpt-5.6-terra": {
            "input_per_million_usd": 2.0,
            "cached_input_per_million_usd": 0.2,
            "cache_creation_per_million_usd": 2.5,
            "output_per_million_usd": 12.0,
        },
        "gpt-5.6-luna": {
            "input_per_million_usd": 0.2,
            "cached_input_per_million_usd": 0.02,
            "cache_creation_per_million_usd": 0.25,
            "output_per_million_usd": 1.2,
        },
    }

    assert {model: pricing[model] for model in expected} == expected


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("gpt-5.5", (5.0, 0.5, 30.0)),
        ("gpt-5.5-pro", (30.0, None, 180.0)),
        ("gpt-5.4-pro", (30.0, None, 180.0)),
        ("gpt-5.3-codex", (1.75, 0.175, 14.0)),
    ],
)
def test_current_openai_models_have_official_token_prices(
    model: str,
    expected: tuple[float, float | None, float],
) -> None:
    pricing = load_pricing(default_pricing_path())
    actual = pricing[model]

    assert (
        actual["input_per_million_usd"],
        actual["cached_input_per_million_usd"],
        actual["output_per_million_usd"],
    ) == expected


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("claude-fable-5", (10.0, 1.0, 12.5, 50.0)),
        ("claude-mythos-5", (10.0, 1.0, 12.5, 50.0)),
        ("claude-opus-5", (5.0, 0.5, 6.25, 25.0)),
        ("claude-opus-4-8", (5.0, 0.5, 6.25, 25.0)),
        ("claude-opus-4-5", (5.0, 0.5, 6.25, 25.0)),
        ("claude-sonnet-5", (2.0, 0.2, 2.5, 10.0)),
        ("claude-sonnet-4-5", (3.0, 0.3, 3.75, 15.0)),
    ],
)
def test_current_anthropic_models_have_official_token_prices(
    model: str,
    expected: tuple[float, float, float, float],
) -> None:
    pricing = load_pricing(default_pricing_path())
    actual = pricing[model]

    assert (
        actual["input_per_million_usd"],
        actual["cached_input_per_million_usd"],
        actual["cache_creation_per_million_usd"],
        actual["output_per_million_usd"],
    ) == expected


def test_repository_and_bundled_pricing_files_match() -> None:
    repository_pricing = Path(__file__).parents[2] / "pricing" / "model_pricing.json"

    assert repository_pricing.read_bytes() == default_pricing_path().read_bytes()
