.PHONY: test smoke-test replay-demo validate incidents production-check redis-diag install-test-deps

PYTHON ?= python
PYTEST ?= pytest

# Default: run unit tests (no integration)
test:
	$(PYTEST) -m "not integration"

# Full test suite including integration (requires running stack)
test-all:
	$(PYTEST)

# Coverage report
test-cov:
	$(PYTEST) -m "not integration" --cov=backend/app --cov-report=term-missing

# Pipeline smoke tests only
smoke-test:
	$(PYTEST) backend/tests/test_pipeline.py backend/tests/test_health.py -v

# End-to-end platform validation
validate:
	$(PYTHON) scripts/test-platform.py

# Production readiness check
production-check:
	$(PYTHON) scripts/production-check.py

# Demo replay for presentations
replay-demo:
	$(PYTHON) scripts/demo-replay.py

# Generate synthetic incidents
incidents:
	$(PYTHON) scripts/generate-incidents.py --all-types

incidents-async:
	$(PYTHON) scripts/generate-incidents.py --all-types --async

# Redis & Celery diagnostics
redis-diag:
	$(PYTHON) scripts/redis-diagnostics.py

# Install test dependencies
install-test-deps:
	pip install -r backend/requirements.txt -r backend/requirements-dev.txt

# Run everything (stack must be up)
full-validation: validate smoke-test production-check
