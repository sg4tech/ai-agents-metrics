from __future__ import annotations

from codex_metrics.git_hooks import (
    GitHookRunner,
    VerifyDecision,
    decide_verify_for_paths,
    run_pre_push,
)


class FakeGitHookRunner(GitHookRunner):
    def __init__(self, paths_by_ref: dict[tuple[str, str], list[str]], verify_returncode: int = 0) -> None:
        self.paths_by_ref = paths_by_ref
        self.verify_returncode = verify_returncode
        self.verify_runs = 0

    def changed_paths_for_ref_update(self, local_sha: str, remote_sha: str) -> list[str]:
        return self.paths_by_ref[(local_sha, remote_sha)]

    def run_verify(self) -> int:
        self.verify_runs += 1
        return self.verify_returncode


def test_decide_verify_for_paths_skips_docs_only_changes() -> None:
    decision = decide_verify_for_paths(
        [
            "README.md",
            "docs/retros/2026-04-03-verify-broken-by-unnoticed-lint-drift-retro.md",
            "metrics/codex_metrics.json",
        ]
    )

    assert decision == VerifyDecision(
        should_run=False,
        reason="docs-only changes detected; skipping make verify",
    )


def test_decide_verify_for_paths_runs_verify_for_code_changes() -> None:
    decision = decide_verify_for_paths(
        [
            "README.md",
            "src/codex_metrics/git_hooks.py",
            "tests/test_git_hooks.py",
        ]
    )

    assert decision.should_run is True
    assert "code-affecting changes detected" in decision.reason
    assert "src/codex_metrics/git_hooks.py" in decision.reason


def test_decide_verify_for_paths_treats_runtime_markdown_assets_as_code_changes() -> None:
    decision = decide_verify_for_paths(
        [
            "docs/retros/2026-04-03-verify-broken-by-unnoticed-lint-drift-retro.md",
            "src/codex_metrics/data/bootstrap_codex_metrics_policy.md",
        ]
    )

    assert decision.should_run is True
    assert "src/codex_metrics/data/bootstrap_codex_metrics_policy.md" in decision.reason


def test_run_pre_push_skips_verify_for_docs_only_push(capsys) -> None:
    runner = FakeGitHookRunner(
        {
            ("abc123", "def456"): [
                "README.md",
                "docs/retros/2026-04-03-verify-broken-by-unnoticed-lint-drift-retro.md",
            ]
        }
    )

    exit_code = run_pre_push(["refs/heads/main abc123 refs/remotes/origin/main def456\n"], runner=runner)

    assert exit_code == 0
    assert runner.verify_runs == 0
    captured = capsys.readouterr()
    assert "docs-only changes detected" in captured.out


def test_run_pre_push_runs_verify_for_code_push(capsys) -> None:
    runner = FakeGitHookRunner(
        {
            ("abc123", "def456"): [
                "src/codex_metrics/git_hooks.py",
                "README.md",
            ]
        }
    )

    exit_code = run_pre_push(["refs/heads/main abc123 refs/remotes/origin/main def456\n"], runner=runner)

    assert exit_code == 0
    assert runner.verify_runs == 1
    captured = capsys.readouterr()
    assert "running make verify" in captured.out


def test_run_pre_push_deduplicates_paths_across_ref_updates() -> None:
    runner = FakeGitHookRunner(
        {
            ("abc123", "def456"): ["src/codex_metrics/git_hooks.py"],
            ("abc124", "def457"): ["src/codex_metrics/git_hooks.py", "tests/test_git_hooks.py"],
        }
    )

    exit_code = run_pre_push(
        [
            "refs/heads/main abc123 refs/remotes/origin/main def456\n",
            "refs/heads/feature abc124 refs/remotes/origin/feature def457\n",
        ],
        runner=runner,
    )

    assert exit_code == 0
    assert runner.verify_runs == 1
