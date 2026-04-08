include oss/Makefile

.PHONY: public-overlay-status public-overlay-bootstrap public-overlay-verify public-overlay-push public-overlay-pull

public-overlay-status:
	./.venv/bin/python scripts/public_overlay.py --private-repo-root . status

public-overlay-bootstrap:
	./.venv/bin/python scripts/public_overlay.py --private-repo-root . bootstrap --public-repo git@github.com:sg4tech/codex-metrics-public.git

public-overlay-verify:
	./.venv/bin/python -m codex_metrics verify-public-boundary --repo-root oss --rules-path oss/config/public-boundary-rules.toml

public-overlay-push:
	./.venv/bin/python scripts/public_overlay.py --private-repo-root . push --execute

public-overlay-pull:
	./.venv/bin/python scripts/public_overlay.py --private-repo-root . pull --execute
