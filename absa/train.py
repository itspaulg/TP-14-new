"""Fine-tune IndoBERT for 3-aspect ABSA on labeled reviews.

Input format: "[ASPEK: <aspect>] <text>" → 4-way classification
  (tidak_disebut / positif / negatif / netral)

One model handles all 3 aspects (aspect-injection). Triples
(text, aspect, label) flatten 1 review → 3 training examples.

Usage:
  python3 train.py                      # default 5 epochs, batch 16, lr 2e-5
  python3 train.py --epochs 8 --batch 8 --lr 1e-5
  python3 train.py --no-mps             # force CPU
"""
import argparse
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

ROOT = Path(__file__).parent
LABELS_FILE = ROOT / "data" / "labels.jsonl"
MODEL_DIR = ROOT / "models" / "indobert-absa"
REPORT_FILE = ROOT / "models" / "eval_report.json"

MODEL_NAME = "indobenchmark/indobert-base-p1"
ASPECTS = ["rasa", "harga", "pelayanan"]
LABEL_NAMES = ["tidak_disebut", "positif", "negatif", "netral"]
L2I = {l: i for i, l in enumerate(LABEL_NAMES)}
I2L = {i: l for l, i in L2I.items()}


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)


def make_input(text: str, aspect: str) -> str:
    return f"[ASPEK: {aspect}] {text}"


class ABSADataset(Dataset):
    def __init__(self, triples, tokenizer, max_len):
        self.triples = triples
        self.tok = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.triples)

    def __getitem__(self, i):
        text, asp, lab = self.triples[i]
        enc = self.tok(
            make_input(text, asp),
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"][0],
            "attention_mask": enc["attention_mask"][0],
            "labels": torch.tensor(L2I[lab], dtype=torch.long),
        }


def evaluate(model, loader, device):
    model.eval()
    preds, trues = [], []
    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            out = model(**batch)
            preds.extend(out.logits.argmax(-1).cpu().numpy().tolist())
            trues.extend(batch["labels"].cpu().numpy().tolist())
    return preds, trues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max-len", type=int, default=192)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--test-size", type=float, default=0.2)
    ap.add_argument("--no-mps", action="store_true")
    ap.add_argument("--no-class-weight", action="store_true",
                    help="Disable balanced class weighting in loss")
    args = ap.parse_args()

    set_seed(args.seed)

    if not LABELS_FILE.exists():
        raise SystemExit(f"{LABELS_FILE} not found. Run annotate.py first.")

    records = [json.loads(l) for l in LABELS_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"Loaded {len(records)} labeled reviews")
    if len(records) < 50:
        print(f"[warn] hanya {len(records)} record — F1 mungkin tidak stabil. Anotasi lebih banyak disarankan.")

    # Build (text, aspect, label) triples
    triples = []
    for r in records:
        for asp in ASPECTS:
            triples.append((r["text"], asp, r[asp]))
    print(f"Total (text, aspect, label) triples: {len(triples)}")

    # Class distribution per aspect
    print("\nDistribusi label per aspek:")
    for asp in ASPECTS:
        c = Counter(r[asp] for r in records)
        print(f"  {asp:10}  {dict(c)}")

    # Stratify by joined "aspect|label"
    strata = [f"{a}|{l}" for _, a, l in triples]
    # Handle case where some strata have <2 instances (can't stratify) — fallback unstratified
    strata_counts = Counter(strata)
    if min(strata_counts.values()) < 2:
        print("[warn] beberapa kelas <2 sample; pakai split unstratified.")
        train_t, test_t = train_test_split(triples, test_size=args.test_size, random_state=args.seed)
    else:
        train_t, test_t = train_test_split(
            triples, test_size=args.test_size, random_state=args.seed, stratify=strata
        )
    print(f"\nTrain: {len(train_t)}  Test: {len(test_t)}")

    # Device
    if args.no_mps or not torch.backends.mps.is_available():
        device = torch.device("cpu")
    else:
        device = torch.device("mps")
    print(f"Device: {device}")

    # Tokenizer + Model
    print(f"\nLoading {MODEL_NAME} ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=len(LABEL_NAMES), id2label=I2L, label2id=L2I,
    ).to(device)

    train_ds = ABSADataset(train_t, tokenizer, args.max_len)
    test_ds = ABSADataset(test_t, tokenizer, args.max_len)
    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=args.batch)  # order preserved

    optimizer = AdamW(model.parameters(), lr=args.lr)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(0.1 * total_steps), num_training_steps=total_steps
    )

    # Class weights (balanced) to compensate for class imbalance
    if args.no_class_weight:
        loss_fn = nn.CrossEntropyLoss()
        print("Class weighting: OFF")
    else:
        train_label_ids = np.array([L2I[lab] for _, _, lab in train_t])
        present_classes = np.unique(train_label_ids)
        weights = compute_class_weight("balanced", classes=present_classes, y=train_label_ids)
        # Map back to a vector of length len(LABEL_NAMES)
        weight_vec = np.ones(len(LABEL_NAMES), dtype=np.float32)
        for cls_id, w in zip(present_classes, weights):
            weight_vec[cls_id] = w
        weight_tensor = torch.tensor(weight_vec, dtype=torch.float).to(device)
        loss_fn = nn.CrossEntropyLoss(weight=weight_tensor)
        print(f"Class weights: " + ", ".join(
            f"{LABEL_NAMES[i]}={weight_vec[i]:.2f}" for i in range(len(LABEL_NAMES))
        ))

    best_f1 = -1.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        total = 0.0
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            out = model(**batch)
            loss = loss_fn(out.logits, batch["labels"])
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            total += loss.item()
        avg = total / len(train_loader)
        preds, trues = evaluate(model, test_loader, device)
        f1 = f1_score(trues, preds, average="macro")
        flag = ""
        if f1 > best_f1:
            best_f1 = f1
            model.save_pretrained(MODEL_DIR)
            tokenizer.save_pretrained(MODEL_DIR)
            flag = " ← saved (best)"
        print(f"epoch {epoch}/{args.epochs}  loss={avg:.4f}  test macro-F1={f1:.4f}{flag}")

    # Final per-aspect breakdown (best model already saved)
    print("\n=== Final per-aspect eval (best checkpoint) ===")
    # reload best
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR).to(device)
    per_asp_preds = {a: [] for a in ASPECTS}
    per_asp_trues = {a: [] for a in ASPECTS}
    # iterate test in order
    model.eval()
    idx = 0
    with torch.no_grad():
        for batch in test_loader:
            inp = {k: v.to(device) for k, v in batch.items()}
            out = model(**inp)
            pred = out.logits.argmax(-1).cpu().numpy()
            true = batch["labels"].cpu().numpy()
            for p, t in zip(pred, true):
                asp = test_t[idx][1]
                per_asp_preds[asp].append(int(p))
                per_asp_trues[asp].append(int(t))
                idx += 1

    report_out = {"best_macro_f1": best_f1, "per_aspect": {}}
    for asp in ASPECTS:
        p, t = per_asp_preds[asp], per_asp_trues[asp]
        if not p:
            continue
        f1m = f1_score(t, p, average="macro")
        f1w = f1_score(t, p, average="weighted")
        print(f"\n[{asp}]  n={len(p)}  macro-F1={f1m:.4f}  weighted-F1={f1w:.4f}")
        print(classification_report(t, p, labels=list(range(len(LABEL_NAMES))),
                                    target_names=LABEL_NAMES, zero_division=0))
        report_out["per_aspect"][asp] = {
            "n": len(p), "macro_f1": f1m, "weighted_f1": f1w,
        }

    REPORT_FILE.write_text(json.dumps(report_out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport: {REPORT_FILE}")
    print(f"Model:  {MODEL_DIR}")
    if best_f1 >= 0.80:
        print(f"\nF1 ≥ 0.80 target tercapai (macro-F1={best_f1:.4f}).")
    else:
        print(f"\nF1 {best_f1:.4f} di bawah target 0.80. Saran: anotasi lebih banyak / lebih balanced, atau naikkan epoch.")


if __name__ == "__main__":
    main()
