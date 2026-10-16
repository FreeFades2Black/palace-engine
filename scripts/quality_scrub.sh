#!/usr/bin/env bash
set -euo pipefail

echo "=== [1/4] Running Cognitive Quality Linter ==="
python engine/cognitive_linter.py

echo "=== [2/4] Correlating Palace Loci with SAA-C03 Exam Trends ==="
python engine/correlate.py

echo "=== [3/4] Running Spaced Repetition & Gap Analysis ==="
python engine/scoring.py
python engine/suggest.py

echo "=== [4/4] Running Automated Test Suite ==="
python -m pytest -v

echo "[✓] Quality scrub passed with clean exit code 0."
