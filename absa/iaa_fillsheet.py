"""
Helper IAA untuk anotator manusia ke-2 (non-teknis).

  python3 iaa_fillsheet.py make      # bikin spreadsheet isian dari iaa_subset.csv
  python3 iaa_fillsheet.py convert   # ubah spreadsheet terisi → labels_pass2_human.jsonl

Alur:
  1. `make` → data/iaa_subset_FILL.csv (kolom rasa/harga/pelayanan kosong)
  2. Anotator ke-2 buka di Excel/Google Sheets, isi tiap kolom dgn:
       1=positif  2=negatif  3=netral  0=tidak disebut
     (tanpa lihat label kamu — harus independen). Save tetap .csv.
  3. `convert` → data/labels_pass2_human.jsonl
  4. python3 iaa.py --pass2 data/labels_pass2_human.jsonl   → Cohen's kappa
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SUBSET = ROOT / "data" / "iaa_subset.csv"
FILL = ROOT / "data" / "iaa_subset_FILL.csv"
OUT = ROOT / "data" / "labels_pass2_human.jsonl"
DIGIT = {"0": "tidak_disebut", "1": "positif", "2": "negatif", "3": "netral"}


def make():
    rows = list(csv.DictReader(open(SUBSET, encoding="utf-8")))
    with FILL.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["review_id", "rating", "text", "rasa", "harga", "pelayanan"])
        for r in rows:
            w.writerow([r["review_id"], r["rating"], r["text"], "", "", ""])
    print(f"Dibuat: {FILL}  ({len(rows)} review)")
    print("Kasih file ini ke anotator ke-2. Isi kolom rasa/harga/pelayanan:")
    print("  1=positif  2=negatif  3=netral  0=tidak disebut")
    print("Save tetap .csv, lalu jalankan: python3 iaa_fillsheet.py convert")


def convert():
    if not FILL.exists():
        sys.exit(f"{FILL} belum ada. Jalankan 'make' dulu + minta diisi.")
    rows = list(csv.DictReader(open(FILL, encoding="utf-8")))
    out, skipped = [], 0
    for r in rows:
        vals = [str(r.get(a, "")).strip() for a in ("rasa", "harga", "pelayanan")]
        if any(v not in DIGIT for v in vals):
            skipped += 1
            continue
        out.append({
            "review_id": r["review_id"],
            "rasa": DIGIT[vals[0]], "harga": DIGIT[vals[1]], "pelayanan": DIGIT[vals[2]],
        })
    with OUT.open("w", encoding="utf-8") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(f"Dikonversi: {len(out)} review → {OUT}")
    if skipped:
        print(f"  ({skipped} baris dilewati karena kolom belum diisi 0-3)")
    print("Lalu: python3 iaa.py --pass2 data/labels_pass2_human.jsonl")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "make"
    {"make": make, "convert": convert}.get(cmd, make)()
