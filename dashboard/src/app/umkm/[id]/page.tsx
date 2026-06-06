import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { snapshot, recommendations, predictions, umkmIds } from "@/lib/data";
import { umkmName, ASPECTS } from "@/lib/types";
import { fmtPct, fmtGap, STRATEGY_STYLE } from "@/lib/colors";
import { AspectBreakdown } from "@/components/AspectBreakdown";
import { RecommendationCard } from "@/components/RecommendationCard";
import { ReviewList } from "@/components/ReviewList";

export function generateStaticParams() {
  return umkmIds.map((id) => ({ id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  if (!snapshot.per_umkm[id]) return { title: "UMKM tidak ditemukan" };
  return {
    title: `${umkmName(id)} · TP-I014 Dashboard`,
    description: `Analisis sentimen per aspek + recommendation playbook untuk ${umkmName(id)}.`,
  };
}

export default async function UmkmDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const u = snapshot.per_umkm[id];
  const rec = recommendations.per_umkm[id];
  if (!u || !rec) return notFound();

  const reviews = predictions.filter((p) => p.umkm_id === id);

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/"
          className="text-sm text-zinc-500 hover:underline"
        >
          ← Overview
        </Link>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 sm:text-3xl">
          {umkmName(id)}
        </h1>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          {u._count} review dengan teks · {rec.summary}
        </p>
      </div>

      {/* KPI cards per aspek */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Posisi per aspek
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {ASPECTS.map((asp) => {
            const a = u.aspects[asp];
            const market = snapshot.market[asp].median_positive_share;
            const code = u.strategies[asp];
            const style = STRATEGY_STYLE[code];
            return (
              <div
                key={asp}
                className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-wide text-zinc-500">
                    {asp}
                  </span>
                  <span
                    className={`rounded-md px-2 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}
                  >
                    {style.label}
                  </span>
                </div>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-2xl font-bold tabular-nums">
                    {fmtPct(a.positive_share)}
                  </span>
                  <span className="text-xs text-zinc-500">positive share</span>
                </div>
                <div className="mt-1 text-xs text-zinc-500">
                  Gap vs market:{" "}
                  <span className="font-mono">
                    {fmtGap(a.positive_share, market)}
                  </span>
                </div>
                <div className="mt-2 grid grid-cols-4 gap-1 text-center text-xs">
                  <div className="rounded bg-emerald-50 py-1 dark:bg-emerald-950/30">
                    <div className="text-emerald-700 dark:text-emerald-400 font-semibold">
                      {a.positif}
                    </div>
                    <div className="text-zinc-500">pos</div>
                  </div>
                  <div className="rounded bg-red-50 py-1 dark:bg-red-950/30">
                    <div className="text-red-700 dark:text-red-400 font-semibold">
                      {a.negatif}
                    </div>
                    <div className="text-zinc-500">neg</div>
                  </div>
                  <div className="rounded bg-amber-50 py-1 dark:bg-amber-950/30">
                    <div className="text-amber-700 dark:text-amber-400 font-semibold">
                      {a.netral}
                    </div>
                    <div className="text-zinc-500">neu</div>
                  </div>
                  <div className="rounded bg-zinc-100 py-1 dark:bg-zinc-800">
                    <div className="text-zinc-600 dark:text-zinc-400 font-semibold">
                      {a.tidak_disebut}
                    </div>
                    <div className="text-zinc-500">td</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Distribution chart */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Distribusi sentimen per aspek
        </h2>
        <AspectBreakdown umkm={u} />
      </section>

      {/* Recommendations */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Recommendation playbook
        </h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {rec.actions.map((a, i) => (
            <RecommendationCard key={a.aspect} action={a} index={i + 1} />
          ))}
        </div>
      </section>

      {/* Review drill-down */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Review drill-down ({reviews.length} reviews)
        </h2>
        <ReviewList reviews={reviews} />
      </section>
    </div>
  );
}
