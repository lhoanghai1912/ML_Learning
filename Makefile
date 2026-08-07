.PHONY: setup lint test up down ingest dbt forecast sample

# Interpreter resolution:
#   - Dùng .venv/bin/python nếu `make setup` đã tạo (uv sync và pip fallback đều tạo .venv).
#   - Fallback python3 (macOS/Linux hiện đại KHÔNG có alias `python`, `pip` trần cũng thường thiếu).
# Không dùng `python`/`pip` trần trong bất kỳ target nào — đó là lý do make setup chết Error 127.
PY  := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
DBT := $(shell [ -x "$(CURDIR)/.venv/bin/dbt" ] && echo "$(CURDIR)/.venv/bin/dbt" || echo dbt)

setup:
	@if command -v uv >/dev/null 2>&1; then \
		echo ">> uv found -> uv sync"; \
		uv sync; \
	else \
		echo ">> uv not found -> python3 -m venv .venv + pip install -e ."; \
		python3 -m venv .venv; \
		.venv/bin/python -m pip install --quiet --upgrade pip; \
		.venv/bin/python -m pip install --quiet -e .; \
	fi
	@echo ">> setup done: $$([ -x .venv/bin/python ] && .venv/bin/python -V || python3 -V)"

lint:
	$(PY) -m ruff check src tests jobs

test:
	$(PY) -m pytest

up:
	docker compose up -d

down:
	docker compose down

ingest:
	$(PY) jobs/ingest_csv_to_iceberg.py

dbt:
	cd dbt_datathon && $(DBT) run

forecast:
	$(PY) -m datathon.submission

sample:
	$(PY) tests/tools/generate_sample.py
