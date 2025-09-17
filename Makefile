.PHONY: help install lint format typecheck test

help:
	@echo "Available commands:"
	@echo "  install   - Install dependencies"
	@echo "  lint      - Run ruff linting"
	@echo "  format    - Format code with ruff"
	@echo "  typecheck - Run pyright type checking"

install:
	poetry install

lint:
	poetry run ruff check .

format:
	poetry run ruff format .

typecheck:
	poetry run pyright

test:
	poetry run pytest
