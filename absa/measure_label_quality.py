"""
Ukur seberapa banyak label bisa direproduksi oleh NAIVE keyword classifier.

Reviewer bisa nguji: "apakah label ini cuma hasil regex keyword?" Kalau
agreement naive-regex ~100%, label dianggap keyword-derived (lemah). Kalau
lebih rendah, artinya label menangkap nuansa (negasi, konsesi, konteks) yg
naive keyword nggak bisa.

Bandingkan:
  - labels_v1.jsonl  (276 awal — accepted dari keyword suggestions)
  - labels_v2_auto.jsonl (230 baru — context-aware, negation-aware)
  - labels.jsonl (gabungan 506)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ASPECTS = ["rasa", "harga", "pelayanan"]

# NAIVE keyword classifier (apa yg reviewer skeptis akan pakai) — TANPA negasi
POS = {
    "rasa": [r"enak", r"lezat", r"sedap", r"gurih", r"mantap", r"mantab", r"nikmat", r"juara", r"terbaik", r"rekomen", r"recomend", r"nagih", r"worth", r"puas"],
    "harga": [r"murah", r"terjangkau", r"ekonomis", r"sepadan", r"cengli", r"worth", r"sebanding"],
    "pelayanan": [r"ramah", r"cepat", r"sigap", r"gercep", r"sopan", r"bagus", r"baik"],
}
NEG = {
    "rasa": [r"hambar", r"basi", r"amem", r"dingin", r"berminyak", r"asin", r"kering", r"bau", r"rasa kecap", r"benyek", r"lembek", r"kecewa"],
    "harga": [r"mahal", r"overprice", r"pricey", r"pelit", r"nasi kucing", r"ppn", r"pungli"],
    "pelayanan": [r"lambat", r"lama", r"jutek", r"kasar", r"sombong", r"cuek", r"jorok", r"jelek", r"buruk"],
}
NEU = {
    "rasa": [r"biasa aja", r"biasa saja", r"b aja", r"standar", r"lumayan"],
    "harga": [r"\d+\s*rb", r"\d+\s*ribu", r"rp\.?\s*\d", r"harga standar"],
    "pelayanan": [r"cukup", r"penyajian"],
}


def naive_label(text, aspect):
    p = any(re.search(x, text, re.I) for x in POS[aspect])
    n = any(re.search(x, text, re.I) for x in NEG[aspect])
    u = any(re.search(x, text, re.I) for x in NEU[aspect])
    if p and n:
        return "netral"
    if p:
        return "positif"
    if n:
        return "negatif"
    if u:
        return "netral"
    return "tidak_disebut"


def agreement(path):
    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    total = match = 0
    per_asp = {a: [0, 0] for a in ASPECTS}
    for r in recs:
        for a in ASPECTS:
            naive = naive_label(r["text"], a)
            total += 1
            per_asp[a][1] += 1
            if naive == r[a]:
                match += 1
                per_asp[a][0] += 1
    return match / total, {a: per_asp[a][0] / per_asp[a][1] for a in ASPECTS}, len(recs)


def main():
    print("Naive-keyword reproducibility (makin RENDAH = label makin 'beyond keyword'):\n")
    for name in ["labels_v1.jsonl", "labels_v2_auto.jsonl", "labels.jsonl"]:
        p = ROOT / "data" / name
        if not p.exists():
            continue
        overall, per_asp, n = agreement(p)
        print(f"  {name:22} n={n:>4}  overall={overall:.1%}  " +
              "  ".join(f"{a}={per_asp[a]:.0%}" for a in ASPECTS))
    print("\nInterpretasi: label awal (v1) tinggi krn accepted dari keyword suggestions.")
    print("Label baru (v2 context-aware) lebih rendah krn handle negasi/konsesi/konteks.")


if __name__ == "__main__":
    main()
