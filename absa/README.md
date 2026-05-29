# absa

Pipeline ABSA pakai IndoBERT untuk 3 aspek inti F&B: rasa, harga, pelayanan.
Output per aspek: 4-class (positif / negatif / netral / tidak_disebut).

Bagian dari TP-I014 (deliverable #2).

## Struktur

```
absa/
├── prepare_data.py    9 raw CSV → pool.csv + stratified sample.csv
├── annotate.py        CLI annotation tool, bisa di-resume
├── train.py           fine-tune indobenchmark/indobert-base-p1
├── predict.py         inference di full pool
├── requirements.txt
├── data/
│   ├── pool.csv         847 review dengan teks (sudah dedupe)
│   ├── sample.csv       276 stratified per rating
│   ├── labels.jsonl     hasil anotasi
│   └── predictions.csv  hasil inference (setelah train)
└── models/
    ├── indobert-absa/   checkpoint terbaik
    └── eval_report.json metric F1 per aspek
```

## Setup

```bash
pip3 install --user -r requirements.txt
```

Python 3.13, torch 2.12, transformers 5.9. Apple Silicon MPS untuk training.

## Workflow

### 1. Data prep

```bash
python3 prepare_data.py
```

Concat 9 CSV dari `gmaps_scraper/output/raw/`, filter review yg ada teksnya,
dedupe by hash (umkm + author + date + text prefix), stratified sample per
rating star untuk anotasi.

Default: target 60 per rating star, total ~300 (cuma 276 yg ke-fill karena
rating 2 cuma punya 36 review).

### 2. Anotasi manual

```bash
python3 annotate.py
```

Per review, ketik 3 digit untuk rasa, harga, pelayanan:

- 1 = positif (aspek disebut + dipuji)
- 2 = negatif (aspek disebut + dikeluh)
- 3 = netral (aspek disebut tanpa penilaian)
- 0 = tidak disebut

Contoh:
- "111" semua positif
- "200" rasa negatif aja, lainnya tidak disebut
- "012" rasa TD, harga positif, pelayanan negatif

Command: `s` skip, `b` undo, `q` quit (auto-save).

Saya pakai ~10 detik per review untuk yg pendek, ~30 detik untuk yg panjang.
Total 276 review sekitar 45-60 menit. Bisa di-pause kapan aja terus lanjut
dari yg belum dilabel.

### 3. Train

```bash
python3 train.py                   # default 5 epoch, lr 2e-5, batch 16
python3 train.py --epochs 8
python3 train.py --batch 8 --lr 1e-5
```

Auto pakai MPS kalau ada (Apple Silicon GPU), fallback CPU dengan `--no-mps`.

Best checkpoint auto-save tiap epoch yg F1 meningkat. Output:
- `models/indobert-absa/` model + tokenizer
- `models/eval_report.json` metric per aspek

### 4. Iterasi kalau F1 rendah

Cek per-aspek F1 di console output dan eval_report.json. Common cause:
class imbalance kalau jumlah label per kelas variansinya tinggi. Misalnya
saya dapat distribusi:

- rasa: pos 81, neg 30, neu 51, td 114
- harga: pos 21, neg 22, neu 14, td 219
- pelayanan: pos 23, neg 40, neu 6, td 207

Harga dan pelayanan dominasi tidak_disebut (kebanyakan review nggak nyebut
aspek itu). Untuk kelas minoritas (mis. pelayanan.netral cuma 6), F1 jadi
nggak stabil dengan 276 sample.

Yg saya coba dan hasilnya:
- 5 epoch tanpa class weight → macro-F1 0.7556 (best)
- 10 epoch tanpa class weight → 0.7321 (overfit, loss turun terus tapi F1 turun)
- 10 epoch dengan balanced class weight → 0.6246 (over-correct minority)

Pelajaran: class weights di dataset kecil + imbalanced sering malah turunkan
F1 karena model jadi terlalu fokus minority class.

### 5. Predict di full pool

```bash
python3 predict.py
```

Inference di semua 847 review yg ada teksnya. Output `data/predictions.csv`
dengan 3 kolom aspek hasil prediksi. Ini input untuk analytics + recommendation
engine.

## Format file

`labels.jsonl` 1 baris per review:

```json
{"review_id":"...","umkm_id":"naste","rating":"4","text":"...","rasa":"positif","harga":"tidak_disebut","pelayanan":"negatif"}
```

`predictions.csv` 1 row per review dengan kolom umkm_id, rating, rasa, harga,
pelayanan, text.

## Catatan teknis

Model: indobenchmark/indobert-base-p1, ~110M params, pretrained Bahasa
Indonesia (Wikipedia + news + Common Crawl Indonesia).

Pendekatan: aspect-injection. Input ke model `"[ASPEK: rasa] <teks review>"`,
output 4-class softmax. Satu model handle 3 aspek (training data triple
karena 1 review jadi 3 example). Lebih efektif daripada train 3 model
terpisah dengan dataset kecil.

Stratified train/test split 80/20 by (aspek, label) supaya minority class
juga ada di test set.

Loss: CrossEntropy biasa. Optimizer: AdamW, lr=2e-5 linear schedule dengan
10% warmup. Gradient clipping 1.0.

Training time di M-series Mac dengan MPS: sekitar 5-7 menit untuk 5 epoch
× 828 samples (276 × 3 aspek).

Eval pakai macro-F1 dan weighted-F1. Macro treat semua kelas equally (sensitif
ke minority class performance). Weighted bobot proporsional support per kelas
(lebih representatif performance real-world kalau distribusi test set
mirror dengan distribusi production).
