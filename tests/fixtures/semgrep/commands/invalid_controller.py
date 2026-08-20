"""Fixture containing persistence leakage in a command handler."""


def handle_report(connection: object) -> None:
    connection.execute("SELECT * FROM derived_goals")  # type: ignore[attr-defined]
