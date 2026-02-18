# Contributing to symref

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone https://github.com/jpuglielli/symref.git
cd symref
uv sync --group dev --group docs
uv run pre-commit install
```

## Running tests

```bash
uv run pytest tests/ -v
```

## Linting and type-checking

```bash
uv run ruff check symref/
uv run mypy symref/
```

Pre-commit hooks run these automatically on each commit.

## Building docs

```bash
uv run mkdocs serve
```

Then open <http://127.0.0.1:8000>.

## PR workflow

1. Create a feature branch from `main`.
2. Make your changes and commit.
3. Push the branch and open a pull request.
4. Ensure CI passes before requesting review.
