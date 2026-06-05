import { snapshot } from "@/lib/data";
import { Heatmap } from "@/components/Heatmap";
import { Leaderboard } from "@/components/Leaderboard";
import { ASPECTS } from "@/lib/types";
import { fmtPct } from "@/lib/colors";

export default function OverviewPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 sm:text-3xl">
          Comparative ABSA Intelligence — Nasi Goreng Medan
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-600 dark:text-zinc-400">
          Hasil aspect-based sentiment analysis terhadap{" "}
          <strong className="text-zinc-900 dark:text-zinc-100">
            {snapshot.total_reviews} review
          </strong>{" "}
          Google Maps dari{" "}
          <strong className="text-zinc-900 dark:text-zinc-100">
            {snapshot.umkm_count} UMKM
          </strong>{" "}
          nasi goreng iconic di Medan. Posisi kompetitif per UMKM × aspek (rasa,
          harga, pelayanan) ditampilkan relatif terhadap median pasar.
        </p>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Market median
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {ASPECTS.map((asp) => {
            const m = snapshot.market[asp];
            return (
              <div
                key={asp}
                className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="text-xs uppercase tracking-wide text-zinc-500">
                  {asp}
                </div>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-3xl font-bold tabular-nums text-zinc-900 dark:text-zinc-100">
                    {fmtPct(m.median_positive_share)}
                  </span>
                  <span className="text-xs text-zinc-500">positive share</span>
                </div>
                <div className="mt-1 text-xs text-zinc-500">
                  net sentiment{" "}
                  <span className="font-mono">
                    {m.median_net_sentiment !== null
                      ? (m.median_net_sentiment >= 0 ? "+" : "") +
                        m.median_net_sentiment.toFixed(2)
                      : "—"}
                  </span>
                  {" · "}
                  {m.n_umkm} UMKM
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Heatmap — UMKM × aspek
        </h2>
        <Heatmap snapshot={snapshot} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Leaderboard per aspek
        </h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {ASPECTS.map((asp) => (
            <Leaderboard key={asp} snapshot={snapshot} aspect={asp} />
          ))}
        </div>
      </section>
    </div>
  );
}
