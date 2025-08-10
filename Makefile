ruff:
	uv run ruff format .
	uv run ruff check . --fix

dev:
	uv run uvicorn backend.main:app --reload

test:
	uv run pytest

test-coverage:
	uv run pytest --cov=backend --cov-report=html --cov-report=term
