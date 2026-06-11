# TP-I014 — ABSA UMKM F&B Medan

Capstone Tempa Dicoding, tema Smart Business & UMKM Empowerment.
Tim: AIC834B6Y0001 — Paulus George Sirait (AI track).

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
dashboard/       Next.js dashboard untuk visualisasi
docs/            Demo script, slide content, validation form
```

Masing-masing folder ada README sendiri dengan detail.

## Flow data end-to-end

```
gmaps_scraper/scrape.py    →  output/raw/<umkm>.csv  (1716 review)
absa/prepare_data.py       →  data/pool.csv (847)  +  data/sample.csv (276)
absa/annotate.py           →  data/labels.jsonl
absa/train.py              →  models/indobert-absa/ (macro-F1 0.7556)
absa/predict.py            →  data/predictions.csv  (847 inference)
analytics/analyze.py       →  snapshot.json + report.md
analytics/recommend.py     →  recommendations.json + .md
dashboard/ (Next.js)       →  visualisasi interaktif
```

## Hasil akhir

| Deliverable | Status | Artefak |
|---|---|---|
| 1. Data collection | ✓ | 1716 review (847 with text), 9 UMKM |
| 2. ABSA model | ✓ | IndoBERT macro-F1 0.7556, weighted-F1 0.835 |
| 3. Analytics engine | ✓ | snapshot.json + leaderboard per aspek |
| 4. Recommendation engine | ✓ | rule-based templates, 6 strategy codes |
| 5. Dashboard | ✓ | Next.js 3 page (overview / per-UMKM / recommendations) |
| 6. Validation | ✓ | Google Form survey (lihat docs/) |
| 7. Docs + demo + deck | ✓ | docs/demo_script.md + docs/slide_content.md |

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
```

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
