# Standalone Binaries Retrospective

## Situation

After packaging `codex-metrics` as an installable Python CLI, the next distribution gap was still obvious:

- downstream users could still get blocked by Python toolchain differences
- Homebrew-managed Python on macOS could reject direct `pip install`
- "install from source" was workable for maintainers, but still too fragile for a one-command downstream experience

The goal of this step was to make `codex-metrics` runnable as a real standalone artifact on macOS, Linux, and Windows, and to treat that artifact as a first-class release surface rather than an afterthought.

## What Happened

The work added a standalone packaging path with:

- a dedicated PyInstaller build script
- a canonical local `make package-standalone` target
- CI matrix builds for macOS, Linux, and Windows
- smoke checks for the built standalone executable on each platform
- README guidance for bootstrap and upgrade flows that use the standalone binary directly

While implementing it, a few hidden assumptions surfaced:

1. The CLI still assumed runtime access to packaged pricing data through a normal source-tree path.
That had to be rewritten to use package resources so the frozen binary could still resolve `model_pricing.json`.

2. PyInstaller on this machine was not frictionless by default.
It needed a workspace-local `PYINSTALLER_CONFIG_DIR` to avoid permission trouble during local builds.

3. A successful source-tree verification pass was not enough.
The real public artifact had to be built and executed directly, because freeze-time resource handling and entrypoint behavior can differ from both `python -m codex_metrics` and the installed wheel path.

## Root Cause

The original packaging work solved the Python distribution problem, but not the artifact-distribution problem.

That left a gap between:

- "the code is installable in a Python environment"
- and "a downstream user can run it without caring about Python environment management"

The gap existed because packaging assumptions were still mostly source-centric:

- runtime data loading still leaned on repo/package layout expectations
- verification focused on source and wheel execution more than frozen execution
- documentation still needed Python-specific fallback guidance because the standalone artifact did not exist yet

## Retrospective

The valuable part of this milestone was not merely producing a binary.

The better outcome was making the standalone artifact an explicit, testable release surface:

- local builds now have one canonical command
- CI now produces platform-specific artifacts instead of only Python packages
- documentation can point downstream users to a distribution mode that bypasses PEP 668 and similar environment friction

The biggest practical lesson is that standalone distribution needs its own validation layer.

Once a project ships both wheels and frozen binaries, "it passed tests" or even "the wheel installs" is still not enough. The binary has to be run as the binary, with its packaged resources and real entrypoint path.

## Conclusions

- Standalone binaries are a distinct product surface, not a trivial packaging byproduct.
- Runtime data files must be loaded through packaging-safe resource access before frozen builds can be trusted.
- Release verification should explicitly include the built standalone executable, not only source-tree and wheel execution.
- Cross-platform artifact generation belongs in CI as a matrix job, not as a manual maintainer-only step.
- Standalone binaries reduce downstream setup friction, but they do not replace the need for clear upgrade and bootstrap instructions.

## Permanent Changes

- Added `scripts/build_standalone.py` as the canonical standalone build entrypoint.
- Added `make package-standalone` for reproducible local artifact generation.
- Updated the package CLI to resolve pricing data through package resources so frozen binaries can load bundled data correctly.
- Added GitHub Actions matrix builds for macOS, Linux, and Windows standalone artifacts.
- Added standalone smoke checks to CI and local validation.
- Updated README install and upgrade guidance to document standalone-binary usage as the preferred downstream path when release artifacts are available.
