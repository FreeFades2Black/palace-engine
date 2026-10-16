# palace-engine

An event-driven spaced-repetition and AWS SAA-C03 knowledge gap analysis engine that bridges daily memory palace recall logs, AWS architectural domains, and automated CI/CD evaluation with local execution on Omarchy Arch Linux.

## Architectural Overview

```text
[ Daily Study / Markdown Notes ]
            │ (git commit & push)
            ▼
[ GitHub Repo: palace-engine ]
    ├── Loci & Architecture Graph (data/palace_map.json, data/saa_taxonomy.json)
    ├── Daily Recall Logs (data/recall_history/*.md)
    └── CI: GitHub Actions (Loci validation, test scoring, gap extraction)
            │ (Dispatch webhook / git pull)
            ▼
[ Omarchy Machine Runner (Local CLI / Systemd Timer) ]
    ├── Spaced Repetition / Decay Algorithm (engine/scoring.py)
    ├── Knowledge Gap Matrix (engine/parser.py)
    └── Dynamic Recall Prompts & Next-Loci Generator (engine/suggest.py)
```

## Repository Structure

```text
palace-engine/
├── .github/
│   └── workflows/
│       ├── test-and-evaluate.yml
│       └── gap-analysis.yml
├── data/
│   ├── palace_map.json       # Structural graph of physical loci and assigned AWS services
│   ├── saa_taxonomy.json     # AWS domains, networking topics, and key test traps
│   └── recall_history/       # Daily markdown notes with YAML frontmatter
│       └── 2026-10-16-session.md
├── engine/
│   ├── parser.py             # Parses recall frontmatter & schemas
│   ├── scoring.py            # Calculates retention, SM-2 stability decay, and gaps
│   └── suggest.py            # Identifies lowest-scoring nodes and generates drill topics
├── tests/
│   └── test_engine.py        # Automated test suite for schema & scoring validation
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

## Quick Start (Omarchy Arch Linux / Local Runner)

```bash
git clone git@github.com:FreeFades2Black/palace-engine.git ~/projects/palace-engine
cd ~/projects/palace-engine

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Evaluate recall logs and print identified SAA-C03 gaps
python engine/scoring.py

# Generate prioritized drill recommendations
python engine/suggest.py
```
