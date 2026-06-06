import { STRATEGY_STYLE, fmtPct } from "@/lib/colors";
import type { RecommendationAction } from "@/lib/types";

export function RecommendationCard({
  action,
  index,
}: {
  action: RecommendationAction;
  index: number;
}) {
  const style = STRATEGY_STYLE[action.code];
  return (
    <div
      id={action.aspect}
      className="scroll-mt-20 overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div className={`border-b border-zinc-200 px-4 py-3 dark:border-zinc-800 ${style.bg}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-zinc-500">#{index}</span>
            <span className="text-lg font-semibold capitalize tracking-tight">
              {action.aspect}
            </span>
            <span className={`rounded-md px-2 py-0.5 text-xs font-bold ${style.text}`}>
              {style.label.toUpperCase()}
            </span>
          </div>
          <div className="text-xs text-zinc-600 dark:text-zinc-400">
            posisi {fmtPct(action.positive_share)} · pasar {fmtPct(action.market_share)}
          </div>
        </div>
      </div>

      <div className="space-y-3 px-4 py-3">
        {action.rationale ? (
          <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
            {action.rationale}
          </p>
        ) : null}

        {action.actionable.length > 0 ? (
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Actionable
            </div>
            <ul className="space-y-1.5 text-sm">
              {action.actionable.map((todo, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-zinc-400">▸</span>
                  <span className="text-zinc-700 dark:text-zinc-300">{todo}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="text-xs text-zinc-500">
          Volume mention: {action.volume}
        </div>
      </div>
    </div>
  );
}
