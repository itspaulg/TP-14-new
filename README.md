# TP-I014 — ABSA UMKM F&B Medan

Capstone Tempa Dicoding, tema Smart Business & UMKM Empowerment.
Tim: AIC834B6Y0001 — Paulus George Sirait (AI).

Sistem intelijen kompetitif untuk pemilik UMKM F&B berbasis Aspect-Based
Sentiment Analysis dari review Google Maps. Output: insight per aspek
(rasa, harga, pelayanan) lintas kompetitor + rekomendasi taktis berbasis
rule-based engine.

Studi kasus proof-of-concept: 9 UMKM nasi goreng iconic di Medan (kategori
sama supaya comparative analysis fair).

## Struktur

```
gmaps_scraper/   Pipeline scraping Google Maps reviews (Playwright)
absa/            Fine-tuning IndoBERT untuk 3-aspect ABSA
analytics/       Comparative benchmarking + rule-based recommendation engine
dashboard/       Next.js dashboard untuk visualisasi (+ search box + live analyze)
api/             FastAPI backend untuk live analyze (scrape+inference on demand)
```

Masing-masing folder ada README sendiri dengan detail.

## Dua mode pakai

1. **Dashboard statis** (instan): overview heatmap, detail per UMKM, dan
   recommendations dibaca dari hasil pipeline yg sudah di-precompute. Ada
   search box untuk lompat ke UMKM mana pun di database. Ini cara utama
   demo — semua instan karena data sudah jadi.

2. **Live analyze** (on demand, ~1-2 menit): halaman `/analyze` menerima URL
   Google Maps UMKM F&B apa pun → backend scrape review → IndoBERT inference
   → bandingkan dengan median pasar → rekomendasi. Butuh backend FastAPI
   jalan (`cd api && uvicorn main:app --port 8000`). Tidak instan karena
   scraping butuh waktu nyata.

## Flow data end-to-end

```
gmaps_scraper/scrape.py    →  output/raw/<umkm>.csv  (1716 review)
absa/prepare_data.py       →  data/pool.csv (847)  +  data/sample.csv
absa/annotate.py + annotate_context.py → data/labels.jsonl (506, rule-based context-aware)
absa/train.py              →  models/indobert-absa/ (macro-F1 0.696, weighted ~0.82)
absa/predict.py            →  data/predictions.csv  (847 inference)
analytics/analyze.py       →  snapshot.json + report.md
analytics/recommend.py     →  recommendations.json + .md
dashboard/ (Next.js)       →  visualisasi interaktif
```

## Hasil akhir

| Deliverable | Status | Artefak |
|---|---|---|
| 1. Data collection | ✓ | 1716 review (847 with text), 9 UMKM |
| 2. ABSA model | ✓ | IndoBERT, 506 labels, macro-F1 0.696 / weighted-F1 ~0.82 |
| 3. Analytics engine | ✓ | snapshot.json + leaderboard per aspek |
| 4. Recommendation engine | ✓ | rule-based templates, 6 strategy codes |
| 5. Dashboard | ✓ | Next.js 4 page (overview / per-UMKM / recommendations / analyze) + search box |
| Bonus. Live analyze | ✓ | api/ FastAPI: paste URL → scrape + inference on demand |

## Quick start

```bash
# Setup semua dependencies
pip install -r gmaps_scraper/requirements.txt
python3 -m playwright install chromium
pip3 install --user -r absa/requirements.txt
cd dashboard && npm install && cd ..

# Run dashboard (data sudah ada di repo)
cd dashboard && npm run dev
# → http://localhost:3000

# (opsional) Run backend untuk fitur live analyze
pip3 install --user -r api/requirements.txt
cd api && python3 -m uvicorn main:app --port 8000
```

> Catatan: model weights (`absa/models/indobert-absa/`) dan `node_modules`
> tidak di-commit (terlalu besar). Regenerate dengan
> `cd absa && python3 train.py --epochs 5 --no-class-weight` dan
> `cd dashboard && npm install`. Live analyze butuh model weights ini.

## Stack

- Python 3.13 (scraping, ML, analytics)
- Playwright 1.60 (Google Maps scraping)
- PyTorch 2.12 + transformers 5.9 + sentencepiece
- IndoBERT base p1 (indobenchmark)
- scikit-learn (eval metrics)
- Node.js 24 + Next.js 16 + Tailwind v4 + Recharts (dashboard)
- Apple Silicon MPS untuk training (CPU fallback tersedia)

## Lisensi & data

Data review adalah konten publik dari Google Maps, di-scrape untuk
kepentingan akademis (capstone). Tidak ada PII identification beyond public
author display name. Repo dibuat untuk submission capstone Tempa Dicoding.
