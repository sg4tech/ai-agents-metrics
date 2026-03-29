from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Protocol

from codex_metrics.storage import atomic_write_text, ensure_parent_dir

START_MARKER = "<!-- codex-metrics:start -->"
END_MARKER = "<!-- codex-metrics:end -->"


@dataclass(frozen=True)
class BootstrapResult:
    messages: list[str]


class InitFilesCallable(Protocol):
    def __call__(self, metrics_path: Path, report_path: Path, force: bool = False) -> None: ...


def load_policy_template() -> str:
    return resources.files("codex_metrics").joinpath("data/bootstrap_codex_metrics_policy.md").read_text(
        encoding="utf-8"
    )


def path_for_agents(target_path: Path, *, agents_path: Path) -> Path:
    return Path(os.path.relpath(target_path, start=agents_path.parent))


def render_agents_block(*, policy_path: Path, metrics_path: Path, report_path: Path) -> str:
    policy_label = policy_path.as_posix()
    metrics_label = metrics_path.as_posix()
    report_label = report_path.as_posix()
    return (
        f"{START_MARKER}\n"
        "## Codex Metrics\n\n"
        "Use `codex-metrics` to track goal, attempt, failure, and cost history for Codex-assisted work.\n\n"
        "Generated artifacts:\n\n"
        f"- `{metrics_label}`\n"
        f"- `{report_label}`\n\n"
        "Policy:\n\n"
        f"- `{policy_label}`\n\n"
        "Typical flow:\n\n"
        "1. `codex-metrics update --title \"...\" --task-type product --attempts-delta 1`\n"
        "2. `codex-metrics update --task-id <goal-id> --status success --notes \"Validated\"`\n"
        "3. `codex-metrics show`\n\n"
        "Do not edit generated metrics files manually when the CLI can regenerate them.\n"
        f"{END_MARKER}\n"
    )


def upsert_agents_text(
    existing_text: str | None,
    *,
    policy_path: Path,
    metrics_path: Path,
    report_path: Path,
) -> tuple[str, str]:
    block = render_agents_block(
        policy_path=policy_path,
        metrics_path=metrics_path,
        report_path=report_path,
    )
    if existing_text is None:
        return f"# AGENTS.md\n\n{block}", "create"

    if START_MARKER in existing_text and END_MARKER in existing_text:
        start_index = existing_text.index(START_MARKER)
        end_index = existing_text.index(END_MARKER) + len(END_MARKER)
        replaced = existing_text[:start_index].rstrip()
        suffix = existing_text[end_index:].lstrip("\n")
        updated_parts = [part for part in (replaced, block.rstrip(), suffix.rstrip()) if part]
        return "\n\n".join(updated_parts) + "\n", "update"

    stripped = existing_text.rstrip()
    if not stripped:
        return f"# AGENTS.md\n\n{block}", "create"
    return f"{stripped}\n\n{block}", "append"


def write_path(path: Path, content: str) -> None:
    ensure_parent_dir(path)
    atomic_write_text(path, content)


def bootstrap_project(
    *,
    target_dir: Path,
    metrics_path: Path,
    report_path: Path,
    policy_path: Path,
    agents_path: Path,
    force: bool,
    dry_run: bool,
    init_files: InitFilesCallable,
) -> BootstrapResult:
    del target_dir
    messages: list[str] = []

    if metrics_path.exists() and report_path.exists():
        messages.extend(
            [
                f"{'Would keep' if dry_run else 'Keeping'} existing metrics file: {metrics_path}",
                f"{'Would keep' if dry_run else 'Keeping'} existing report file: {report_path}",
            ]
        )
    else:
        if dry_run:
            messages.append(f"Would create metrics file: {metrics_path}")
            messages.append(f"Would create report file: {report_path}")
        else:
            init_files(metrics_path, report_path, force=False)
            messages.append(f"Created metrics file: {metrics_path}")
            messages.append(f"Created report file: {report_path}")

    policy_template = load_policy_template()
    if policy_path.exists():
        existing_policy = policy_path.read_text(encoding="utf-8")
        if existing_policy == policy_template:
            messages.append(f"{'Would keep' if dry_run else 'Keeping'} existing policy file: {policy_path}")
        elif dry_run and not force:
            messages.append(
                f"Would refuse to replace existing policy file without --force: {policy_path}"
            )
        elif not force:
            raise ValueError(
                f"Policy file already exists with different content: {policy_path}. Use --force to replace it."
            )
        elif dry_run:
            messages.append(f"Would replace policy file: {policy_path}")
        else:
            write_path(policy_path, policy_template)
            messages.append(f"Replaced policy file: {policy_path}")
    elif dry_run:
        messages.append(f"Would create policy file: {policy_path}")
    else:
        write_path(policy_path, policy_template)
        messages.append(f"Created policy file: {policy_path}")

    existing_agents_text = agents_path.read_text(encoding="utf-8") if agents_path.exists() else None
    agents_text, agents_action = upsert_agents_text(
        existing_agents_text,
        policy_path=path_for_agents(policy_path, agents_path=agents_path),
        metrics_path=path_for_agents(metrics_path, agents_path=agents_path),
        report_path=path_for_agents(report_path, agents_path=agents_path),
    )
    if dry_run:
        if existing_agents_text is None:
            messages.append(f"Would create AGENTS.md: {agents_path}")
        elif existing_agents_text == agents_text:
            messages.append(f"Would keep AGENTS.md unchanged: {agents_path}")
        else:
            verb = "update" if agents_action == "update" else "append codex-metrics block to"
            messages.append(f"Would {verb} AGENTS.md: {agents_path}")
    else:
        if existing_agents_text != agents_text:
            write_path(agents_path, agents_text)
            if existing_agents_text is None:
                messages.append(f"Created AGENTS.md: {agents_path}")
            elif agents_action == "update":
                messages.append(f"Updated managed codex-metrics block in AGENTS.md: {agents_path}")
            else:
                messages.append(f"Appended managed codex-metrics block to AGENTS.md: {agents_path}")
        else:
            messages.append(f"Keeping AGENTS.md unchanged: {agents_path}")

    return BootstrapResult(messages=messages)
