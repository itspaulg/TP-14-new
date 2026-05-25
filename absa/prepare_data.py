"""Concat scraped review CSVs → pool.csv, then stratified-sample → sample.csv.

Usage:
  python3 prepare_data.py                # default 60 per rating star
  python3 prepare_data.py --per-rating 80
"""
import argparse
import csv
import hashlib
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
RAW_DIR = ROOT.parent / "gmaps_scraper" / "output" / "raw"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
POOL = DATA_DIR / "pool.csv"
SAMPLE = DATA_DIR / "sample.csv"
SEED = 42

FIELDS = ["review_id", "umkm_id", "author", "rating", "date_relative", "text"]


def make_id(umkm: str, author: str, date: str, text: str) -> str:
    h = hashlib.sha256(f"{umkm}|{author}|{date}|{text[:120]}".encode("utf-8")).hexdigest()
    return h[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-rating", type=int, default=60,
                    help="Target sample size per rating star (default 60 × 5 = 300)")
    args = ap.parse_args()

    files = sorted(RAW_DIR.glob("*.csv"))
    if not files:
        raise SystemExit(f"No CSVs found in {RAW_DIR}")

    rows = []
    for f in files:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            if not r["text"].strip():
                continue
            r["review_id"] = make_id(r["umkm_id"], r["author"], r["date_relative"], r["text"])
            rows.append(r)
    print(f"With-text reviews: {len(rows)} from {len(files)} UMKM CSVs")

    # dedupe by review_id
    seen = set()
    unique = []
    for r in rows:
        if r["review_id"] in seen:
            continue
        seen.add(r["review_id"])
        unique.append(r)
    print(f"After dedupe: {len(unique)}")

    # write pool
    with POOL.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in unique:
            w.writerow({k: r[k] for k in FIELDS})
    print(f"Wrote {POOL}  ({len(unique)} rows)")

    # stratified sample by rating
    by_rating: dict[str, list[dict]] = {}
    for r in unique:
        by_rating.setdefault(r["rating"], []).append(r)

    rng = random.Random(SEED)
    sample: list[dict] = []
    print("\nStratified sampling per rating:")
    for rating in sorted(by_rating, key=lambda x: (not x.isdigit(), x)):
        bucket = by_rating[rating]
        rng.shuffle(bucket)
        take = bucket[: args.per_rating]
        sample.extend(take)
        print(f"  rating={rating!r:5}  bucket={len(bucket):>4}  taken={len(take):>4}")

    rng.shuffle(sample)
    with SAMPLE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in sample:
            w.writerow({k: r[k] for k in FIELDS})
    print(f"\nWrote {SAMPLE}  ({len(sample)} rows for annotation)")
    print(f"  UMKM coverage: {Counter(r['umkm_id'] for r in sample)}")


if __name__ == "__main__":
    main()
