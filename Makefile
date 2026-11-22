PYTHON ?= python3

.PHONY: test build eval sensitivity a10 a18 figures audit verify reproduce

test:
	$(PYTHON) -m pytest -v

build:
	$(PYTHON) -m revision.build_variant
	$(PYTHON) -m revision.build_hp_apple_lagged

eval:
	$(PYTHON) -m revision.eval_run

sensitivity:
	$(PYTHON) -m revision.sensitivity_a8

a10:
	$(PYTHON) -m revision.eval_a10

a18:
	$(PYTHON) -m revision.eval_a18

figures:
	$(PYTHON) -m revision.make_figures

audit:
	$(PYTHON) scripts/a16_independent_audit.py

verify:
	$(PYTHON) scripts/verify_traceability.py

reproduce: build eval sensitivity a10 a18 figures
	@test ! -f scripts/a16_independent_audit.py || $(PYTHON) scripts/a16_independent_audit.py
	@test ! -f scripts/verify_traceability.py || $(PYTHON) scripts/verify_traceability.py
	$(PYTHON) -m pytest -v
