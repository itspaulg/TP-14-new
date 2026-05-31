"""
Comparative benchmarking dan gap analysis untuk capstone TP-I014.

Input: ../absa/data/predictions.csv (hasil predict.py).
Output: snapshot.json (data terstruktur) + report.md (readable).

Per (UMKM, aspek), saya hitung:
- positive_share = positif / (positif + negatif), exclude netral & TD
- mention_volume = positif + negatif + netral
- net_sentiment = (pos - neg) / volume

Strategy code per aspek berdasarkan posisi UMKM vs median pasar:
- ATTACK: weak (share rendah dan jauh di bawah pasar)
- FIX: di bawah pasar tapi belum kritis
- DEFEND: kuat dan jauh di atas pasar
- PROMOTE: di atas pasar tapi belum "kuat banget"
- MONITOR: dekat median, no action
- NO_DATA: volume terlalu kecil
"""
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
PRED = ROOT.parent / "absa" / "data" / "predictions.csv"
SNAPSHOT = ROOT / "snapshot.json"
REPORT = ROOT / "report.md"

ASPECTS = ["rasa", "harga", "pelayanan"]
MIN_VOLUME = 5  # below this, mark NO_DATA

# Thresholds untuk strategy assignment (relative to market median + absolute share)
GAP_BIG = 0.10   # |gap| ≥ 10% → BELOW/ABOVE
LOW_SHARE = 0.50   # positive_share < 50% → kandidat ATTACK
HIGH_SHARE = 0.70  # ≥ 70% → kandidat DEFEND


def compute_scores(rows: list[dict]) -> dict:
    """Per-UMKM per-aspek metrics."""
    out: dict[str, dict] = {}
    by_umkm: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_umkm[r["umkm_id"]].append(r)

    for umkm, sub in by_umkm.items():
        m = {"_count": len(sub), "aspects": {}}
        for asp in ASPECTS:
            c = Counter(r[asp] for r in sub)
            pos = c.get("positif", 0)
            neg = c.get("negatif", 0)
            neu = c.get("netral", 0)
            td = c.get("tidak_disebut", 0)
            volume = pos + neg + neu
            decisive = pos + neg
            pshare = (pos / decisive) if decisive else None
            net = (pos - neg) / volume if volume else None
            m["aspects"][asp] = {
                "positif": pos, "negatif": neg, "netral": neu, "tidak_disebut": td,
                "volume": volume,            # how often aspek dimention
                "decisive": decisive,        # pos+neg saja
                "positive_share": pshare,    # pos/(pos+neg)
                "net_sentiment": net,        # (pos-neg)/volume
            }
        out[umkm] = m
    return out


def market_medians(scores: dict) -> dict[str, dict]:
    """Median positive_share & net_sentiment across UMKMs (only counting those with volume)."""
    med: dict[str, dict] = {}
    for asp in ASPECTS:
        pshares = [s["aspects"][asp]["positive_share"] for s in scores.values()
                   if s["aspects"][asp]["decisive"] >= MIN_VOLUME and s["aspects"][asp]["positive_share"] is not None]
        nets = [s["aspects"][asp]["net_sentiment"] for s in scores.values()
                if s["aspects"][asp]["volume"] >= MIN_VOLUME and s["aspects"][asp]["net_sentiment"] is not None]
        med[asp] = {
            "median_positive_share": statistics.median(pshares) if pshares else None,
            "median_net_sentiment": statistics.median(nets) if nets else None,
            "n_umkm": len(pshares),
        }
    return med


def assign_strategy(pshare: float | None, volume: int, decisive: int,
                    market_share: float | None) -> str:
    """Return strategy code for (UMKM, aspect) given share + market context."""
    if volume < MIN_VOLUME or pshare is None or market_share is None:
        return "NO_DATA"
    gap = pshare - market_share
    if pshare < LOW_SHARE and gap < -GAP_BIG:
        return "ATTACK"
    if pshare >= HIGH_SHARE and gap > GAP_BIG:
        return "DEFEND"
    if gap > GAP_BIG:
        return "PROMOTE"
    if gap < -GAP_BIG:
        return "FIX"
    return "MONITOR"


def build_snapshot() -> dict:
    rows = list(csv.DictReader(open(PRED, encoding="utf-8")))
    scores = compute_scores(rows)
    med = market_medians(scores)

    for umkm, s in scores.items():
        s["strategies"] = {}
        s["headlines"] = []
        for asp in ASPECTS:
            a = s["aspects"][asp]
            mshare = med[asp]["median_positive_share"]
            code = assign_strategy(a["positive_share"], a["volume"], a["decisive"], mshare)
            s["strategies"][asp] = code
            if code in ("ATTACK", "FIX"):
                s["headlines"].append(f"WEAKNESS:{asp}")
            elif code in ("DEFEND", "PROMOTE"):
                s["headlines"].append(f"STRENGTH:{asp}")

    return {
        "total_reviews": len(rows),
        "umkm_count": len(scores),
        "market": med,
        "per_umkm": scores,
        "min_volume_threshold": MIN_VOLUME,
        "thresholds": {"gap_big": GAP_BIG, "low_share": LOW_SHARE, "high_share": HIGH_SHARE},
    }


def render_report(snap: dict) -> str:
    lines = []
    lines.append("# Snapshot analytics — UMKM nasi goreng Medan\n")
    lines.append(f"Total {snap['total_reviews']} review dari {snap['umkm_count']} UMKM. ")
    lines.append("Hasil ABSA model di-aggregate per (UMKM, aspek) untuk lihat posisi ")
    lines.append("kompetitif tiap UMKM relatif terhadap median pasar.\n")

    lines.append("## Median pasar\n")
    lines.append("Acuan kompetitif lintas 9 UMKM (cuma masuk hitung kalau volume mention ≥ 5):\n")
    lines.append("| Aspek | median positive_share | median net_sentiment | n_umkm |")
    lines.append("|---|---:|---:|---:|")
    for asp in ASPECTS:
        m = snap["market"][asp]
        ps = f"{m['median_positive_share']:.1%}" if m["median_positive_share"] is not None else "-"
        ns = f"{m['median_net_sentiment']:+.2f}" if m["median_net_sentiment"] is not None else "-"
        lines.append(f"| {asp} | {ps} | {ns} | {m['n_umkm']} |")
    lines.append("")

    for asp in ASPECTS:
        lines.append(f"## Ranking per UMKM — {asp}\n")
        rank = []
        for u, s in snap["per_umkm"].items():
            a = s["aspects"][asp]
            if a["decisive"] >= MIN_VOLUME and a["positive_share"] is not None:
                rank.append((u, a["positive_share"], a["volume"], a["positif"], a["negatif"], s["strategies"][asp]))
        rank.sort(key=lambda x: -x[1])
        lines.append("| UMKM | positive_share | volume | pos | neg | strategy |")
        lines.append("|---|---:|---:|---:|---:|---|")
        for u, ps, vol, p, n, strat in rank:
            lines.append(f"| {u} | {ps:.1%} | {vol} | {p} | {n} | {strat} |")
        lines.append("")

    lines.append("## Ringkasan per UMKM\n")
    for u in sorted(snap["per_umkm"]):
        s = snap["per_umkm"][u]
        lines.append(f"### {u} ({s['_count']} review)\n")
        lines.append("| Aspek | pos | neg | neu | TD | share | strategy |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for asp in ASPECTS:
            a = s["aspects"][asp]
            ps = f"{a['positive_share']:.1%}" if a["positive_share"] is not None else "-"
            lines.append(f"| {asp} | {a['positif']} | {a['negatif']} | {a['netral']} | {a['tidak_disebut']} | {ps} | {s['strategies'][asp]} |")
        lines.append("")

    return "\n".join(lines)


def main():
    if not PRED.exists():
        raise SystemExit(f"{PRED} not found. Run absa/predict.py first.")
    snap = build_snapshot()
    SNAPSHOT.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT.write_text(render_report(snap), encoding="utf-8")
    print(f"Wrote {SNAPSHOT}")
    print(f"Wrote {REPORT}")

    # Console summary
    print("\n=== Market Median ===")
    for asp in ASPECTS:
        m = snap["market"][asp]
        ps = f"{m['median_positive_share']:.1%}" if m["median_positive_share"] is not None else "—"
        print(f"  {asp:10}: {ps}")

    print("\n=== Per-UMKM strategy codes ===")
    for u in sorted(snap["per_umkm"]):
        s = snap["per_umkm"][u]
        codes = " ".join(f"{asp}:{s['strategies'][asp]}" for asp in ASPECTS)
        print(f"  {u:30} {codes}")


if __name__ == "__main__":
    main()
