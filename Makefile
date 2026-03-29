.PHONY: lint typecheck test verify coverage

lint:
	./.venv/bin/ruff check .

typecheck:
	./.venv/bin/mypy scripts

test:
	./.venv/bin/python -m pytest tests/test_update_codex_metrics.py tests/test_update_codex_metrics_domain.py

verify: lint typecheck test

coverage:
	./.venv/bin/coverage erase
	CODEX_SUBPROCESS_COVERAGE=1 ./.venv/bin/coverage run -m pytest tests/test_update_codex_metrics.py tests/test_update_codex_metrics_domain.py
	./.venv/bin/coverage combine
	./.venv/bin/coverage report -m scripts/update_codex_metrics.py
