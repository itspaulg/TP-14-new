"""
Bangun sample anotasi yg lebih besar + seimbang.

Masalah di sample awal (276): kelas minoritas tipis — pelayanan.netral=6,
harga.netral=14, harga.positif=21. Untuk fix imbalance + naikin F1, kita
oversample review yg menyebut HARGA dan PELAYANAN (yg paling sering jadi
tidak_disebut), supaya dapat lebih banyak contoh minority class.

Output: data/sample_v2.csv — review baru yg belum dilabel, prioritas
mention harga/pelayanan, untuk dianotasi context-aware.
"""
import csv
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).parent
POOL = ROOT / "data" / "pool.csv"
LABELS = ROOT / "data" / "labels.jsonl"
OUT = ROOT / "data" / "sample_v2.csv"
SEED = 7
TARGET_NEW = 230  # tambahan di atas 276 → total ~506

FIELDS = ["review_id", "umkm_id", "author", "rating", "date_relative", "text"]

PRICE = [r"\bmahal", r"\bmurah", r"\bharga", r"\d+\s*rb\b", r"\d+\s*ribu", r"\brp\.?\s*\d",
         r"overprice", r"\bworth", r"\bporsi", r"\bsepadan", r"\bekonomis", r"\bterjangkau",
         r"\bcengli", r"\bmahal", r"ppn", r"pungli", r"parkir"]
SERVICE = [r"\blambat", r"\blama\b", r"\bpelayan", r"\bramah", r"\bjutek", r"\bkasir",
           r"\bstaff", r"\bpegawai", r"\bantri", r"\bnunggu", r"\bsopan", r"\bcuek",
           r"\bsombong", r"\bgercep", r"\bsigap", r"\bservice", r"\bwaiters", r"\bkaryawan",
           r"\bpenyajian", r"\bcepat"]


def matches(text, pats):
    return any(re.search(p, text, re.I) for p in pats)


def main():
    pool = list(csv.DictReader(open(POOL, encoding="utf-8")))
    labeled_ids = {json.loads(l)["review_id"] for l in open(LABELS, encoding="utf-8") if l.strip()}
    unlabeled = [r for r in pool if r["review_id"] not in labeled_ids]

    rng = random.Random(SEED)

    price = [r for r in unlabeled if matches(r["text"], PRICE)]
    service = [r for r in unlabeled if matches(r["text"], SERVICE)]
    both_ids = {r["review_id"] for r in price} | {r["review_id"] for r in service}
    rest = [r for r in unlabeled if r["review_id"] not in both_ids]

    # priority: reviews mentioning price OR service (yield minority labels), then a few others
    priority = {r["review_id"]: r for r in (price + service)}.values()
    priority = list(priority)
    rng.shuffle(priority)
    rng.shuffle(rest)

    take_priority = priority[: int(TARGET_NEW * 0.8)]
    take_rest = rest[: TARGET_NEW - len(take_priority)]
    new_sample = take_priority + take_rest
    rng.shuffle(new_sample)

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in new_sample:
            w.writerow({k: r[k] for k in FIELDS})

    print(f"unlabeled pool: {len(unlabeled)}")
    print(f"  price-signal: {len(price)}  service-signal: {len(service)}")
    print(f"new sample (untuk anotasi): {len(new_sample)} → {OUT}")
    print(f"  prioritas harga/pelayanan: {len(take_priority)}  lain: {len(take_rest)}")


if __name__ == "__main__":
    main()
