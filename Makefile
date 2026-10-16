.PHONY: install evaluate suggest scrape correlate lint srs serve scrub test all

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) engine/cognitive_linter.py

scrape:
	$(PYTHON) engine/scraper.py

correlate:
	$(PYTHON) engine/correlate.py

srs:
	$(PYTHON) engine/adaptive_srs.py

evaluate:
	$(PYTHON) engine/scoring.py

suggest:
	$(PYTHON) engine/suggest.py

serve:
	$(PYTHON) -m uvicorn engine.server:app --host 127.0.0.1 --port 8420 --reload

test:
	$(PYTHON) -m pytest -v

scrub:
	bash scripts/quality_scrub.sh

all: lint correlate test evaluate suggest
