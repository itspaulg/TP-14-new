"""
Rule-based recommendation engine.

Input: snapshot.json (dari analyze.py).
Output: recommendations.json + recommendations.md.

Pendekatan: pakai dynamic string template. Per (UMKM, aspek), strategy code
dari analytics di-map ke template rationale + actionable items. Deterministic,
no LLM (LLM wrap opsional, bisa di-bolt-on di presentation layer kalau perlu).
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
SNAPSHOT = ROOT / "snapshot.json"
OUT_JSON = ROOT / "recommendations.json"
OUT_MD = ROOT / "recommendations.md"

ASPECTS = ["rasa", "harga", "pelayanan"]

# Priority ranking of strategy codes (lower = higher priority for action)
PRIORITY = {
    "ATTACK": 1,    # urgent weakness vs market
    "FIX": 2,       # below market but not catastrophic
    "DEFEND": 3,    # explicit strength to protect
    "PROMOTE": 4,   # competitive advantage to highlight
    "MONITOR": 5,   # near market, no action needed
    "NO_DATA": 6,   # insufficient sample
}

# Templates per (aspect, code). Format placeholders: {umkm}, {share}, {market}, {gap},
# {volume}, {pos}, {neg}.
RATIONALES = {
    ("rasa", "ATTACK"): (
        "Rasa adalah aspek paling sering dibicarakan customer F&B, dan {umkm} "
        "berada di {share} positif — di bawah median pasar ({market}). "
        "Dari {volume} mention rasa, {neg} bernada negatif. Ini adalah threat "
        "kompetitif paling serius karena rasa biasanya sticky habit konsumen."
    ),
    ("rasa", "FIX"): (
        "Rasa {umkm} di {share}, sedikit di bawah median pasar {market} (gap {gap}). "
        "Perlu pengecekan konsistensi resep dan kualitas bahan. Tidak urgent "
        "tapi jangan dibiarkan menurun lebih jauh."
    ),
    ("rasa", "DEFEND"): (
        "Rasa adalah moat {umkm}: {share} positif, jauh di atas median ({market}). "
        "Konsumen yang puas dengan rasa cenderung loyal. Pertahankan konsistensi "
        "produk dan jadikan rasa sebagai pesan utama marketing."
    ),
    ("rasa", "PROMOTE"): (
        "{umkm} unggul di rasa ({share} vs market {market}). Jadikan diferensiasi "
        "konten: testimoni, content marketing dengan tagline khas rasa."
    ),
    ("rasa", "MONITOR"): (
        "Rasa {umkm} setara market ({share} vs {market}). Tidak perlu intervensi; "
        "alokasikan resource ke aspek lain."
    ),
    ("rasa", "NO_DATA"): (
        "Volume mention rasa kurang dari threshold ({volume}). Pertimbangkan "
        "campaign untuk mendorong feedback (mis. discount kalau review)."
    ),

    ("harga", "ATTACK"): (
        "Harga {umkm} dipersepsikan tidak adil oleh customer: hanya {share} positif "
        "dari {volume} mention (median pasar {market}). Dari {pos}/{neg} pos/neg, "
        "complaint dominan adalah 'mahal untuk porsi' atau 'tidak sepadan'. "
        "Aksi: audit pricing vs kompetitor langsung, atau tambahkan value (bundling, "
        "porsi alternatif, paket promo)."
    ),
    ("harga", "FIX"): (
        "Harga {umkm} di {share} positif, sedikit di bawah median ({market}). "
        "Sebagian customer feel value-for-money kurang. Pertimbangkan menu paket "
        "atau klarifikasi value lewat marketing."
    ),
    ("harga", "DEFEND"): (
        "Harga adalah strength {umkm}: {share} positif (jauh di atas market {market}). "
        "Customer melihat ini sebagai 'value for money'. Pertahankan price-point "
        "dan jangan naik tanpa upgrade kualitas; tonjolkan di komunikasi."
    ),
    ("harga", "PROMOTE"): (
        "Harga {umkm} kompetitif ({share} vs market {market}). Use case "
        "marketing: 'pilihan terbaik di kisaran harga'."
    ),
    ("harga", "MONITOR"): (
        "Harga {umkm} setara market ({share} vs {market}). Tidak ada signal "
        "untuk intervensi pricing saat ini."
    ),
    ("harga", "NO_DATA"): (
        "Mention harga sangat sedikit ({volume}). Customer kemungkinan tidak "
        "menjadikan harga sebagai pertimbangan utama, atau sample bias. "
        "Tidak ada rekomendasi pricing."
    ),

    ("pelayanan", "ATTACK"): (
        "Pelayanan adalah pain point akut: hanya {share} positif (median pasar {market}). "
        "{neg}/{volume} mention bernada negatif. Pattern umum di review: waktu tunggu, "
        "sikap staff, kesalahan order. Aksi prioritas: audit response time, training "
        "staff, dan SOP penanganan komplain. Ini sering jadi alasan #1 customer pindah."
    ),
    ("pelayanan", "FIX"): (
        "Pelayanan {umkm} di {share}, sedikit di bawah median {market}. Inkonsistensi "
        "kemungkinan ada di shift tertentu atau staff tertentu. Tracking customer "
        "feedback per shift bisa membantu."
    ),
    ("pelayanan", "DEFEND"): (
        "Pelayanan adalah strength {umkm}: {share} positif (vs market {market}). "
        "Customer experience yang konsisten ramah/cepat. Pertahankan culture staff "
        "dan jangan turunkan standar saat scale up."
    ),
    ("pelayanan", "PROMOTE"): (
        "Pelayanan {umkm} di atas market ({share} vs {market}). Tonjolkan di "
        "review platform dan social media — 'ramah', 'cepat', 'helpful'."
    ),
    ("pelayanan", "MONITOR"): (
        "Pelayanan {umkm} setara market ({share} vs {market}). Tidak urgent."
    ),
    ("pelayanan", "NO_DATA"): (
        "Mention pelayanan terlalu sedikit ({volume}). Implikasi: customer tidak "
        "mengingat pengalaman service, atau review mostly fokus produk."
    ),
}

ACTIONABLES = {
    ("rasa", "ATTACK"): [
        "Survey blind taste-test dengan 20-30 customer reguler vs kompetitor",
        "Standarisasi resep tertulis untuk semua koki/shift",
        "Cek kualitas bahan baku dengan supplier",
    ],
    ("rasa", "FIX"): [
        "Quality check harian sample masakan",
        "Internal tasting weekly dengan owner + senior cook",
    ],
    ("rasa", "DEFEND"): [
        "Dokumentasikan resep & SOP rasa (sebelum pengetahuan implicit hilang)",
        "Buat content story 'kenapa rasa kami berbeda' untuk marketing",
    ],
    ("rasa", "PROMOTE"): [
        "Konten testimoni rasa di IG/TikTok",
        "Highlight rasa di menu/banner",
    ],
    ("harga", "ATTACK"): [
        "Benchmark pricing vs 3 kompetitor terdekat (per menu sejenis)",
        "Tambah opsi porsi (mini/regular/jumbo) untuk price-flexibility",
        "Paket promo combo (nasgor + minum + side) dengan diskon 10-15%",
    ],
    ("harga", "FIX"): [
        "Tambahkan side menu murah untuk persepsi value (kerupuk gratis, dll)",
        "Komunikasikan 'kenapa harga segini' (kualitas bahan, porsi besar)",
    ],
    ("harga", "DEFEND"): [
        "Jangan naikkan harga tanpa upgrade visible (porsi, bahan premium)",
        "Tagline marketing: 'rasa premium, harga warung'",
    ],
    ("harga", "PROMOTE"): [
        "Comparison content vs kompetitor menunjukkan harga lebih baik",
    ],
    ("pelayanan", "ATTACK"): [
        "Audit waktu tunggu rata-rata pesanan (target ≤ 15 menit untuk dine-in)",
        "Training basic hospitality untuk semua staff: greeting, eye contact, smile",
        "SOP penanganan komplain (acknowledge → apologize → action)",
        "Re-design alur pesanan: kasir → dapur → pengantar, cek bottleneck",
    ],
    ("pelayanan", "FIX"): [
        "Daily briefing pre-shift untuk align expectations staff",
        "Track customer satisfaction per shift untuk identify pattern",
    ],
    ("pelayanan", "DEFEND"): [
        "Sistem rotation/insentif untuk pertahankan staff lama",
        "Buddy system: staff baru ikut staff lama 2 minggu",
    ],
    ("pelayanan", "PROMOTE"): [
        "Highlight nama staff favorit di marketing (jika ada permission)",
        "Ulasan 'ramah' jadi pull quote di feed",
    ],
}

# Generic fallback if specific actionable not defined
FALLBACK_ACTIONS = {
    "ATTACK": ["Audit aspek ini sebagai prioritas #1 minggu depan."],
    "FIX": ["Monitor; cek root cause penurunan."],
    "DEFEND": ["Pertahankan apa yang sudah bekerja."],
    "PROMOTE": ["Highlight aspek ini di komunikasi marketing."],
    "MONITOR": ["Tidak perlu intervensi saat ini."],
    "NO_DATA": ["Drive lebih banyak feedback dari customer."],
}


def fmt_pct(x: float | None) -> str:
    return f"{x*100:.1f}%" if x is not None else "—"


def fmt_gap(x: float | None) -> str:
    if x is None:
        return "—"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x*100:.1f}pp"


def render_rationale(template: str, umkm: str, asp_data: dict, market_share: float) -> str:
    share = asp_data["positive_share"]
    gap = (share - market_share) if (share is not None and market_share is not None) else None
    return template.format(
        umkm=umkm,
        share=fmt_pct(share),
        market=fmt_pct(market_share),
        gap=fmt_gap(gap),
        volume=asp_data["volume"],
        pos=asp_data["positif"],
        neg=asp_data["negatif"],
    )


def build_recommendations(snap: dict) -> dict:
    out: dict = {"per_umkm": {}, "market": snap["market"]}
    for umkm, s in snap["per_umkm"].items():
        actions = []
        for asp in ASPECTS:
            code = s["strategies"][asp]
            asp_data = s["aspects"][asp]
            market_share = snap["market"][asp]["median_positive_share"]
            template = RATIONALES.get((asp, code), "")
            rationale = render_rationale(template, umkm, asp_data, market_share) if template else ""
            todos = ACTIONABLES.get((asp, code), FALLBACK_ACTIONS.get(code, []))
            actions.append({
                "aspect": asp,
                "code": code,
                "priority": PRIORITY[code],
                "positive_share": asp_data["positive_share"],
                "market_share": market_share,
                "volume": asp_data["volume"],
                "rationale": rationale,
                "actionable": list(todos),
            })
        actions.sort(key=lambda a: (a["priority"], -a["volume"]))
        top_codes = [f"{a['aspect']} ({a['code']})" for a in actions if a["priority"] <= 4]
        summary = "Prioritas: " + ", ".join(top_codes) if top_codes else "Stabil di semua aspek."
        out["per_umkm"][umkm] = {
            "summary": summary,
            "actions": actions,
            "review_count": s["_count"],
        }
    return out


def render_markdown(recs: dict) -> str:
    lines: list[str] = []
    lines.append("# Rekomendasi strategis per UMKM\n")
    lines.append("Hasil dari rule-based recommendation engine, dibuat dari hasil ")
    lines.append("ABSA model + comparative analytics.\n")

    lines.append("Median pasar (referensi):\n")
    lines.append("| Aspek | median positive_share |")
    lines.append("|---|---:|")
    for asp in ASPECTS:
        ps = recs["market"][asp]["median_positive_share"]
        lines.append(f"| {asp} | {fmt_pct(ps)} |")
    lines.append("")

    for umkm, data in sorted(recs["per_umkm"].items()):
        lines.append(f"## {umkm}\n")
        lines.append(f"{data['summary']} ({data['review_count']} review)\n")
        for i, a in enumerate(data["actions"], 1):
            lines.append(f"### {i}. {a['aspect']} — {a['code']}")
            lines.append("")
            ps = fmt_pct(a["positive_share"])
            ms = fmt_pct(a["market_share"])
            lines.append(f"Posisi: {ps} positive_share. Median pasar {ms}. Volume {a['volume']} mention.\n")
            if a["rationale"]:
                lines.append(f"{a['rationale']}\n")
            if a["actionable"]:
                lines.append("Actionable:\n")
                for todo in a["actionable"]:
                    lines.append(f"- {todo}")
                lines.append("")
        lines.append("---\n")
    return "\n".join(lines)


def main():
    if not SNAPSHOT.exists():
        raise SystemExit(f"{SNAPSHOT} not found. Run analyze.py first.")
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    recs = build_recommendations(snap)
    OUT_JSON.write_text(json.dumps(recs, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_MD.write_text(render_markdown(recs), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print()
    print("=== Per-UMKM priorities ===")
    for umkm, data in sorted(recs["per_umkm"].items()):
        print(f"  {umkm:30} {data['summary']}")


if __name__ == "__main__":
    main()
