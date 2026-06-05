import Link from "next/link";
import { umkmName, type Aspect, type Snapshot } from "@/lib/types";
import { fmtPct } from "@/lib/colors";
import { StrategyBadge } from "./StrategyBadge";

export function Leaderboard({
  snapshot,
  aspect,
}: {
  snapshot: Snapshot;
  aspect: Aspect;
}) {
  const minVol = snapshot.min_volume_threshold;
  const rank = Object.entries(snapshot.per_umkm)
    .filter(
      ([, u]) =>
        u.aspects[aspect].decisive >= minVol &&
        u.aspects[aspect].positive_share !== null,
    )
    .map(([id, u]) => ({
      id,
      share: u.aspects[aspect].positive_share!,
      volume: u.aspects[aspect].volume,
      pos: u.aspects[aspect].positif,
      neg: u.aspects[aspect].negatif,
      strategy: u.strategies[aspect],
    }))
    .sort((a, b) => b.share - a.share);

  const marketShare = snapshot.market[aspect].median_positive_share;

  return (
    <div className="rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
        <h3 className="text-base font-semibold capitalize text-zinc-900 dark:text-zinc-100">
          {aspect}
        </h3>
        <p className="text-xs text-zinc-500">
          Median pasar: <span className="font-mono">{fmtPct(marketShare)}</span>
        </p>
      </div>
      <ol className="divide-y divide-zinc-100 text-sm dark:divide-zinc-800">
        {rank.map((r, i) => (
          <li
            key={r.id}
            className="flex items-center gap-3 px-4 py-2 hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
          >
            <span className="w-5 text-right font-mono text-xs text-zinc-400">
              {i + 1}
            </span>
            <Link
              href={`/umkm/${r.id}`}
              className="flex-1 truncate font-medium text-zinc-800 hover:underline dark:text-zinc-200"
            >
              {umkmName(r.id)}
            </Link>
            <span className="tabular-nums font-mono text-zinc-700 dark:text-zinc-300">
              {fmtPct(r.share)}
            </span>
            <StrategyBadge code={r.strategy} />
          </li>
        ))}
      </ol>
    </div>
  );
}
