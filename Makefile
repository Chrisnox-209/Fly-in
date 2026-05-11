MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
--disallow-untyped-defs --check-untyped-defs
MYPY_STRICT = --strict
FLAKE_STRICT = --max-complexity=5
.PHONY: install, run, clean, lint, lint-strict, debug

install:

run:

clean:

lint:
	@python3 -m poetry run python3 -m mypy . $(MYPY_FLAGS)
	@python3 -m poetry run python3 -m flake8 .
lint-strict:
	@python3 -m poetry run python3 -m mypy . $(MYPY_FLAGS) $(MYPY_STRICT)
	@python3 -m poetry run python3 -m flake8 .$(LAKE_STRICT)
debug:
