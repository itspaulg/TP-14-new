"""
Inter-Annotator Agreement (Cohen's kappa) — tooling untuk future work.

IAA yang sah butuh DUA anotator independen. Script ini menghitung kappa
antara dua file label pada review yang sama.

Alur:
  1. python3 iaa.py --make-subset      # buat data/iaa_subset.csv (60 review)
  2. Anotator ke-2 label subset itu → data/labels_pass2_human.jsonl
     (format: {"review_id","rasa","harga","pelayanan"})
     (lihat iaa_fillsheet.py untuk versi spreadsheet yg mudah diisi)
  3. python3 iaa.py --pass2 data/labels_pass2_human.jsonl

Cohen's kappa (Landis & Koch): <0 poor, 0-0.2 slight, 0.21-0.4 fair,
0.41-0.6 moderate, 0.61-0.8 substantial, 0.81-1.0 almost perfect.
"""
import argparse
import csv
import json
import random
from pathlib import Path

from sklearn.metrics import cohen_kappa_score

ROOT = Path(__file__).parent
ASPECTS = ["rasa", "harga", "pelayanan"]


def load(path):
    return {json.loads(l)["review_id"]: json.loads(l)
            for l in open(path, encoding="utf-8") if l.strip()}


def koch(k):
    if k < 0: return "poor"
    if k <= 0.20: return "slight"
    if k <= 0.40: return "fair"
    if k <= 0.60: return "moderate"
    if k <= 0.80: return "substantial"
    return "almost perfect"


def make_subset(n=60, seed=11):
    sample = list(csv.DictReader(open(ROOT / "data" / "sample.csv", encoding="utf-8")))
    rng = random.Random(seed)
    rng.shuffle(sample)
    sub = sample[:n]
    out = ROOT / "data" / "iaa_subset.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["review_id", "umkm_id", "rating", "text"])
        w.writeheader()
        for r in sub:
            w.writerow({k: r[k] for k in ["review_id", "umkm_id", "rating", "text"]})
    print(f"Subset untuk anotator ke-2: {out} ({n} review)")
    print("Minta 1 orang label, simpan ke data/labels_pass2_human.jsonl")
    print("(atau pakai iaa_fillsheet.py untuk versi spreadsheet)")


def compute(pass1_path, pass2_path):
    p1, p2 = load(pass1_path), load(pass2_path)
    shared = sorted(set(p1) & set(p2))
    if not shared:
        print("Tidak ada review_id yg sama antara dua pass."); return
    print(f"\n=== Inter-annotator agreement (Cohen's kappa) ===")
    print(f"Overlap: {len(shared)} review\n")
    kappas = []
    for a in ASPECTS:
        y1 = [p1[i][a] for i in shared]
        y2 = [p2[i][a] for i in shared]
        k = cohen_kappa_score(y1, y2)
        kappas.append(k)
        agree = sum(x == y for x, y in zip(y1, y2)) / len(shared)
        print(f"  {a:10} kappa={k:.3f} ({koch(k)})   raw agreement={agree:.1%}")
    avg = sum(kappas) / len(kappas)
    print(f"\n  AVERAGE kappa = {avg:.3f} ({koch(avg)})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass1", default=str(ROOT / "data" / "labels.jsonl"),
                    help="anotator ke-1 (default labels.jsonl)")
    ap.add_argument("--pass2", default=None, help="file label anotator ke-2 (human)")
    ap.add_argument("--make-subset", action="store_true")
    args = ap.parse_args()

    if args.make_subset:
        make_subset()
    elif args.pass2:
        compute(args.pass1, args.pass2)
    else:
        print("Pakai --make-subset dulu, atau --pass2 <file> untuk hitung kappa.")


if __name__ == "__main__":
    main()
