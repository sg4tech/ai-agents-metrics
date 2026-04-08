.PHONY: init check-init lint typecheck test verify security verify-public-boundary setup-hooks dev-refresh-local package package-standalone package-refresh-local package-refresh-global live-usage-smoke

PYTHON3 ?= python3

init:
	git pull origin master
	$(PYTHON3) -m venv .venv
	.venv/bin/pip install -U pip setuptools wheel
	.venv/bin/pip install -e ".[dev]" || .venv/bin/pip install -e .

check-init:
	@test -d .venv || $(MAKE) init

lint:
	./.venv/bin/ruff check .

typecheck:
	./.venv/bin/mypy src scripts

test:
	./.venv/bin/python -m pytest tests/

verify: check-init lint security typecheck test

security:
	./.venv/bin/python -m codex_metrics security --repo-root . --rules-path config/security-rules.toml

verify-public-boundary:
	./.venv/bin/python -m codex_metrics verify-public-boundary --repo-root . --rules-path config/public-boundary-rules.toml

setup-hooks:
	git config core.hooksPath .githooks

dev-refresh-local:
	./.venv/bin/python -m pip install --no-deps --no-build-isolation -e .

package:
	rm -rf build dist src/codex_metrics.egg-info
	./.venv/bin/python -m build --no-isolation

package-standalone:
	rm -rf build/standalone dist/standalone
	./.venv/bin/python scripts/build_standalone.py

package-refresh-local: package
	./.venv/bin/python -m pip install --no-deps --force-reinstall dist/*.whl

package-refresh-global: package-refresh-local package-standalone
	./dist/standalone/codex-metrics install-self $(INSTALL_SELF_ARGS)

live-usage-smoke:
	./.venv/bin/python scripts/check_live_usage_recovery.py

coverage:
	./.venv/bin/coverage erase
	CODEX_SUBPROCESS_COVERAGE=1 ./.venv/bin/coverage run -m pytest tests/
	./.venv/bin/coverage combine
	./.venv/bin/coverage report -m
