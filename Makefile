.PHONY: install test lint demo report dashboard-dev dashboard-build sample-report all

VENV ?= .venv
PY   ?= $(VENV)/bin/python
PIP  ?= $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip wheel
	$(PIP) install -e ".[dev,api]"

test:
	$(VENV)/bin/pytest -q

lint:
	$(VENV)/bin/ruff check src tests

demo:
	$(PY) demo/multi_tenant_leak.py

sample-report:
	FERRYTE_STATE_DIR=$$(mktemp -d) $(PY) -c "import ferryte; from ferryte.adapters.vector import InMemoryVectorStore; from ferryte.instrument import current_instrumentation; from ferryte.lineage import get_lineage; from ferryte.oracle.runner import run_scenarios; from ferryte.reports import build_coverage_report, write_json_report; from pathlib import Path; ferryte.instrument(); InMemoryVectorStore(leak_summaries=True); h = current_instrumentation(); rs = run_scenarios(instrumentation=h, names=['all']); r = build_coverage_report(instrumentation=h, lineage=get_lineage(), results=rs); write_json_report(path=Path('dashboard/src/sample-report.json'), report=r, results=rs); print('regenerated sample report')"

dashboard-dev:
	cd dashboard && npm run dev

dashboard-build:
	cd dashboard && npm run build

all: install test demo sample-report dashboard-build
