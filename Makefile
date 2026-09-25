.PHONY: install test lint validate analysis serve all

install:
	python -m venv .venv
	.venv/bin/pip install -e ".[api,dev]"

test:
	.venv/bin/pytest -q

lint:
	.venv/bin/ruff check src tests

validate:
	.venv/bin/cost-to-orbit-validate

analysis:
	.venv/bin/python -m cost_to_orbit.report

serve:
	.venv/bin/uvicorn cost_to_orbit.api:app --reload

all: lint test validate analysis
