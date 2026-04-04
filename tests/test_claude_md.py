"""CLAUDE.md must remain a stable pointer to AGENTS.md and never be edited directly."""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

EXPECTED_CONTENT = (
    "See AGENTS.md for project rules and working style"
    " — read it before starting any task.\n"
    "\n"
    "To update project rules or working style, edit AGENTS.md only."
    " Never edit this file (CLAUDE.md).\n"
)


def test_claude_md_exists():
    assert CLAUDE_MD.exists(), "CLAUDE.md must exist"


def test_claude_md_content_unchanged():
    actual = CLAUDE_MD.read_text(encoding="utf-8")
    assert actual == EXPECTED_CONTENT, (
        "CLAUDE.md was modified. Edit AGENTS.md instead.\n"
        f"Expected:\n{EXPECTED_CONTENT!r}\nGot:\n{actual!r}"
    )
