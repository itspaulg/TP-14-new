"""
Tool buat anotasi manual review per aspek (rasa, harga, pelayanan).
Output: data/labels.jsonl (satu baris JSON per review).

Cara pakai:
  python3 annotate.py

Per review, ketik 3 digit untuk rasa, harga, pelayanan:
  1 = positif    2 = negatif    3 = netral    0 = tidak disebut

Contoh: "111" semua positif; "200" rasa negatif doang.

Bisa pause kapan aja (tekan q), nanti lanjut dari yg belum kelabel.
"""
import csv
import json
import sys
import termios
import tty
from pathlib import Path

ROOT = Path(__file__).parent
SAMPLE = ROOT / "data" / "sample.csv"
LABELS = ROOT / "data" / "labels.jsonl"

ASPECTS = ["rasa", "harga", "pelayanan"]
DIGIT_TO_LABEL = {"0": "tidak_disebut", "1": "positif", "2": "negatif", "3": "netral"}
SHORT = {"tidak_disebut": "TD ", "positif": "POS", "negatif": "NEG", "netral": "NEU"}


def load_done():
    if not LABELS.exists():
        return []
    out = []
    for line in LABELS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def append_label(rec):
    with LABELS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def rewrite_labels(records):
    with LABELS.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def getch():
    """Baca 1 keystroke tanpa perlu Enter."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def read_input():
    """Ambil 3 digit dari user, atau command 1 huruf (s/b/q)."""
    sys.stdout.write("[R H P] > ")
    sys.stdout.flush()
    digits = ""
    while True:
        ch = getch()
        if ch == "\x03":
            sys.stdout.write("\n")
            raise KeyboardInterrupt
        if ch in ("\x7f", "\b"):
            if digits:
                digits = digits[:-1]
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue
        if ch in "0123":
            digits += ch
            sys.stdout.write(ch)
            sys.stdout.flush()
            if len(digits) == 3:
                sys.stdout.write("\n")
                return digits
            continue
        if ch in ("s", "b", "q"):
            if digits:
                sys.stdout.write("\b" * len(digits) + " " * len(digits) + "\b" * len(digits))
            sys.stdout.write(ch + "\n")
            return ch


def show_review(idx, total, row):
    print()
    print("=" * 70)
    print(f"[{idx}/{total}]  {row['umkm_id']}  {row['rating']}*  {row['date_relative']}")
    print("-" * 70)
    print(row["text"])
    print("=" * 70)


def main():
    if not SAMPLE.exists():
        sys.exit(f"{SAMPLE} belum ada. Jalanin prepare_data.py dulu.")

    rows = list(csv.DictReader(open(SAMPLE, encoding="utf-8")))
    by_id = {r["review_id"]: r for r in rows}
    history = load_done()
    done_ids = {r["review_id"] for r in history}
    todo = [r for r in rows if r["review_id"] not in done_ids]

    print(f"Total: {len(rows)}  |  done: {len(history)}  |  sisa: {len(todo)}")
    if not todo:
        print("Sudah selesai semua.")
        return

    i = 0
    while i < len(todo):
        row = todo[i]
        show_review(len(history) + i + 1, len(rows), row)
        ans = read_input()

        if ans == "q":
            print(f"\nKeluar. {len(history)}/{len(rows)} sudah dilabel.")
            return
        if ans == "s":
            i += 1
            continue
        if ans == "b":
            if not history:
                print("Belum ada yang bisa diundo.")
                continue
            last = history.pop()
            rewrite_labels(history)
            if last["review_id"] in by_id:
                todo.insert(i, by_id[last["review_id"]])
            print(f"Undo: {last['review_id']}")
            continue

        labels = {ASPECTS[k]: DIGIT_TO_LABEL[ans[k]] for k in range(3)}
        rec = {
            "review_id": row["review_id"],
            "umkm_id": row["umkm_id"],
            "rating": row["rating"],
            "text": row["text"],
            **labels,
        }
        append_label(rec)
        history.append(rec)
        i += 1
        out = "  ".join(f"{a}={SHORT[labels[a]]}" for a in ASPECTS)
        print(f"  -> {out}")

    print(f"\nSelesai. {len(rows)} review terlabel di {LABELS.name}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nDihentikan. Progress sudah tersimpan.")
