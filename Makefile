PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: venv install test lint run-example clean

venv:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install -U pip

install: venv
	$(BIN)/python -m pip install -e .
	$(BIN)/python -m pip install pytest

test:
	$(BIN)/python -m pytest -q

lint:
	$(BIN)/python -m py_compile patchprobe/*.py patchprobe/**/*.py

run-example:
	@echo "Usage:"
	@echo "  $(BIN)/python -m patchprobe.cli run --a ./before.bin --b ./after.bin --out ./job --format json"

clean:
	rm -rf .pytest_cache .mypy_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
