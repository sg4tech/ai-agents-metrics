# Shell Completion and Standalone UX Retrospective

## Situation

After adding standalone binaries and documenting self-host usage, the CLI was runnable, but still not smooth in day-to-day shell use.

Two user-facing gaps surfaced immediately:

- `codex-metrics` did not autocomplete commands in the shell
- the documentation still blurred the line between "installed CLI on PATH" and "downloaded standalone binary invoked by path"

That made the tooling feel more complete than it actually was.

## What Happened

The first standalone-oriented documentation assumed a user could switch from a downloaded binary to commands like:

- `codex-metrics bootstrap`
- `codex-metrics show`

But in a self-host scenario the binary was often just a file in the current directory or another arbitrary path, so the shell correctly returned:

- `zsh: command not found: codex-metrics`

That exposed two separate product issues:

1. The standalone path had not been documented precisely enough.
Examples still implicitly assumed the command was already on `PATH`.

2. The CLI had no built-in completion support.
Even after the command was reachable, the shell had no way to autocomplete subcommands or flags.

The fix added:

- a new `completion` command that prints completion scripts for `bash` and `zsh`
- automated tests for completion output
- README updates that distinguish:
  - PATH-installed command usage
  - standalone-binary-by-path usage
  - troubleshooting for `command not found`
  - completion setup for both installed and standalone flows

## Root Cause

The underlying mistake was treating "distribution exists" as if it automatically implied "interactive UX is good enough".

That assumption hid two separate realities:

- a standalone binary is a delivery artifact, not an installed shell command
- shell ergonomics such as completion do not appear automatically unless the product explicitly provides and documents them

So the packaging work solved execution, but not discoverability and shell comfort.

## Retrospective

The useful lesson here is that CLI completeness has at least three layers:

- runnable
- discoverable
- ergonomic

We had already made the tool runnable in more environments, but the user quickly surfaced that it still felt unfinished in the shell.

The good outcome is that the fix stayed small and product-shaped:

- one built-in `completion` surface
- no extra runtime dependency
- tests that lock the feature in place
- clearer docs for the real self-host path

## Conclusions

- A standalone binary should never be documented as if it were automatically on `PATH`.
- CLI release work should include shell ergonomics, not only execution.
- Completion support is part of the public command surface once a CLI is meant for repeated interactive use.
- Docs must distinguish "invoke by command name" from "invoke by filesystem path" explicitly.

## Permanent Changes

- Added `codex-metrics completion bash|zsh` as a built-in completion surface.
- Added automated tests for help output and generated completion scripts.
- Updated README to explain standalone-binary invocation by path versus PATH-installed command usage.
- Added explicit completion setup instructions for both normal install and standalone self-host flows.
