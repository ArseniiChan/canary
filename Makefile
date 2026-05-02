PYTHON ?= python3.12
PIP    ?= $(PYTHON) -m pip
VENV   ?= .venv
ACT    := . $(VENV)/bin/activate &&

.PHONY: help venv install pin-accessions data parse embeddings train score validate figures test reproduce clean

help:
	@echo "Canary build targets:"
	@echo "  make venv             create Python 3.12 virtualenv at $(VENV)"
	@echo "  make install          install runtime + dev deps into the venv"
	@echo "  make pin-accessions   Phase 0 — verify and pin EDGAR accessions"
	@echo "  make data             Phase 1+2 — pull filings + parse MD&A"
	@echo "  make embeddings       Phase 3 — compute MiniLM sentence embeddings"
	@echo "  make train            Phase 3 — train LOCO + time-controlled autoencoders"
	@echo "  make score            Phase 4 — score every filing"
	@echo "  make validate         Phase 5 — run validation against frozen analysis_spec.md"
	@echo "  make figures          Phase 6 — regenerate every report figure"
	@echo "  make test             run pytest"
	@echo "  make reproduce        end-to-end from data/raw cache"
	@echo "  make clean            remove caches and venv (does NOT touch data/raw)"

venv:
	$(PYTHON) -m venv $(VENV)
	$(ACT) $(PIP) install --upgrade pip wheel

install: venv
	$(ACT) $(PIP) install -e ".[dev]"

pin-accessions:
	$(ACT) $(PYTHON) scripts/00_pin_accessions.py

data:
	$(ACT) $(PYTHON) scripts/01_pull_filings.py
	$(ACT) $(PYTHON) scripts/02_parse_filings.py

parse:
	$(ACT) $(PYTHON) scripts/02_parse_filings.py

embeddings:
	$(ACT) $(PYTHON) scripts/03_compute_embeddings.py

train:
	$(ACT) $(PYTHON) scripts/04_train_loco_autoencoders.py

score:
	$(ACT) $(PYTHON) scripts/05_score_filings.py

validate:
	$(ACT) $(PYTHON) scripts/06_validate.py

figures:
	$(ACT) $(PYTHON) scripts/07_generate_figures.py

test:
	$(ACT) pytest

reproduce: data embeddings train score validate figures
	@echo "Reproduction complete. See data/results/ and reports/figures/."

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache .mypy_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} +
