# engine/server.py
import json
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from engine.adaptive_srs import calculate_sm2
from engine.db import get_telemetry_metrics, init_db, record_interaction

app = FastAPI(title="Palace Deck")
init_db()


@app.get("/", response_class=HTMLResponse)
def index():
    with open("data/palace_map.json", "r", encoding="utf-8") as f:
        palace = json.load(f)

    loci_items = "".join(
        [
            f"<div class='locus-item' onclick='selectLocus(\"{l['id']}\")'>"
            f"<b>{l['name']}</b> <span class='badge'>{int(l.get('stability_score', 0.8) * 100)}%</span>"
            f"<br><small>{', '.join(l['aws_services'])}</small></div>"
            for l in palace["loci"]
        ]
    )

    # Minimalist, keyboard-first visual UI built for tiling managers
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Palace Deck // SAA-C03 Control</title>
      <style>
        body {{ background: #0f111a; color: #e6edf3; font-family: monospace; margin: 2rem; }}
        .grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 2rem; }}
        .card {{ background: #161b22; border: 1px solid #30363d; padding: 1.5rem; border-radius: 8px; }}
        .badge {{ background: #238636; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; float: right; }}
        .locus-item {{ padding: 0.75rem; border-bottom: 1px solid #21262d; cursor: pointer; }}
        .locus-item:hover {{ background: #1f242c; }}
        .kinetic-box {{ border-left: 3px solid #f78166; padding-left: 1rem; margin: 1rem 0; color: #ffab70; }}
        button {{ background: #238636; color: white; border: none; padding: 0.6rem 1.2rem; cursor: pointer; border-radius: 4px; margin-right: 0.5rem; }}
      </style>
    </head>
    <body>
      <h2>[PALACE-DECK] AWS SAA Cognitive Ingestion Engine</h2>
      <div class="grid">
        <div class="card">
          <h3>Memory Loci</h3>
          <div id="loci-list">
            {loci_items}
          </div>
        </div>
        <div class="card" id="detail-panel">
          <h3>Active Recall Station</h3>
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
              document.getElementById('active-locus-view').innerHTML = `
                <h4>${{data.name}}</h4>
                <div class="kinetic-box">${{data.scene_narrative || ''}}</div>
                <p><b>Major System Pegs:</b> ${{JSON.stringify(data.encoded_limits || [])}}</p>
                <p><b>Confusion Pairs:</b> ${{(data.confusion_pairs || []).join(', ') || 'None'}}</p>
                <p>Rate your instant retrieval (Keys 1-5):</p>
                <button onclick="submitScore(1)">1 (Blackout)</button>
                <button onclick="submitScore(3)">3 (Strained)</button>
                <button onclick="submitScore(5)">5 (Instant)</button>
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

        document.addEventListener('keydown', (e) => {{
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
        key=lambda l: (l.get("stability_score", 0.5), l.get("next_due", "9999-12-31")),
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

    record_interaction(
        locus_id=locus_id,
        latency_ms=latency_ms,
        score=score,
        distractor=distractor,
    )

    # Also calibrate SM-2 interval in palace_map.json
    with open("data/palace_map.json", "r", encoding="utf-8") as f:
        palace = json.load(f)
    for locus in palace.get("loci", []):
        if locus["id"] == locus_id:
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

    return {"status": "recorded", "locus_id": locus_id, "score": score, "latency_ms": latency_ms}


@app.get("/api/metrics")
def get_metrics():
    return get_telemetry_metrics()
