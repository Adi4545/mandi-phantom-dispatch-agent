PYTHON ?= python3

.PHONY: test build eval sensitivity a10 a18 v6 figures audit verify deliverables reproduce

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

v6:
	$(PYTHON) -m revision.eval_v6

figures:
	$(PYTHON) -m revision.make_figures

audit:
	$(PYTHON) scripts/a16_independent_audit.py

verify:
	$(PYTHON) scripts/verify_traceability.py

deliverables:
	$(PYTHON) scripts/build_revision_v5_deliverables.py
	$(PYTHON) scripts/build_first_principles_defense_pdf.py
	$(PYTHON) scripts/build_master_study_guide_pdf.py
	$(PYTHON) scripts/build_student_study_guide_pdf.py

reproduce: build eval sensitivity a10 a18 v6 figures
	@test ! -f scripts/a16_independent_audit.py || $(PYTHON) scripts/a16_independent_audit.py
	@test ! -f scripts/verify_traceability.py || $(PYTHON) scripts/verify_traceability.py
	$(PYTHON) -m pytest -v
