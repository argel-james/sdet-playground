.PHONY: install test coverage test-ci run

install:
	pip install -r requirements.txt

test:
	pytest -v --tb=short

coverage:
	pytest --cov=app --cov-report=term-missing --cov-report=html

test-ci:
	pytest --cov=app --cov-report=term-missing --cov-report=xml

run:
	uvicorn app.main:app --reload --port 8000
