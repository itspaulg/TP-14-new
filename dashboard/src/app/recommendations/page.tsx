"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { recommendations } from "@/lib/data";
import { umkmName, ASPECTS, type Aspect, type StrategyCode } from "@/lib/types";
import { STRATEGY_STYLE, fmtPct } from "@/lib/colors";

const STRATEGY_FILTERS: { id: StrategyCode | "ALL"; label: string }[] = [
  { id: "ALL", label: "Semua" },
  { id: "ATTACK", label: "Attack (urgent fix)" },
  { id: "FIX", label: "Fix (below market)" },
  { id: "DEFEND", label: "Defend (strength)" },
  { id: "PROMOTE", label: "Promote (above market)" },
  { id: "MONITOR", label: "Monitor (stable)" },
];

export default function RecommendationsPage() {
  const [strategyFilter, setStrategyFilter] = useState<StrategyCode | "ALL">("ALL");
  const [aspectFilter, setAspectFilter] = useState<Aspect | "ALL">("ALL");

  const allActions = useMemo(() => {
    const out: Array<{
      umkmId: string;
      umkmReviewCount: number;
      action: typeof recommendations.per_umkm[string]["actions"][number];
    }> = [];
    for (const [umkmId, data] of Object.entries(recommendations.per_umkm)) {
      for (const action of data.actions) {
        out.push({ umkmId, umkmReviewCount: data.review_count, action });
      }
    }
    return out.sort((a, b) => {
      if (a.action.priority !== b.action.priority) {
        return a.action.priority - b.action.priority;
      }
      return b.action.volume - a.action.volume;
    });
  }, []);

  const filtered = useMemo(() => {
    return allActions.filter(({ action }) => {
      if (strategyFilter !== "ALL" && action.code !== strategyFilter) return false;
      if (aspectFilter !== "ALL" && action.aspect !== aspectFilter) return false;
      return true;
    });
  }, [allActions, strategyFilter, aspectFilter]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 sm:text-3xl">
          Recommendation playbook lintas UMKM
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-600 dark:text-zinc-400">
          Strategi action per (UMKM, aspek) hasil dari rule-based engine. Diurut
          berdasarkan priority (ATTACK paling atas, MONITOR paling bawah), lalu
          volume mention. Klik UMKM untuk lihat detail.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900">
        <span className="text-xs uppercase tracking-wide text-zinc-500">
          Filter
        </span>
        <select
          value={strategyFilter}
          onChange={(e) => setStrategyFilter(e.target.value as StrategyCode | "ALL")}
          className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-800"
        >
          {STRATEGY_FILTERS.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
        <select
          value={aspectFilter}
          onChange={(e) => setAspectFilter(e.target.value as Aspect | "ALL")}
          className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-800"
        >
          <option value="ALL">Semua aspek</option>
          {ASPECTS.map((a) => (
            <option key={a} value={a} className="capitalize">
              {a}
            </option>
          ))}
        </select>
        <span className="ml-auto text-xs text-zinc-500">
          {filtered.length} dari {allActions.length} action
        </span>
      </div>

      {/* Actions list */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="rounded-lg border border-dashed border-zinc-300 p-8 text-center text-sm text-zinc-500 dark:border-zinc-700">
            Tidak ada action yang cocok dengan filter.
          </div>
        ) : null}
        {filtered.map(({ umkmId, action }, idx) => {
          const style = STRATEGY_STYLE[action.code];
          return (
            <div
              key={`${umkmId}-${action.aspect}-${idx}`}
              className="overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900"
            >
              <div className="flex flex-wrap items-center gap-3 border-b border-zinc-100 px-4 py-3 dark:border-zinc-800">
                <Link
                  href={`/umkm/${umkmId}#${action.aspect}`}
                  className="font-semibold text-zinc-900 hover:underline dark:text-zinc-100"
                >
                  {umkmName(umkmId)}
                </Link>
                <span className="text-xs uppercase tracking-wide text-zinc-500">
                  {action.aspect}
                </span>
                <span
                  className={`rounded-md px-2 py-0.5 text-xs font-bold ${style.bg} ${style.text}`}
                >
                  {style.label.toUpperCase()}
                </span>
                <span className="ml-auto text-xs text-zinc-500">
                  posisi {fmtPct(action.positive_share)} · pasar{" "}
                  {fmtPct(action.market_share)} · volume {action.volume}
                </span>
              </div>
              <div className="space-y-3 px-4 py-3">
                {action.rationale ? (
                  <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
                    {action.rationale}
                  </p>
                ) : null}
                {action.actionable.length > 0 ? (
                  <ul className="space-y-1 text-sm">
                    {action.actionable.map((todo, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-zinc-400">▸</span>
                        <span className="text-zinc-700 dark:text-zinc-300">
                          {todo}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
