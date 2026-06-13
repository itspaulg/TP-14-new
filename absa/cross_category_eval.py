"""
Cross-category test (#6): jalankan model (di-train di nasi goreng) ke kategori
F&B lain (bakso) untuk ukur domain shift secara JUJUR.

Tidak ada gold label untuk bakso, jadi kita pakai context-aware labeler sbg
referensi proxy (BUKAN gold standard) dan lapor agreement model vs proxy +
distribusi prediksi. Penurunan agreement vs performa in-domain = bukti domain shift.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from annotate_context import label_aspect  # context-aware reference

MODEL_DIR = ROOT / "models" / "indobert-absa"
BAKSO = ROOT.parent / "gmaps_scraper" / "output" / "raw" / "bakso_beranak.csv"
ASPECTS = ["rasa", "harga", "pelayanan"]

device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
tok = AutoTokenizer.from_pretrained(str(MODEL_DIR))
model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR)).to(device).eval()
id2label = model.config.id2label


def predict(texts, aspect, bs=32):
    out = []
    inp = [f"[ASPEK: {aspect}] {t}" for t in texts]
    for i in range(0, len(inp), bs):
        enc = tok(inp[i:i+bs], truncation=True, padding=True, max_length=192, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(**enc).logits
        out.extend(id2label[int(p)] for p in logits.argmax(-1).cpu().numpy())
    return out


rows = [r for r in csv.DictReader(open(BAKSO, encoding="utf-8")) if r["text"].strip()]
texts = [r["text"] for r in rows]
print(f"Bakso reviews with text: {len(texts)}\n")

print("Model prediction distribution (bakso / out-of-domain):")
agreements = []
for asp in ASPECTS:
    preds = predict(texts, asp)
    ref = [label_aspect(t, asp) for t in texts]
    agree = sum(p == r for p, r in zip(preds, ref)) / len(preds)
    agreements.append(agree)
    dist = Counter(preds)
    print(f"  {asp:10} agree_vs_ref={agree:.1%}  dist={{pos:{dist.get('positif',0)}, "
          f"neg:{dist.get('negatif',0)}, neu:{dist.get('netral',0)}, td:{dist.get('tidak_disebut',0)}}}")

print(f"\nAvg model-vs-reference agreement (bakso): {sum(agreements)/len(agreements):.1%}")
print("Catatan: referensi = context-aware labeler (proxy, bukan gold). Agreement")
print("lebih rendah dari performa in-domain nasi goreng = indikasi domain shift.")
