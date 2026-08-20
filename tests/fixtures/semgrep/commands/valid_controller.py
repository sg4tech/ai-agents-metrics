"""Fixture containing a thin command handler."""


def handle_report(runtime: object) -> None:
    runtime.build_report()  # type: ignore[attr-defined]
