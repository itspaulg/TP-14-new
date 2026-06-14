"""
Rule-based / lexicon-based context-aware auto-labeler (weak supervision).

Beda dari naive keyword matching: ini handle
  - NEGASI: "gak/ga/nggak/tidak/tak/kurang/belum/jangan + kata-sentimen" → flip polarity
  - KONSESI: split di "tapi/tetapi/namun/cuma/sayang/walau/meski" → evaluasi tiap klausa
  - INTENSITAS & frasa multi-kata

Karena handle negasi/konsesi, label yg dihasilkan SENGAJA menyimpang dari
naive regex pada kasus sulit (mis. "nasi goreng gak enak" → naive bilang
positif krn ada 'enak', tool ini bilang negatif). Penurunan
regex-reproducibility ini diukur di measure_label_quality.py sebagai bukti
label menangkap nuansa di luar keyword.

Pendekatan weak-supervision dengan aturan deterministik & reproducible.

Output: data/labels_v2_auto.jsonl untuk sample_v2.csv
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SAMPLE = ROOT / "data" / "sample_v2.csv"
OUT = ROOT / "data" / "labels_v2_auto.jsonl"

ASPECTS = ["rasa", "harga", "pelayanan"]

NEG_CUES = r"(?:gak|ga|nggak|ngga|tidak|tak|kurang|belum|jangan|bukan|gada|gaada|ga ada|nggk|kgk|kga)"

POS = {
    "rasa": [r"enak", r"lezat", r"sedap", r"gurih", r"mantap", r"mantab", r"nikmat",
             r"juara", r"terbaik", r"rekomen", r"recomend", r"nagih", r"otentik",
             r"sedaaap", r"endes", r"endeus", r"maknyus", r"masyook", r"worth", r"puas"],
    "harga": [r"murah", r"terjangkau", r"ekonomis", r"sepadan", r"cengli", r"worth",
              r"ramah dompet", r"ramah kantong", r"sebanding"],
    "pelayanan": [r"ramah", r"cepat", r"sigap", r"gercep", r"good service",
                  r"pelayanan\w*\s+(?:ok|oke|bagus|baik|mantap|memuaskan)", r"sopan",
                  r"penyajian cepat", r"helpful"],
}
NEG = {
    "rasa": [r"hambar", r"basi", r"amem", r"dingin", r"berminyak", r"asin\b",
             r"kering", r"bau", r"anyep", r"anyir", r"rasa kecap", r"blue band",
             r"benyek", r"lembek", r"diare", r"kuku", r"mules", r"asam", r"keras",
             r"overrated", r"kecewa", r"eneg", r"alot"],
    "harga": [r"mahal", r"overprice", r"over price", r"kemahalan", r"pricey",
              r"porsi\s+\w*\s*(?:kecil|dikit|sedikit|pelit|nanggung)", r"nasi kucing",
              r"ppn", r"pungli", r"tidak sebanding", r"gak sebanding", r"ga sebanding",
              r"naik", r"sikit"],
    "pelayanan": [r"lambat", r"lemot", r"lama", r"berjam", r"jutek", r"kasar",
                  r"sombong", r"cuek", r"jorok", r"emosian", r"nyolot", r"pembohong",
                  r"ancor", r"ancur", r"pelayanan\w*\s+(?:jelek|buruk|menyedihkan|parah|tidak\s+baik|tidak\s+ramah)",
                  r"antri\s+\w*\s*(?:jam|lama)", r"nunggu\s+\w*\s*(?:jam|lama)", r"dibiarin",
                  r"tidak dilayani", r"ga dilayani", r"diabaikan", r"kapok", r"sdm rendah"],
}
NEU = {
    "rasa": [r"biasa aja", r"biasa saja", r"b aja", r"standar", r"lumayan",
             r"just ordinary", r"tidak istimewa", r"gak istimewa", r"cukup",
             r"so so", r"meh", r"oke lah", r"ok lah", r"selera"],
    "harga": [r"harga\s*standar", r"\brp\.?\s*\d", r"\d+\s*rb\b", r"\d+\s*ribu", r"\d+\s*k\b",
              r"harga\s+segini"],
    "pelayanan": [r"cukup ramah", r"cukup cepat", r"penyajian\b", r"standar"],
}

CONCESSION = re.compile(r"\b(?:tapi|tetapi|namun|cuma|cuman|sayang|walau|walaupun|meski|meskipun|kecuali)\b", re.I)


def negated(text, kw_match_start):
    """Apakah ada cue negasi dalam ~4 kata sebelum posisi keyword?"""
    window = text[max(0, kw_match_start - 35):kw_match_start]
    return re.search(NEG_CUES + r"\b", window, re.I) is not None


def score_clause(clause, aspect):
    """Return 'pos'|'neg'|'neu'|None untuk satu klausa, negation-aware."""
    pos_hit = neg_hit = neu_hit = False
    for p in POS[aspect]:
        for m in re.finditer(p, clause, re.I):
            if negated(clause, m.start()):
                neg_hit = True   # negasi membalik pujian → negatif
            else:
                pos_hit = True
    for p in NEG[aspect]:
        for m in re.finditer(p, clause, re.I):
            if negated(clause, m.start()):
                pos_hit = True   # negasi keluhan → cenderung positif
            else:
                neg_hit = True
    for p in NEU[aspect]:
        if re.search(p, clause, re.I):
            neu_hit = True
    if pos_hit and neg_hit:
        return "neu"   # mixed dalam 1 klausa → netral
    if pos_hit:
        return "pos"
    if neg_hit:
        return "neg"
    if neu_hit:
        return "neu"
    return None


def label_aspect(text, aspect):
    clauses = CONCESSION.split(text)
    verdicts = [score_clause(c, aspect) for c in clauses]
    verdicts = [v for v in verdicts if v]
    if not verdicts:
        return "tidak_disebut"
    if "pos" in verdicts and "neg" in verdicts:
        return "netral"  # konsesi positif+negatif → netral keseluruhan
    if "neg" in verdicts:
        return "negatif"
    if "pos" in verdicts:
        return "positif"
    return "netral"


def main():
    rows = list(csv.DictReader(open(SAMPLE, encoding="utf-8")))
    out = []
    for r in rows:
        labels = {a: label_aspect(r["text"], a) for a in ASPECTS}
        out.append({
            "review_id": r["review_id"], "umkm_id": r["umkm_id"], "rating": r["rating"],
            "text": r["text"], **labels,
        })
    OUT.write_text("\n".join(json.dumps(o, ensure_ascii=False) for o in out) + "\n", encoding="utf-8")

    from collections import Counter
    print(f"labeled {len(out)} reviews → {OUT}")
    for a in ASPECTS:
        c = Counter(o[a] for o in out)
        print(f"  {a:10} pos={c.get('positif',0):>3} neg={c.get('negatif',0):>3} "
              f"neu={c.get('netral',0):>3} td={c.get('tidak_disebut',0):>3}")


if __name__ == "__main__":
    main()
