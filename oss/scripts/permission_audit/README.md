# permission_audit

Analyze Claude Code bash command history and optimize `.claude/settings.local.json` permission rules.

## What it does

1. **Extract** — scans `~/.claude/projects/` JSONL session files, extracts all `Bash` tool_use commands, writes a frequency-sorted TSV.
2. **Check** — reads the TSV and checks each command against `allow`/`deny` rules from `settings.local.json` and `~/.claude/settings.json`. Reports commands that would trigger a permission prompt.
3. **Find redundant** — detects allow rules that are fully covered by another broader rule.

## Quick start

```bash
cd your-project/          # the project whose permissions you want to audit
python path/to/permission_audit/extract_bash_commands.py
python path/to/permission_audit/check_permissions.py
python path/to/permission_audit/find_redundant_rules.py
```

All scripts auto-detect the project from the current git repo root.

## Files

| File | Purpose |
|---|---|
| `claude_glob.py` | Claude Code permission glob matcher (library) |
| `check_permissions.py` | Check commands against allow/deny rules |
| `extract_bash_commands.py` | Extract bash commands from JSONL history |
| `find_redundant_rules.py` | Find redundant allow rules |
| `conftest.py` | pytest path setup |
| `test_claude_glob.py` | Tests for the glob matcher |
| `test_check_permissions.py` | Tests for the permission checker |

## Claude Code matching semantics

- `*` does NOT match shell operators (`&&`, `||`, `|`, `;`, `>`)
- fd redirects (`2>&1`, `2>/dev/null`) are NOT operators — `*` matches through them
- Operators inside quotes or after backslash are treated as ordinary characters
- Compound commands are split at operators; each segment is checked independently
- Deny rules are checked before allow rules

## Running tests

```bash
cd permission_audit/
python -m pytest -v
```
