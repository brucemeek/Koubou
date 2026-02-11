.PHONY: format lint test install install-dev install-hooks check

format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/
	mypy src/

test:
	pytest -v --cov=src/koubou

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-hooks:
	git config core.hooksPath .githooks

check: format lint test
