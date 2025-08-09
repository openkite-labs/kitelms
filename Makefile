ruff:
	uv run ruff format .
	uv run ruff check . --fix

dev:
	uv run uvicorn backend.main:app --reload