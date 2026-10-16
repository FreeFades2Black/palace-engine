# palace-engine

An event-driven spaced-repetition, trend intelligence, cognitive quality linter, and interactive recall station (`palace-deck`) for AWS SAA-C03 mastery on Omarchy Arch Linux.

## Architectural Overview

```text
[ External Intel Sources (Reddit r/AWSCertifications) ]
            │ (engine/scraper.py -> data/exam_trends.json)
            ▼
[ Cognitive Quality & Spaced Repetition Engine ]
    ├── engine/cognitive_linter.py  (Von Restorff kinetic check + Major System pegs)
    ├── engine/adaptive_srs.py      (SM-2 interval calibration + confusion matrix)
    ├── engine/correlate.py         (Exam heat score vs. locus stability radar)
    ├── engine/scoring.py           (Markdown recall history parser & evaluator)
    └── engine/suggest.py           (Dynamic next-loci drill generator)
            │
            ▼
[ Palace Deck Interactive Station (http://127.0.0.1:8420) ]
    ├── engine/server.py            (FastAPI keyboard-driven tiling UI)
    ├── engine/db.py                (SQLite millisecond latency & recall ledger)
    └── config/hyprland-palace-deck.conf (Super + Shift + M scratchpad rule)
```

## Repository Structure

```text
palace-engine/
├── .antigravity/
│   └── memory_quality_rules.md     # Cognitive quality gates & pre-commit rules
├── .github/
│   └── workflows/
│       ├── test-and-evaluate.yml   # Lints loci, correlates trends, runs tests & step summary
│       └── gap-analysis.yml        # Scheduled daily decay & drill digest
├── config/
│   └── hyprland-palace-deck.conf   # Hyprland floating window rules & Super+Shift+M keybind
├── data/
│   ├── palace_map.json             # Loci graph with kinetic scenes, Major System pegs & SM-2 state
│   ├── saa_taxonomy.json           # AWS SAA-C03 domains and exam traps
│   ├── exam_trends.json            # Scraped SAA-C03 topic frequency rankings
│   ├── daily_test.json             # Practice exam evaluation records for SM-2 calibration
│   └── recall_history/
│       └── 2026-10-16-session.md   # Daily markdown recall logs
├── engine/
│   ├── adaptive_srs.py             # SuperMemo SM-2 calculator & confusion matrix updater
│   ├── cognitive_linter.py         # Audits kinetic verbs and Major System phonetic pegs
│   ├── correlate.py                # Cross-references exam heat with locus stability
│   ├── db.py                       # SQLite interaction & millisecond latency ledger
│   ├── parser.py                   # Schema and frontmatter parser
│   ├── scoring.py                  # Evaluates recall sessions and knowledge gaps
│   ├── scraper.py                  # Harvests SAA-C03 debriefs from Reddit JSON feeds
│   ├── server.py                   # FastAPI Palace Deck interactive UI & REST endpoints
│   └── suggest.py                  # Prioritized drill generator
├── scripts/
│   └── quality_scrub.sh            # Pre-commit verification pipeline
├── systemd/
│   ├── palace-deck.service         # User daemon for Palace Deck UI (port 8420)
│   ├── palace-scraper.service      # Oneshot trend scraper service
│   └── palace-scraper.timer        # Weekly Monday 06:00 systemd timer
├── tests/
│   └── test_engine.py              # Comprehensive pytest suite
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

## Omarchy Arch Linux Setup

### 1. Install & Run Pre-Commit Quality Scrub
```bash
git clone git@github.com:FreeFades2Black/palace-engine.git ~/projects/palace-engine
cd ~/projects/palace-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

bash scripts/quality_scrub.sh
```

### 2. Enable Systemd Trend Scraper & Palace Deck Daemon
```bash
mkdir -p ~/.config/systemd/user
cp systemd/palace-scraper.service systemd/palace-scraper.timer systemd/palace-deck.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now palace-scraper.timer
systemctl --user enable --now palace-deck.service
```

### 3. Add Hyprland Scratchpad Keybinding
Append `config/hyprland-palace-deck.conf` to `~/.config/hypr/hyprland.conf` to launch or toggle Palace Deck (`http://localhost:8420`) with `Super + Shift + M`.
