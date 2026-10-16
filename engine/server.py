# engine/server.py
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from engine.adaptive_srs import calculate_sm2
from engine.competency_gate import (
    CompetencyEvidence,
    CompetencyGate,
    apply_competency_transition,
)
from engine.db import get_telemetry_metrics, init_db, record_interaction
from engine.evaluator_rubric import evaluate_candidate_response, rubric_to_evidence

app = FastAPI(title="Palace Deck")
init_db()

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index(req: Request):
    with open("data/palace_map.json", "r", encoding="utf-8") as f:
        palace = json.load(f)

    cf_identity = req.headers.get("Cf-Access-Authenticated-User-Email", "local-omarchy-session")

    loci_items = "".join(
        [
            f"<div class='locus-item' onclick='selectLocus(\"{l['id']}\")'>"
            f"<b>{l['name']}</b> <span class='badge'>Stage {l.get('competency_stage', 1)} | {int(l.get('stability_score', 0.8) * 100)}%</span>"
            f"<br><small>{', '.join(l['aws_services'])}</small></div>"
            for l in palace["loci"]
        ]
    )

    # Minimalist, keyboard-first & mobile PWA visual UI built for tiling managers & Cloudflare Zero Trust
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
      <link rel="manifest" href="/static/manifest.json">
      <title>Palace Deck // SAA-C03 Control</title>
      <style>
        body {{ background: #0f111a; color: #e6edf3; font-family: monospace; margin: 1.5rem; }}
        .header-bar {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 1rem; }}
        .grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 1.5rem; }}
        @media (max-width: 768px) {{
          body {{ margin: 0.75rem; }}
          .grid {{ grid-template-columns: 1fr; gap: 1rem; }}
        }}
        .card {{ background: #161b22; border: 1px solid #30363d; padding: 1.25rem; border-radius: 8px; }}
        .badge {{ background: #238636; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; float: right; }}
        .stage-banner {{ background: #1f6feb; color: #fff; padding: 0.4rem 0.8rem; border-radius: 4px; display: inline-block; margin-bottom: 0.5rem; }}
        .locus-item {{ padding: 0.75rem; border-bottom: 1px solid #21262d; cursor: pointer; }}
        .locus-item:hover {{ background: #1f242c; }}
        .kinetic-box {{ border-left: 3px solid #f78166; padding-left: 1rem; margin: 1rem 0; color: #ffab70; }}
        textarea {{ width: 100%; box-sizing: border-box; background: #0d1117; color: #e6edf3; border: 1px solid #30363d; border-radius: 4px; padding: 0.6rem; font-family: monospace; margin: 0.5rem 0; }}
        button {{ background: #238636; color: white; border: none; padding: 0.6rem 1.1rem; cursor: pointer; border-radius: 4px; margin: 0.25rem 0.4rem 0.25rem 0; }}
      </style>
    </head>
    <body>
      <div class="header-bar">
        <h2>[PALACE-DECK] AWS SAA Cognitive & Evidentiary Gate Engine</h2>
        <small>Auth: {cf_identity}</small>
      </div>
      <div class="grid">
        <div class="card">
          <h3>Memory Loci</h3>
          <button onclick="loadNextDecaying()" style="width:100%; margin-bottom:0.75rem; background:#8957e5;">Next Decaying Node [Space]</button>
          <div id="loci-list">
            {loci_items}
          </div>
        </div>
        <div class="card" id="detail-panel">
          <h3>Active Recall & Evidentiary Gate Station</h3>
          <p>Select a locus or press <b>[Space]</b> to load next decaying node.</p>
          <div id="active-locus-view"></div>
        </div>
      </div>
      <script>
        let startTime = Date.now();
        let currentLocus = null;

        function selectLocus(id) {{
          startTime = Date.now();
          currentLocus = id;
          fetch('/api/locus/' + id)
            .then(r => r.json())
            .then(data => {{
              const stage = data.competency_stage || 1;
              const sceneHtml = stage < 4
                ? `<div class="kinetic-box">${{data.scene_narrative || ''}}</div>`
                : `<div class="kinetic-box"><i>[Stage 4 Production Instinct Active: Mnemonic scaffolding retired]</i></div>`;
              document.getElementById('active-locus-view').innerHTML = `
                <div class="stage-banner">Competency Gate: Stage ${{stage}} / 4</div>
                <h4>${{data.name}}</h4>
                ${{sceneHtml}}
                <p><b>Major System Pegs:</b> ${{JSON.stringify(data.encoded_limits || [])}}</p>
                <p><b>Confusion Pairs:</b> ${{(data.confusion_pairs || []).join(', ') || 'None'}}</p>
                <p><b>Evidentiary Synthesis (Boundary / Trade-offs / Failure Modes):</b></p>
                <textarea id="evidence-input" rows="3" placeholder="Explain why adjacent services fail, cost/latency/blast-radius trade-offs, and failure mode mitigations (DLQ, idempotency, failover)..."></textarea>
                <p>Rate your instant retrieval (Keys 1-5) or submit Evidence Gate:</p>
                <button onclick="submitScore(1)">1 (Blackout)</button>
                <button onclick="submitScore(3)">3 (Strained)</button>
                <button onclick="submitScore(5)">5 (Instant)</button>
                <button onclick="submitCompetencyEvidence()" style="background:#1f6feb;">Evaluate Competency Gate</button>
              `;
            }});
        }}

        function loadNextDecaying() {{
          fetch('/api/drill/next')
            .then(r => r.json())
            .then(data => {{
              if (data && data.id) selectLocus(data.id);
            }});
        }}

        function submitScore(score) {{
          if (!currentLocus) return;
          const latency = Date.now() - startTime;
          fetch('/api/drill/submit', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{ locus_id: currentLocus, score: score, latency_ms: latency }})
          }}).then(() => {{
            alert(`Recall recorded in ${{latency}}ms. Updating telemetry.`);
            location.reload();
          }});
        }}

        function submitCompetencyEvidence() {{
          if (!currentLocus) return;
          const latency = Date.now() - startTime;
          const responseText = (document.getElementById('evidence-input') || {{}}).value || '';
          fetch('/api/competency/evaluate', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{ locus_id: currentLocus, response_text: responseText, latency_ms: latency }})
          }})
          .then(r => r.json())
          .then(res => {{
            alert(`[${{res.action}}] Stage ${{res.stage_before}} -> Stage ${{res.stage_after}}: ${{res.reason}}`);
            location.reload();
          }});
        }}

        document.addEventListener('keydown', (e) => {{
          if (e.target && e.target.tagName === 'TEXTAREA') return;
          if (e.code === 'Space') {{
            e.preventDefault();
            loadNextDecaying();
          }} else if (['1', '2', '3', '4', '5'].includes(e.key) && currentLocus) {{
            submitScore(parseInt(e.key, 10));
          }}
        }});
      </script>
    </body>
    </html>
    """


@app.get("/api/locus/{locus_id}")
def get_locus(locus_id: str):
    with open("data/palace_map.json", "r", encoding="utf-8") as f:
        palace = json.load(f)
    for l in palace["loci"]:
        if l["id"] == locus_id:
            return l
    return JSONResponse(status_code=404, content={"error": "Not found"})


@app.get("/api/drill/next")
def get_next_drill():
    with open("data/palace_map.json", "r", encoding="utf-8") as f:
        palace = json.load(f)
    loci = sorted(
        palace.get("loci", []),
        key=lambda l: (
            l.get("competency_stage", 1),
            l.get("stability_score", 0.5),
            l.get("next_due", "9999-12-31"),
        ),
    )
    if not loci:
        return JSONResponse(status_code=404, content={"error": "No loci configured"})
    return loci[0]


@app.post("/api/drill/submit")
async def submit_drill(req: Request):
    payload = await req.json()
    locus_id = payload["locus_id"]
    score = int(payload["score"])
    latency_ms = int(payload["latency_ms"])
    distractor = payload.get("distractor_selected")
    tradeoffs = payload.get("tradeoffs_addressed", [])
    failure_modes = payload.get("failure_modes_mitigated", [])
    boundary_passed = payload.get("correct_boundary_identified", score >= 3)

    with open("data/palace_map.json", "r", encoding="utf-8") as f:
        palace = json.load(f)

    stage_before = 1
    stage_after = 1

    for locus in palace.get("loci", []):
        if locus["id"] == locus_id:
            stage_before = int(locus.get("competency_stage", 1))
            evidence = CompetencyEvidence(
                factual_latency_ms=latency_ms,
                correct_boundary_identified=bool(boundary_passed),
                tradeoffs_addressed=tradeoffs,
                failure_modes_mitigated=failure_modes,
            )
            gate_outcome = CompetencyGate(locus_id, stage_before).evaluate_promotion(evidence)
            stage_after = gate_outcome["new_stage"]
            locus["competency_stage"] = stage_after

            rep, ef, interval = calculate_sm2(
                locus.get("repetitions", 0),
                locus.get("ease_factor", 2.5),
                locus.get("interval_days", 1),
                score,
            )
            locus["repetitions"] = rep
            locus["ease_factor"] = ef
            locus["interval_days"] = interval
            locus["next_due"] = (
                datetime.now(timezone.utc) + timedelta(days=interval)
            ).strftime("%Y-%m-%d")
            weight = (score - 3) * 0.1
            locus["stability_score"] = round(
                max(0.1, min(1.0, locus.get("stability_score", 0.75) + weight)), 2
            )
            break

    with open("data/palace_map.json", "w", encoding="utf-8") as f:
        json.dump(palace, f, indent=2)
        f.write("\n")

    record_interaction(
        locus_id=locus_id,
        latency_ms=latency_ms,
        score=score,
        distractor=distractor,
        stage_before=stage_before,
        stage_after=stage_after,
        boundary_passed=bool(boundary_passed),
        tradeoffs_logged=tradeoffs,
        failure_modes_logged=failure_modes,
    )

    return {
        "status": "recorded",
        "locus_id": locus_id,
        "score": score,
        "latency_ms": latency_ms,
        "stage_before": stage_before,
        "stage_after": stage_after,
    }


@app.post("/api/competency/evaluate")
async def evaluate_competency(req: Request):
    payload = await req.json()
    locus_id = payload["locus_id"]
    response_text = payload.get("response_text", "")
    latency_ms = int(payload.get("latency_ms", 2000))

    with open("data/palace_map.json", "r", encoding="utf-8") as f:
        palace = json.load(f)
    distractors = []
    for loc in palace.get("loci", []):
        if loc["id"] == locus_id:
            distractors = loc.get("confusion_pairs", [])
            break

    rubric_result = evaluate_candidate_response(response_text, distractors=distractors)
    evidence = rubric_to_evidence(rubric_result, factual_latency_ms=latency_ms)
    transition = apply_competency_transition(locus_id, evidence)

    record_interaction(
        locus_id=locus_id,
        latency_ms=latency_ms,
        score=5 if evidence.correct_boundary_identified else 2,
        stage_before=transition["stage_before"],
        stage_after=transition["stage_after"],
        boundary_passed=evidence.correct_boundary_identified,
        tradeoffs_logged=evidence.tradeoffs_addressed,
        failure_modes_logged=evidence.failure_modes_mitigated,
    )

    return {
        **transition,
        "rubric": rubric_result,
    }


@app.get("/api/metrics")
def get_metrics():
    return get_telemetry_metrics()
