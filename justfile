set default-list := true

set shell := ["cmd.exe", "/c"]
lint:
	uv run ruff check src
	uv run ruff format --check src

fixup:
	uv run ruff format src
	uv run ruff check --fix src	

type-check:
	uv run ty check .

test:
	uv run pytest .