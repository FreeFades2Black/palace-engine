.PHONY: install evaluate suggest test all

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -r requirements.txt

evaluate:
	$(PYTHON) engine/scoring.py

suggest:
	$(PYTHON) engine/suggest.py

test:
	$(PYTHON) -m pytest -v

all: test evaluate suggest
