import Link from "next/link";
import { ASPECTS, umkmName, type Snapshot } from "@/lib/types";
import { heatColor, fmtPct } from "@/lib/colors";

export function Heatmap({ snapshot }: { snapshot: Snapshot }) {
  const umkmIds = Object.keys(snapshot.per_umkm).sort();
  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">
            <th className="px-4 py-3 text-left font-medium text-zinc-700 dark:text-zinc-300">
              UMKM
            </th>
            {ASPECTS.map((asp) => (
              <th
                key={asp}
                className="px-4 py-3 text-center font-medium capitalize text-zinc-700 dark:text-zinc-300"
              >
                {asp}
              </th>
            ))}
            <th className="px-4 py-3 text-right font-medium text-zinc-700 dark:text-zinc-300">
              reviews
            </th>
          </tr>
        </thead>
        <tbody>
          {umkmIds.map((id) => {
            const u = snapshot.per_umkm[id];
            return (
              <tr
                key={id}
                className="border-b border-zinc-100 hover:bg-zinc-50 dark:border-zinc-900 dark:hover:bg-zinc-900/50"
              >
                <td className="px-4 py-2">
                  <Link
                    href={`/umkm/${id}`}
                    className="font-medium text-zinc-900 hover:underline dark:text-zinc-100"
                  >
                    {umkmName(id)}
                  </Link>
                </td>
                {ASPECTS.map((asp) => {
                  const a = u.aspects[asp];
                  const share = a.positive_share;
                  const bg = heatColor(share);
                  const dim = a.decisive < snapshot.min_volume_threshold;
                  return (
                    <td key={asp} className="px-1 py-1">
                      <Link
                        href={`/umkm/${id}#${asp}`}
                        className="block rounded px-3 py-2 text-center font-mono text-xs font-semibold text-white shadow-sm"
                        style={{
                          backgroundColor: bg,
                          opacity: dim ? 0.4 : 1,
                        }}
                        title={`${a.positif}+ ${a.negatif}- ${a.netral}~ ${a.tidak_disebut}TD (vol ${a.volume})`}
                      >
                        {fmtPct(share)}
                      </Link>
                    </td>
                  );
                })}
                <td className="px-4 py-2 text-right tabular-nums text-zinc-500">
                  {u._count}
                </td>
              </tr>
            );
          })}
          <tr className="bg-zinc-100/70 font-medium dark:bg-zinc-900">
            <td className="px-4 py-3 text-zinc-700 dark:text-zinc-300">
              Median pasar
            </td>
            {ASPECTS.map((asp) => (
              <td
                key={asp}
                className="px-4 py-3 text-center tabular-nums text-zinc-700 dark:text-zinc-300"
              >
                {fmtPct(snapshot.market[asp].median_positive_share)}
              </td>
            ))}
            <td className="px-4 py-3 text-right tabular-nums text-zinc-500">
              {snapshot.total_reviews} total
            </td>
          </tr>
        </tbody>
      </table>
      <div className="border-t border-zinc-200 bg-zinc-50 px-4 py-2 text-xs text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900">
        Sel adalah <strong>positive share</strong> = positif / (positif + negatif) untuk
        review yang menyebut aspek. Sel transparan = volume mention &lt;{" "}
        {snapshot.min_volume_threshold} (data tidak signifikan).
      </div>
    </div>
  );
}
