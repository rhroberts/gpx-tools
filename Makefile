.PHONY: help install lint format typecheck

# Default target
help:
	@echo "Available commands:"
	@echo "  install   - Install dependencies"
	@echo "  lint      - Run ruff linting"
	@echo "  format    - Format code with ruff"
	@echo "  typecheck - Run pyright type checking"


# Install dependencies
install:
	poetry install

# Linting
lint:
	poetry run ruff check .

# Formatting
format:
	poetry run ruff format .

# Type checking
typecheck:
	poetry run pyright
