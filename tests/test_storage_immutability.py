from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest

from codex_metrics import file_immutability, storage


def test_metrics_file_immutability_guard_unlocks_and_relocks_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text("{}", encoding="utf-8")

    calls: list[list[str]] = []

    def fake_immutability_command() -> tuple[list[str], list[str]]:
        return (["fake-unlock"], ["fake-lock"])

    def fake_run(command: list[str], path: Path) -> None:
        calls.append([*command, str(path)])

    backend = file_immutability.FileImmutabilityBackend()
    monkeypatch.setattr(backend, "command_pair", fake_immutability_command)
    monkeypatch.setattr(backend, "run_command", fake_run)

    with file_immutability.metrics_file_immutability_guard(metrics_path, backend=backend):
        calls.append(["body"])

    assert calls == [
        ["fake-unlock", str(metrics_path)],
        ["body"],
        ["fake-lock", str(metrics_path)],
    ]


def test_metrics_file_immutability_guard_relocks_after_body_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text("{}", encoding="utf-8")

    calls: list[list[str]] = []

    def fake_immutability_command() -> tuple[list[str], list[str]]:
        return (["fake-unlock"], ["fake-lock"])

    def fake_run(command: list[str], path: Path) -> None:
        calls.append([*command, str(path)])

    backend = file_immutability.FileImmutabilityBackend()
    monkeypatch.setattr(backend, "command_pair", fake_immutability_command)
    monkeypatch.setattr(backend, "run_command", fake_run)

    with pytest.raises(RuntimeError):
        with file_immutability.metrics_file_immutability_guard(metrics_path, backend=backend):
            raise RuntimeError("boom")

    assert calls == [
        ["fake-unlock", str(metrics_path)],
        ["fake-lock", str(metrics_path)],
    ]


def test_immutability_backend_returns_none_when_command_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = file_immutability.FileImmutabilityBackend()
    monkeypatch.setattr(file_immutability.os, "name", "posix", raising=False)
    monkeypatch.setattr(file_immutability.os, "uname", lambda: type("Uname", (), {"sysname": "Darwin"})(), raising=False)
    monkeypatch.setattr(file_immutability.shutil, "which", lambda command: None)

    assert backend.command_pair() is None


def test_immutability_backend_selects_linux_chattr_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = file_immutability.FileImmutabilityBackend()
    monkeypatch.setattr(file_immutability.os, "name", "posix", raising=False)
    monkeypatch.setattr(file_immutability.os, "uname", lambda: type("Uname", (), {"sysname": "Linux"})(), raising=False)
    monkeypatch.setattr(file_immutability.shutil, "which", lambda command: f"/usr/bin/{command}")
    monkeypatch.setattr(backend, "_probe_permitted", lambda commands: True)

    assert backend.command_pair() == (["chattr", "-i"], ["chattr", "+i"])


def test_immutability_backend_selects_darwin_chflags_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = file_immutability.FileImmutabilityBackend()
    monkeypatch.setattr(file_immutability.os, "name", "posix", raising=False)
    monkeypatch.setattr(file_immutability.os, "uname", lambda: type("Uname", (), {"sysname": "Darwin"})(), raising=False)
    monkeypatch.setattr(file_immutability.shutil, "which", lambda command: f"/usr/bin/{command}")
    monkeypatch.setattr(backend, "_probe_permitted", lambda commands: True)

    assert backend.command_pair() == (["chflags", "nouchg"], ["chflags", "uchg"])


def test_immutability_backend_returns_none_when_command_exists_but_not_permitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = file_immutability.FileImmutabilityBackend()
    monkeypatch.setattr(file_immutability.os, "name", "posix", raising=False)
    monkeypatch.setattr(file_immutability.os, "uname", lambda: type("Uname", (), {"sysname": "Linux"})(), raising=False)
    monkeypatch.setattr(file_immutability.shutil, "which", lambda command: f"/usr/bin/{command}")
    monkeypatch.setattr(backend, "_probe_permitted", lambda commands: False)

    assert backend.command_pair() is None


def test_immutability_backend_returns_none_on_non_posix(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = file_immutability.FileImmutabilityBackend()
    monkeypatch.setattr(file_immutability.os, "name", "nt", raising=False)

    assert backend.command_pair() is None


def test_immutability_backend_returns_none_on_unsupported_posix_sysname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = file_immutability.FileImmutabilityBackend()
    monkeypatch.setattr(file_immutability.os, "name", "posix", raising=False)
    monkeypatch.setattr(file_immutability.os, "uname", lambda: type("Uname", (), {"sysname": "AIX"})(), raising=False)

    assert backend.command_pair() is None


def test_immutability_backend_run_command_invokes_subprocess_with_expected_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = file_immutability.FileImmutabilityBackend()
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(args: list[str], **kwargs: object) -> None:
        calls.append((args, kwargs))

    monkeypatch.setattr(file_immutability.subprocess, "run", fake_run)

    backend.run_command(["chattr", "+i"], metrics_path)

    assert calls == [
        (
            ["chattr", "+i", str(metrics_path)],
            {
                "check": True,
                "capture_output": True,
                "text": True,
            },
        )
    ]


def test_metrics_file_immutability_guard_noops_when_backend_unsupported(
    tmp_path: Path,
) -> None:
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    calls: list[str] = []

    backend = file_immutability.FileImmutabilityBackend()

    def fake_command_pair() -> None:
        return None

    def fake_run_command(command: list[str], path: Path) -> None:
        calls.append("run")

    backend.command_pair = fake_command_pair  # type: ignore[assignment]
    backend.run_command = fake_run_command  # type: ignore[assignment]

    with file_immutability.metrics_file_immutability_guard(metrics_path, backend=backend):
        calls.append("body")

    assert calls == ["body"]


def test_metrics_file_immutability_guard_locks_created_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    calls: list[list[str]] = []

    def fake_immutability_command() -> tuple[list[str], list[str]]:
        return (["fake-unlock"], ["fake-lock"])

    def fake_run(command: list[str], path: Path) -> None:
        calls.append([*command, str(path)])

    backend = file_immutability.FileImmutabilityBackend()
    monkeypatch.setattr(backend, "command_pair", fake_immutability_command)
    monkeypatch.setattr(backend, "run_command", fake_run)

    with file_immutability.metrics_file_immutability_guard(metrics_path, backend=backend):
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text("{}", encoding="utf-8")
        calls.append(["body"])

    assert calls == [
        ["body"],
        ["fake-lock", str(metrics_path)],
    ]


def test_metrics_mutation_lock_uses_lockfile_and_releases_after_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    lock_path = storage.metrics_lock_path(metrics_path)
    calls: list[tuple[str, str]] = []

    def fake_flock(fd: int, mode: int) -> None:
        calls.append(("flock", str(mode)))

    def fake_sleep(seconds: float) -> None:
        calls.append(("sleep", str(seconds)))

    monkeypatch.setattr(storage.fcntl, "flock", fake_flock)
    monkeypatch.setattr(storage.time, "sleep", fake_sleep)
    monkeypatch.setenv("CODEX_METRICS_DEBUG_LOCK_HOLD_SECONDS", "0.1")

    with storage.metrics_mutation_lock(metrics_path):
        calls.append(("body", str(lock_path)))

    assert lock_path.exists()
    assert calls == [
        ("flock", str(storage.fcntl.LOCK_EX)),
        ("sleep", "0.1"),
        ("body", str(lock_path)),
        ("flock", str(storage.fcntl.LOCK_UN)),
    ]


def test_save_metrics_uses_metrics_file_immutability_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    calls: list[tuple[str, Path]] = []

    @contextmanager
    def metrics_file_immutability_guard(path: Path):
        calls.append(("enter", path))
        yield
        calls.append(("exit", path))

    monkeypatch.setattr(storage, "metrics_file_immutability_guard", metrics_file_immutability_guard, raising=False)

    written: dict[str, object] = {}

    def fake_atomic_write_text(path: Path, content: str) -> None:
        written["path"] = path
        written["content"] = content

    monkeypatch.setattr(storage, "atomic_write_text", fake_atomic_write_text)

    storage.save_metrics(metrics_path, {"summary": {}, "goals": [], "entries": []})

    assert calls == [("enter", metrics_path), ("exit", metrics_path)]
    assert written["path"] == metrics_path


def test_save_metrics_relocks_after_failed_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metrics_path = tmp_path / "metrics" / "codex_metrics.json"
    calls: list[tuple[str, Path]] = []

    @contextmanager
    def metrics_file_immutability_guard(path: Path):
        calls.append(("enter", path))
        try:
            yield
        finally:
            calls.append(("exit", path))

    monkeypatch.setattr(storage, "metrics_file_immutability_guard", metrics_file_immutability_guard, raising=False)

    def fake_atomic_write_text(path: Path, content: str) -> None:
        raise PermissionError(f"simulated immutable file: {path}")

    monkeypatch.setattr(storage, "atomic_write_text", fake_atomic_write_text)

    with pytest.raises(PermissionError):
        storage.save_metrics(metrics_path, {"summary": {}, "goals": [], "entries": []})

    assert calls == [("enter", metrics_path), ("exit", metrics_path)]
