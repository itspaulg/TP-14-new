"""
Inter-Annotator Agreement (Cohen's kappa).

PENTING — INTEGRITAS:
IAA yg SAH untuk laporan butuh DUA anotator MANUSIA independen. Script ini
menyediakan tooling-nya. Secara default ia menghitung kappa antara:
  - pass1 = anotasi yg ada (data/labels.jsonl / labels_v1.jsonl)
  - pass2 = file anotator ke-2

Kalau pass2 = anotasi AI (context-aware labeler), hasilnya dilaporkan
sebagai "AI self-consistency", BUKAN human IAA. Untuk human IAA:
  1. Ambil subset (mis. 60 review) → data/iaa_subset.csv (dibuat script ini)
  2. Minta 1 orang lain label subset itu → simpan data/labels_pass2_human.jsonl
     (format sama: {"review_id","rasa","harga","pelayanan"})
  3. Jalankan: python3 iaa.py --pass2 data/labels_pass2_human.jsonl

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
    """Buat subset untuk anotator manusia ke-2."""
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


def gen_ai_pass2():
    """Pass2 demonstrasi: context-aware labeler di sample.csv (AI self-consistency)."""
    from annotate_context import label_aspect
    rows = list(csv.DictReader(open(ROOT / "data" / "sample.csv", encoding="utf-8")))
    out = ROOT / "data" / "labels_pass2_ai.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            rec = {"review_id": r["review_id"], **{a: label_aspect(r["text"], a) for a in ASPECTS}}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return out


def compute(pass1_path, pass2_path, human):
    p1, p2 = load(pass1_path), load(pass2_path)
    shared = sorted(set(p1) & set(p2))
    if not shared:
        print("Tidak ada review_id yg sama antara dua pass."); return
    label = "HUMAN inter-annotator agreement" if human else "AI self-consistency (BUKAN human IAA)"
    print(f"\n=== {label} ===")
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
    if not human:
        print("\n  [!] Ini self-consistency AI. Untuk laporan, ganti pass2 dgn anotasi manusia ke-2.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass1", default=str(ROOT / "data" / "labels_v1.jsonl"))
    ap.add_argument("--pass2", default=None, help="file anotator ke-2 (human). Kalau kosong, pakai AI self-consistency.")
    ap.add_argument("--make-subset", action="store_true", help="buat iaa_subset.csv untuk anotator manusia")
    args = ap.parse_args()

    if args.make_subset:
        make_subset()
        return

    if args.pass2:
        compute(args.pass1, args.pass2, human=True)
    else:
        p2 = gen_ai_pass2()
        compute(args.pass1, str(p2), human=False)


if __name__ == "__main__":
    main()
