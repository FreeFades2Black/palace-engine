#!/usr/bin/env bash
set -euo pipefail

echo "=== [1/5] Running Cognitive Quality Linter ==="
python engine/cognitive_linter.py

echo "=== [2/5] Checking Evidentiary Competency Gate Status ==="
python engine/competency_gate.py

echo "=== [3/5] Correlating Palace Loci with SAA-C03 Exam Trends ==="
python engine/correlate.py

echo "=== [4/5] Running Spaced Repetition & Gap Analysis ==="
python engine/scoring.py
python engine/suggest.py

echo "=== [5/5] Running Automated Test Suite ==="
python -m pytest -v

echo "[✓] Quality scrub passed with clean exit code 0."
