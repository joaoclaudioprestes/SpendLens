.DEFAULT_GOAL := help

PYTHON := uv run python
PYTEST := uv run pytest
RUFF := uv run ruff

.PHONY: \
	help setup sync update lock \
	run shell \
	test test-unit test-cov \
	lint format format-check \
	check verify ci \
	clean

# Help

help:
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "Environment"
	@echo "  make setup          Install/sync dependencies"
	@echo "  make sync           Sync dependencies"
	@echo "  make update         Upgrade dependencies"
	@echo "  make lock           Regenerate lock file"
	@echo ""
	@echo "Development"
	@echo "  make run            Run application"
	@echo "  make shell          Open Python shell"
	@echo ""
	@echo "Quality"
	@echo "  make format         Auto-format code"
	@echo "  make lint           Run linter"
	@echo "  make test           Run tests"
	@echo "  make test-cov       Run tests with coverage"
	@echo "  make verify         Format check + lint + tests"
	@echo ""
	@echo "Maintenance"
	@echo "  make clean          Remove cache files"
	@echo ""

# Environment

setup:
	uv sync

sync:
	uv sync

update:
	uv sync --upgrade

lock:
	uv lock

# Development

run:
	uv run spendlens

shell:
	uv run python

# Formatting & Linting

format:
	$(RUFF) format .
	$(RUFF) check . --fix

format-check:
	$(RUFF) format --check .

lint:
	$(RUFF) check .

# Testing

test:
	$(PYTEST)

test-unit:
	$(PYTEST) src/tests/unit

test-integration:
	$(PYTEST) src/tests/integration

test-cov:
	$(PYTEST) \
		--cov=src \
		--cov-report=term-missing \
		--cov-report=html

# Verification

verify: format-check lint test

check:
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test

ci: verify

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	rm -rf htmlcov
	rm -rf dist
	rm -rf build