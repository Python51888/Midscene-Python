.PHONY: help install dev test lint format clean build docs requirements-freeze requirements-check

# Default target
help:
	@echo "Available commands:"
	@echo "  install            Install package and dependencies"
	@echo "  dev                Install development dependencies"
	@echo "  requirements-freeze    Generate complete requirements.txt"
	@echo "  requirements-check     Verify dependencies integrity"
	@echo "  requirements-quick-check Quick requirements validation"
	@echo "  test               Run tests"
	@echo "  lint               Run linting"
	@echo "  format             Format code"
	@echo "  clean              Clean build artifacts"
	@echo "  build              Build package"
	@echo "  docs               Build documentation"

# Generate complete requirements.txt with all dependencies
requirements-freeze:
	uv pip compile --all-extras pyproject.toml -o requirements.txt

# Verify dependencies integrity
requirements-check:
	uv pip check
	@python scripts/validate_requirements.py

# Quick requirements validation
requirements-quick-check:
	@scripts/quick_validate.bat

# Install package from requirements.txt
install:
	pip install -r requirements.txt

# Install package in development mode
install-dev:
	pip install -e ".[dev,docs]"
	pre-commit install

# Install development dependencies (alias for backward compatibility)
dev: install-dev

# Run tests
test:
	pytest tests/ -v --cov=midscene --cov-report=html --cov-report=term-missing

# Run tests with specific markers
test-unit:
	pytest tests/ -v -m "unit"

test-integration:
	pytest tests/ -v -m "integration"

# Linting
lint:
	ruff check midscene/ tests/
	mypy midscene/

# Format code
format:
	black midscene/ tests/ examples/
	isort midscene/ tests/ examples/
	ruff check --fix midscene/ tests/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	python -m build

# Build documentation
docs:
	mkdocs build

# Serve documentation locally
docs-serve:
	mkdocs serve

# Release to PyPI
release: build
	twine upload dist/*

# Release to Test PyPI
release-test: build
	twine upload --repository testpypi dist/*