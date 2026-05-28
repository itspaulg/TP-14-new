"""Run trained IndoBERT ABSA on entire pool → predictions.csv.

Usage:
  python3 predict.py                      # all rows in pool.csv
  python3 predict.py --limit 100          # for quick spot-check
  python3 predict.py --no-mps             # force CPU
"""
import argparse
import csv
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).parent
MODEL_DIR = ROOT / "models" / "indobert-absa"
POOL = ROOT / "data" / "pool.csv"
PREDICTIONS = ROOT / "data" / "predictions.csv"

ASPECTS = ["rasa", "harga", "pelayanan"]


def make_input(text: str, aspect: str) -> str:
    return f"[ASPEK: {aspect}] {text}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-len", type=int, default=192)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-mps", action="store_true")
    args = ap.parse_args()

    if not MODEL_DIR.exists():
        raise SystemExit(f"{MODEL_DIR} not found. Run train.py first.")
    if not POOL.exists():
        raise SystemExit(f"{POOL} not found. Run prepare_data.py first.")

    if args.no_mps or not torch.backends.mps.is_available():
        device = torch.device("cpu")
    else:
        device = torch.device("mps")
    print(f"Device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR).to(device).eval()
    id2label = model.config.id2label

    rows = list(csv.DictReader(open(POOL, encoding="utf-8")))
    if args.limit:
        rows = rows[: args.limit]
    print(f"Predicting {len(rows)} reviews × {len(ASPECTS)} aspects ...")

    def batch_predict(texts: list[str], aspect: str) -> list[str]:
        out_labels: list[str] = []
        inputs = [make_input(t, aspect) for t in texts]
        for i in range(0, len(inputs), args.batch):
            chunk = inputs[i : i + args.batch]
            enc = tokenizer(chunk, truncation=True, padding=True,
                            max_length=args.max_len, return_tensors="pt").to(device)
            with torch.no_grad():
                logits = model(**enc).logits
            for p in logits.argmax(-1).cpu().numpy():
                out_labels.append(id2label[int(p)])
        return out_labels

    texts = [r["text"] for r in rows]
    preds_by_asp = {}
    for asp in ASPECTS:
        print(f"  → predicting aspect: {asp}")
        preds_by_asp[asp] = batch_predict(texts, asp)

    with PREDICTIONS.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["review_id", "umkm_id", "rating", "rasa", "harga", "pelayanan", "text"])
        for i, r in enumerate(rows):
            w.writerow([
                r["review_id"], r["umkm_id"], r["rating"],
                preds_by_asp["rasa"][i], preds_by_asp["harga"][i], preds_by_asp["pelayanan"][i],
                r["text"],
            ])
    print(f"Saved: {PREDICTIONS}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
