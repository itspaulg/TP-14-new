# TP-I014 — ABSA UMKM F&B Medan

Capstone Tempa Dicoding, tema Smart Business & UMKM Empowerment.
Tim: AIC834B6Y0001 - Paulus George Sirait (AI track).

Sistem intelijen kompetitif untuk pemilik UMKM F&B berbasis Aspect-Based
Sentiment Analysis dari review Google Maps. Output: insight per aspek
(rasa, harga, pelayanan) lintas kompetitor + rekomendasi taktis.

Studi kasus untuk proof-of-concept: 9 UMKM nasi goreng iconic di Medan.

## Struktur

Repo ini terdiri dari 3 komponen yg dijalankan berurutan:

```
gmaps_scraper/   Pipeline scraping Google Maps reviews (Playwright)
absa/            Fine-tuning IndoBERT untuk 3-aspect ABSA
analytics/       Comparative benchmarking + rule-based recommendation engine
```

Masing-masing folder ada README sendiri dengan detail cara pakai.

## Flow data end-to-end

```
gmaps_scraper/scrape.py  --[per UMKM]-->  output/raw/<umkm>.csv  (1716 review)
                                          |
absa/prepare_data.py  --[concat+filter]-->  data/pool.csv  (847 review w/ text)
                                          |
                              data/sample.csv  (276 stratified, untuk anotasi)
                                          |
absa/annotate.py  --[manual labeling]-->  data/labels.jsonl
                                          |
absa/train.py  --[fine-tune IndoBERT]-->  models/indobert-absa/
                                          |
absa/predict.py  --[inference all 847]-->  data/predictions.csv
                                          |
analytics/analyze.py  --[aggregate]-->  snapshot.json + report.md
                                          |
analytics/recommend.py  --[rule-based]-->  recommendations.json + .md
```

## Hasil ringkas

Data: 1716 review dari 9 UMKM (847 punya teks).
Model: IndoBERT fine-tuned, macro-F1 0.7556, weighted-F1 0.835.
Analytics: market median + leaderboard per aspek lintas UMKM.
Recommendation: 6 strategy code (ATTACK / FIX / DEFEND / PROMOTE / MONITOR / NO_DATA)
per (UMKM, aspek), masing-masing dengan rationale + actionable items.

Detail metric dan diskusi: `analytics/checkpoint_w4.md` (mid-checkpoint report).

## Setup

Dependencies:

```bash
# scraper
pip install -r gmaps_scraper/requirements.txt
python3 -m playwright install chromium

# ABSA model
pip3 install --user -r absa/requirements.txt
```

Python 3.13 di Mac Apple Silicon (MPS untuk training). Bisa juga jalan di
CPU dengan flag `--no-mps` di train.py / predict.py.

## Stack

- Python 3.13, Playwright 1.60 (scraping)
- PyTorch 2.12 + transformers 5.9 + sentencepiece (NLP)
- IndoBERT base p1 dari indobenchmark/IndoBenchmark
- scikit-learn (eval metrics)

## Lisensi & data

Data review adalah konten publik dari Google Maps. Scraping dilakukan untuk
kepentingan akademis (capstone). Tidak ada PII identification beyond
public author display name.
