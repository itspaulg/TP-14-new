# gmaps_scraper

Scraper Google Maps reviews untuk capstone TP-I014 (ABSA UMKM F&B di Medan).
Tujuannya simpel: kasih 1 URL Maps + nama UMKM (slug), output CSV dengan
kolom `umkm_id, author, rating, date_relative, text`.

## Setup

Sekali doang di awal:

```bash
pip install -r requirements.txt
python3 -m playwright install chromium
```

Python 3.13 di Mac (Apple Silicon).

## Cara pakai

Mode interaktif (paling gampang):

```bash
python3 scrape.py
```

Nanti dia minta URL Maps + slug UMKM.

Mode CLI kalau mau lebih cepat:

```bash
python3 scrape.py --url "https://www.google.com/maps/place/..." --id nasi_goreng_surya
python3 scrape.py --url "..." --id naste --target 300
python3 scrape.py --url "..." --id naste --headless
```

Default target 200 review. Kalau total review di Maps lebih sedikit dari
target, scraper berhenti otomatis setelah 12 iterasi tanpa progress.

## Rotasi akun

Setiap profile = folder browser sendiri. Cookies dan login session
tersimpan terpisah. Berguna kalau perlu rotasi akun Google buat menghindari
rate limit:

```bash
python3 scrape.py --url "..." --id surya --profile akun1
python3 scrape.py --url "..." --id komdak --profile akun2
```

Pertama kali pakai profile baru, scraper otomatis klik "Tolak semua" di
consent.google.com. Kalau mau login ke akun Google, jalanin di headed mode,
login manual di window yg muncul, terus close — sesi tersimpan untuk run
berikutnya.

## Output

Kolomnya:

- `umkm_id` — slug yg di-pass via `--id`
- `author` — nama reviewer
- `rating` — 1–5 (kosong kalau parse gagal)
- `date_relative` — label "X hari/bulan lalu" dari Maps
- `text` — isi review (bisa kosong, sekitar 50% review di Maps emang
  rate-only tanpa teks — pattern normal)

Filter teks-kosong di preprocessing kalau ABSA butuh text aja.

## Troubleshooting

- Stuck di consent.google.com → run headed (tanpa `--headless`), klik
  Tolak semua manual sekali. Profile cookies tersimpan, run berikutnya
  skip otomatis.
- Tidak ada `[data-review-id]` di DOM → URL salah atau place memang gak
  punya review. Cek URL di browser dulu.
- Cuma dapat sedikit review walaupun target 200 → place memang punya
  review sedikit di Maps. Cek total review di sidebar Maps.
- Stuck di angka tertentu (mis. 73/200, stagnant) → semua review sudah
  ke-load, scraper auto-stop.
- Browser minta CAPTCHA → rate-limit. Switch ke `--profile` baru atau
  istirahat sejam.

## Catatan implementasi

Beberapa detail teknis yg perlu diingat:

Sort: review di-sort by "Terbaru" supaya deterministic dan dapat fresh
data. Kalau pakai "Paling Relevan" urutan bisa berubah-ubah, susah
reproduksi.

Virtualisasi DOM: Maps menghapus review item lama dari DOM saat di-scroll
jauh ke bawah. Saya extract incremental tiap iterasi scroll, bukan sekali
di akhir, supaya nggak ada review yg hilang dari virtualisasi.

Selector multi-bahasa: locale di-set id-ID tapi selector saya bikin
match aria-label Indonesia + English (case-insensitive) jadi tetap jalan
kalau profile login default English.

Anti-bot: persistent context + `--disable-blink-features=AutomationControlled`.
Untuk volume kecil 9 UMKM × 200 = 1800 review, ini cukup. Lebih dari itu
mungkin perlu proxy rotation.

URL pattern: Google Maps URL ada 2 varian. Yg simpel adalah direct place
URL (data flag `!3m1!4b1!4m6!3m5...`). Yg search-style (data flag `!4m10!1m2!2m1!1s...<query>`)
load 2 panel (search results di kiri, place di kanan). Awalnya scraper saya
salah scroll feed di kiri (cuma dapat 10 review search result), saya
fix dengan filter `[role="feed"]` yg mengandung `[data-review-id]`.
