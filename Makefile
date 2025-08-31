.PHONY: help install dev test lint format clean build docs

# Default target
help:
	@echo "Available commands:"
	@echo "  install     Install package and dependencies"
	@echo "  dev         Install development dependencies"
	@echo "  test        Run tests"
	@echo "  lint        Run linting"
	@echo "  format      Format code"
	@echo "  clean       Clean build artifacts"
	@echo "  build       Build package"
	@echo "  docs        Build documentation"

# Install package
install:
	pip install -e .

# Install development dependencies
dev:
	pip install -e ".[dev,docs]"
	pre-commit install

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