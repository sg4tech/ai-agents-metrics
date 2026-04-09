include oss/Makefile

# Override: delegate to oss/ where pyproject.toml lives
init:
	cd oss && $(MAKE) init
	@echo ""
	@echo "AGENTS: all engineering work must be done inside oss/ — do not run make targets or CLI from the private root"
	@echo ""

# When run from the private repo, check the oss/ subtree specifically
public-overlay-verify:
	./.venv/bin/python -m codex_metrics verify-public-boundary --repo-root oss --rules-path oss/config/public-boundary-rules.toml
