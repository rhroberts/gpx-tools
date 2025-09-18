.PHONY: help install lint format typecheck test

help:
	@echo "Available commands:"
	@echo "  install   - Install dependencies"
	@echo "  lint      - Run ruff linting"
	@echo "  format    - Format code with ruff"
	@echo "  typecheck - Run pyright type checking"

install:
	uv sync --dev

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run pyright

test:
	uv run pytest
