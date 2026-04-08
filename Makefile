include oss/Makefile

# When run from the private repo, check the oss/ subtree specifically
public-overlay-verify:
	./.venv/bin/python -m codex_metrics verify-public-boundary --repo-root oss --rules-path oss/config/public-boundary-rules.toml
