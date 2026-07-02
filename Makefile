MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
--disallow-untyped-defs --check-untyped-defs
MYPY_STRICT = --strict
FLAKE_STRICT = --max-complexity=5
MAIN = fly-in.py
export UV_LINK_MODE=copy
.PHONY: install, run, clean, lint, lint-strict, debug

install:
	@uv sync

run:
	@uv run python $(MAIN)

clean:
	@rm -Rf .venv
	@rm -Rf __pycache__
	@rm -Rf .mypy_cache
	@rm -Rf uv.lock
	@echo "All code clean"

lint:
	@uv run python -m mypy . $(MYPY_FLAGS)
	@uv run python -m flake8 --exclude .venv .

lint-strict:
	@uv run python -m mypy .  $(MYPY_FLAGS) $(MYPY_STRICT)
	@uv run python -m flake8 --exclude .venv . $(FLAKE_STRICТ)

debug:
	@uv run python -m pdb $(MAIN)
