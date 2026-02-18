.PHONY: install test lint typecheck format docs hooks

install: ## Install dev and docs dependencies
	uv sync --group dev --group docs

hooks: ## Install pre-commit hooks
	uv run pre-commit install

test: ## Run tests
	uv run pytest tests/ -v

lint: ## Run ruff linter
	uv run ruff check symref/

typecheck: ## Run mypy
	uv run mypy symref/

format: ## Run ruff formatter
	uv run ruff format symref/ tests/

docs: ## Serve docs locally
	uv run mkdocs serve

check: lint typecheck test ## Run lint, typecheck, and tests

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
