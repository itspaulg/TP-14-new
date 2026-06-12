# api — live analyze backend

FastAPI backend untuk fitur "analyze UMKM baru" di dashboard. Terima 1 URL
Google Maps → scrape review → IndoBERT inference per aspek → bandingkan
dengan median pasar → strategy code + rekomendasi.

Reuse 100% logic dari pipeline:
- scraping: `gmaps_scraper/scrape.py` (dipanggil sebagai subprocess)
- model: `absa/models/indobert-absa/` (di-load sekali saat startup)
- strategy + template: `analytics/analyze.py` + `analytics/recommend.py`

## Setup

```bash
pip3 install --user -r requirements.txt
# torch, transformers, playwright sudah terinstall dari pipeline
```

Pastikan model weights sudah ada di `absa/models/indobert-absa/`. Kalau belum:
`cd ../absa && python3 train.py --epochs 5 --no-class-weight`.

## Jalankan

```bash
cd api
python3 -m uvicorn main:app --port 8000
```

Tunggu sampai log `[startup] ready` (model loading ~10 detik).

## Endpoint

`GET /health` → `{"status":"ok","device":"mps"}`

`POST /analyze`
```json
{ "url": "https://www.google.com/maps/place/...", "name": "optional", "target": 80 }
```
Return: per-aspek positive_share, strategy code, rationale, actionable, +
market median pembanding.

## Catatan teknis

- **Tidak instan**: scraping butuh ~1-2 menit. Frontend nampilin loading state.
- **Subprocess scrape**: scrape.py dijalankan sebagai proses terpisah, bukan
  Playwright sync API di dalam threadpool FastAPI (yg bermasalah). Ini juga
  pakai headed browser (Google Maps serve headless layout berbeda yg
  selector review-tab-nya nggak match).
- **Default target 80**: target kecil (<40) sering bikin aspek harga/pelayanan
  jadi NO_DATA karena volume mention di bawah threshold 5. Pakai 80+ untuk
  hasil lebih lengkap.
- **CORS**: dibuka untuk semua origin (local dev tool, no auth).
- Market median pembanding dihitung dari 9 UMKM nasi goreng — untuk kategori
  F&B lain ada domain shift (akurasi & relevansi benchmark berkurang).
