# dashboard

Frontend dashboard untuk capstone TP-I014. Next.js 16 app router +
Tailwind v4 + Recharts. Load data static dari JSON yg di-generate oleh
analytics engine — no backend, no database, no auth.

## Page yg tersedia

- `/` — overview: market median KPI, heatmap UMKM × aspek, leaderboard per
  aspek.
- `/umkm/[id]` — detail per UMKM: KPI aspek, distribusi sentimen (stacked
  bar), recommendation playbook 3 aspek, drill-down review list dengan
  filter aspek + sentimen.
- `/recommendations` — playbook lintas UMKM diurut by priority (ATTACK
  paling atas), filter by strategy code dan aspek.

## Setup

```bash
cd dashboard
npm install
npm run dev
```

Dashboard jalan di http://localhost:3000.

## Build static (production)

```bash
npm run build
npm run start
```

## Sumber data

Data di-import langsung sebagai static JSON dari `src/data/`:

- `snapshot.json` — output dari `analytics/analyze.py`
- `recommendations.json` — output dari `analytics/recommend.py`
- `predictions.json` — converted dari `absa/data/predictions.csv`

Kalau model di-retrain, regenerate:

```bash
cd ../absa && python3 predict.py
cd ../analytics && python3 analyze.py && python3 recommend.py
cp ../analytics/snapshot.json ../analytics/recommendations.json src/data/
python3 -c "import csv, json; rows=list(csv.DictReader(open('../absa/data/predictions.csv'))); json.dump(rows, open('src/data/predictions.json','w'), ensure_ascii=False)"
```

## Catatan teknis

Pakai Next.js 16 app router. `params` di dynamic route adalah Promise jadi
harus di-await (breaking change dari versi sebelumnya).

`generateStaticParams` di `/umkm/[id]` dipakai supaya semua 9 page UMKM bisa
di-prerender static — nantinya bisa di-deploy ke Vercel/Netlify tanpa
runtime cost.

Chart pakai Recharts (client component). Sisa page server component supaya
JSON di-bundle ke server-rendered HTML, no client-side fetch.

Color gradient heatmap dari merah (positive_share 0%) → amber (50%) →
hijau (100%). Cell dengan volume < 5 di-dim opacity karena data tidak
signifikan.
