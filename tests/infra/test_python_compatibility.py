"""Checks for compatibility with the project's minimum Python version."""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path


def test_source_parses_with_minimum_supported_python() -> None:
    repo_root = Path(__file__).parents[2]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text())
    requires_python = pyproject["project"]["requires-python"]
    match = re.fullmatch(r">=(\d+)\.(\d+)", requires_python)

    assert match is not None
    feature_version = tuple(int(part) for part in match.groups())

    for source_path in (repo_root / "src").rglob("*.py"):
        ast.parse(
            source_path.read_text(),
            filename=str(source_path.relative_to(repo_root)),
            feature_version=feature_version,
        )
