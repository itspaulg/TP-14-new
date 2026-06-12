"""
Live-analyze backend untuk TP-I014.

Terima 1 URL Google Maps → scrape review → IndoBERT inference per aspek →
aggregate jadi positive_share → bandingkan dengan median pasar →
strategy code + rekomendasi. Return JSON.

Reuse 100% logic dari pipeline yg sudah ada:
- scrape: gmaps_scraper/scrape.py (collect_for_url)
- model: absa/models/indobert-absa
- strategy + template: analytics/analyze.py + recommend.py

Jalankan:
  cd api && pip install -r requirements.txt
  uvicorn main:app --reload --port 8000

CATATAN: tidak instan — scraping butuh ~1-2 menit. Endpoint sync (jalan di
threadpool) supaya kompatibel dengan Playwright sync API.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "analytics"))

from analyze import assign_strategy, ASPECTS, MIN_VOLUME  # noqa: E402
from recommend import RATIONALES, ACTIONABLES, FALLBACK_ACTIONS, render_rationale  # noqa: E402

SCRAPER = ROOT / "gmaps_scraper" / "scrape.py"
SCRAPE_OUT_DIR = ROOT / "gmaps_scraper" / "output" / "raw"


def scrape_via_subprocess(url: str, target: int, slug: str = "_live") -> tuple[str, list[dict]]:
    """Run scrape.py as a separate process (proven CLI path), then read the CSV.
    Avoids running Playwright sync API inside the FastAPI threadpool."""
    out_path = SCRAPE_OUT_DIR / f"{slug}.csv"
    if out_path.exists():
        out_path.unlink()
    proc = subprocess.run(
        [sys.executable, str(SCRAPER), "--url", url, "--id", slug, "--target", str(target)],
        cwd=str(SCRAPER.parent),
        capture_output=True,
        text=True,
        timeout=600,
    )
    title = ""
    for line in proc.stdout.splitlines():
        if line.startswith("[place]"):
            title = line.split("[place]", 1)[1].strip().strip("'\"")
    if not out_path.exists():
        return title, []
    rows = list(csv.DictReader(out_path.open(encoding="utf-8")))
    out_path.unlink()  # cleanup
    reviews = [
        {"text": r.get("text", ""), "rating": r.get("rating", ""), "author": r.get("author", "")}
        for r in rows
    ]
    return title, reviews

MODEL_DIR = ROOT / "absa" / "models" / "indobert-absa"
SNAPSHOT = ROOT / "analytics" / "snapshot.json"

# ---------- load once at startup ----------

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")

print(f"[startup] device={DEVICE}")
print(f"[startup] loading model from {MODEL_DIR}")
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR)).to(DEVICE).eval()
ID2LABEL = model.config.id2label

snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
MARKET = snapshot["market"]
print("[startup] ready")


def make_input(text: str, aspect: str) -> str:
    return f"[ASPEK: {aspect}] {text}"


def predict_aspect(texts: list[str], aspect: str, batch_size: int = 32) -> list[str]:
    out: list[str] = []
    inputs = [make_input(t, aspect) for t in texts]
    for i in range(0, len(inputs), batch_size):
        chunk = inputs[i : i + batch_size]
        enc = tokenizer(
            chunk, truncation=True, padding=True, max_length=192, return_tensors="pt"
        ).to(DEVICE)
        with torch.no_grad():
            logits = model(**enc).logits
        for p in logits.argmax(-1).cpu().numpy():
            out.append(ID2LABEL[int(p)])
    return out


# ---------- app ----------

app = FastAPI(title="TP-I014 Live Analyze API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev tool, no auth — any localhost port OK
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    url: str
    name: str | None = None
    target: int = 80


@app.get("/health")
def health():
    return {"status": "ok", "device": str(DEVICE)}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL kosong")

    # 1. scrape via subprocess (~1-2 menit). Runs scrape.py as a separate
    #    process — the proven CLI path — instead of Playwright sync API inside
    #    the FastAPI threadpool (which serves headless a broken layout).
    try:
        title, reviews = scrape_via_subprocess(req.url, target=req.target)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Scraping timeout (>10 menit).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping gagal: {e}")

    name = (req.name or title or "UMKM").strip()
    with_text = [
        (r.get("text") or "").strip()
        for r in reviews
        if (r.get("text") or "").strip()
    ]
    if not with_text:
        raise HTTPException(
            status_code=422,
            detail="Tidak ada review berteks ditemukan. Cek URL atau place mungkin belum punya review.",
        )

    # 2. inference per aspek
    aspect_results = {}
    for asp in ASPECTS:
        labels = predict_aspect(with_text, asp)
        pos = labels.count("positif")
        neg = labels.count("negatif")
        neu = labels.count("netral")
        td = labels.count("tidak_disebut")
        volume = pos + neg + neu
        decisive = pos + neg
        pshare = (pos / decisive) if decisive else None
        net = (pos - neg) / volume if volume else None
        market_share = MARKET[asp]["median_positive_share"]
        code = assign_strategy(pshare, volume, decisive, market_share)

        template = RATIONALES.get((asp, code), "")
        asp_data = {
            "positive_share": pshare,
            "volume": volume,
            "positif": pos,
            "negatif": neg,
        }
        rationale = (
            render_rationale(template, name, asp_data, market_share) if template else ""
        )
        actionable = ACTIONABLES.get((asp, code), FALLBACK_ACTIONS.get(code, []))

        aspect_results[asp] = {
            "positif": pos,
            "negatif": neg,
            "netral": neu,
            "tidak_disebut": td,
            "volume": volume,
            "decisive": decisive,
            "positive_share": pshare,
            "net_sentiment": net,
            "market_share": market_share,
            "strategy": code,
            "rationale": rationale,
            "actionable": list(actionable),
        }

    return {
        "name": name,
        "place_title": title,
        "review_count": len(reviews),
        "with_text": len(with_text),
        "min_volume_threshold": MIN_VOLUME,
        "market": {a: MARKET[a]["median_positive_share"] for a in ASPECTS},
        "aspects": aspect_results,
    }
