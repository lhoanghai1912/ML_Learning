.PHONY: setup lint test up down ingest dbt forecast sample

setup:
	@if command -v uv >/dev/null 2>&1; then \
		uv sync; \
	else \
		pip install -e .; \
	fi

lint:
	ruff check src tests jobs

test:
	pytest

up:
	docker compose up -d

down:
	docker compose down

ingest:
	python jobs/ingest_csv_to_iceberg.py

dbt:
	cd dbt_datathon && dbt run

forecast:
	python -m datathon.submission

sample:
	python jobs/make_sample.py
