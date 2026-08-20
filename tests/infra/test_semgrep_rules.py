"""Regression tests for project-specific Semgrep architecture rules."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import certifi
import pytest


@pytest.mark.timeout(15)
def test_layer_boundary_rules_detect_incident_patterns() -> None:
    repo_root = Path(__file__).parents[2]
    fixture_root = repo_root / "tests/fixtures/semgrep"
    environment = os.environ.copy()
    environment.update(
        {
            "SSL_CERT_FILE": certifi.where(),
            "SEMGREP_LOG_FILE": "/tmp/ai-agents-metrics-semgrep-test.log",
            "SEMGREP_SETTINGS_FILE": "/tmp/ai-agents-metrics-semgrep-test-settings.yml",
            "SEMGREP_VERSION_CACHE_PATH": "/tmp/ai-agents-metrics-semgrep-test-version-cache",
        }
    )
    completed = subprocess.run(
        [
            str(repo_root / ".venv/bin/semgrep"),
            "scan",
            "--quiet",
            "--json",
            "--metrics=off",
            "--disable-version-check",
            "--config",
            str(repo_root / "config/semgrep/layer-boundaries.yml"),
            str(fixture_root / "commands/invalid_controller.py"),
            str(fixture_root / "commands/invalid_broad_runtime.py"),
            str(fixture_root / "commands/invalid_report_runtime.py"),
            str(fixture_root / "commands/_runtime.py"),
            str(fixture_root / "commands/valid_controller.py"),
            str(fixture_root / "report/application.py"),
            str(fixture_root / "report/application/invalid_use_case.py"),
            str(fixture_root / "report/valid_use_case.py"),
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        env=environment,
        text=True,
    )
    report: dict[str, Any] = json.loads(completed.stdout)
    findings = report["results"]

    assert {finding["check_id"].removeprefix("config.semgrep.") for finding in findings} == {
        "ai-agents-metrics.application-direct-io",
        "ai-agents-metrics.command-broad-runtime",
        "ai-agents-metrics.command-runtime-any-return",
        "ai-agents-metrics.controller-persistence-call",
        "ai-agents-metrics.controller-warehouse-schema",
    }
    assert all(not Path(finding["path"]).name.startswith("valid_") for finding in findings)
    assert any(
        finding["path"].endswith("report/application/invalid_use_case.py") for finding in findings
    )
    assert any(
        finding["path"].endswith("commands/invalid_report_runtime.py") for finding in findings
    )
