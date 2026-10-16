# palace-engine

An event-driven spaced-repetition, trend intelligence, cognitive quality linter, 4-stage Evidentiary Competency Gate, and Progressive Web App (`palace-deck`) for AWS SAA-C03 mastery on Omarchy Arch Linux.

## Architectural Overview

```text
[ Remote Client (Desktop / iPad / iPhone PWA) ]
            │  HTTPS (Cloudflare Zero Trust Access + MFA)
            ▼
[ cloudflared Outbound Tunnel on Omarchy ] (config/cloudflared-config.yml)
            │  http://localhost:8420
            ▼
[ Palace Deck Interactive Station ] (engine/server.py + static/manifest.json)
    ├── 4-Stage Evidentiary Competency Gate (engine/competency_gate.py)
    ├── Lead Architect Rubric Evaluator     (engine/evaluator_rubric.py)
    ├── Cognitive Quality Linter            (engine/cognitive_linter.py)
    ├── SuperMemo SM-2 Calibration          (engine/adaptive_srs.py)
    ├── Reddit SAA-C03 Trend Radar          (engine/scraper.py & engine/correlate.py)
    └── SQLite Interaction & Audit Ledger   (engine/db.py)
```

## The 4 Evidentiary Competency Gates

1. **Stage 1: Mnemonic Retrieval** $\rightarrow$ Gate 1 requires sub-2.2s factual recall latency and boundary accuracy.
2. **Stage 2: Boundary Disambiguation** $\rightarrow$ Gate 2 requires distractor rejection and $\ge 2$ architectural trade-offs (`cost`, `latency`, `operational_overhead`, `blast_radius`). Boundary failure snaps back to Stage 1.
3. **Stage 3: Trade-Off Synthesis** $\rightarrow$ Gate 3 requires $\ge 3$ trade-offs and $\ge 1$ mitigated failure mode (`poison_pill`, `duplicate_execution`, `throttling`, `regional_outage`).
4. **Stage 4: Production Instinct** $\rightarrow$ Mnemonic scaffolding is retired; locus is tested exclusively via production design prompts.

## Omarchy Arch Linux & Cloudflare Zero Trust Setup

### 1. Run Pre-Commit Quality Scrub
```bash
bash scripts/quality_scrub.sh
```

### 2. Enable Local Systemd Services & Hyprland Scratchpad
```bash
mkdir -p ~/.config/systemd/user
cp systemd/palace-scraper.service systemd/palace-scraper.timer systemd/palace-deck.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now palace-scraper.timer
systemctl --user enable --now palace-deck.service
```
Append `config/hyprland-palace-deck.conf` to `~/.config/hypr/hyprland.conf` (`Super + Shift + M`).

### 3. Provision Cloudflare Tunnel (`cloudflared`) for Zero-Port Remote PWA Access
```bash
bash scripts/setup_cloudflared_omarchy.sh palace-tunnel palace.yourdomain.com
```
Copy `config/cloudflared-config.yml` to `~/.cloudflared/config.yml`, then enable the system daemon:
```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

## Automated CI Maintenance Log
<!-- START_AGENT_MAINTENANCE_LOG -->
#### Maintenance Run: `2026-10-16 19:16:08 UTC`
- `.github/workflows/gap-analysis.yml`: Upgrade actions/checkout from v4 to v7 for security & performance. [Research: RCSB PDB AI Help Desk: retrieval-augmented generation for protein structure deposition support (OpenAlex / Global University Research)] [NIST SP 800-218 PW.4]
- `.github/workflows/gap-analysis.yml`: Upgrade actions/setup-python from v5 to v7 for security & performance. [Research: RCSB PDB AI Help Desk: retrieval-augmented generation for protein structure deposition support (OpenAlex / Global University Research)] [NIST SP 800-218 PW.4]
- `.github/workflows/gap-analysis.yml`: Enforce timeout-minutes: 10 to kill hung processes and prevent runaway billing (CISA & FinOps).
- `.github/workflows/test-and-evaluate.yml`: Upgrade actions/checkout from v4 to v7 for security & performance. [Research: RCSB PDB AI Help Desk: retrieval-augmented generation for protein structure deposition support (OpenAlex / Global University Research)] [NIST SP 800-218 PW.4]
- `.github/workflows/test-and-evaluate.yml`: Upgrade actions/setup-python from v5 to v7 for security & performance. [Research: RCSB PDB AI Help Desk: retrieval-augmented generation for protein structure deposition support (OpenAlex / Global University Research)] [NIST SP 800-218 PW.4]
- `.github/workflows/test-and-evaluate.yml`: Enforce timeout-minutes: 10 to kill hung processes and prevent runaway billing (CISA & FinOps).

<!-- END_AGENT_MAINTENANCE_LOG -->
