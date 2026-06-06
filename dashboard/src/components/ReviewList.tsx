"use client";

import { useMemo, useState } from "react";
import type { Aspect, Label, Prediction } from "@/lib/types";
import { ASPECTS } from "@/lib/types";
import { LABEL_STYLE } from "@/lib/colors";

const SENTIMENTS: { id: Label | "all"; label: string }[] = [
  { id: "all", label: "Semua" },
  { id: "positif", label: "Positif" },
  { id: "negatif", label: "Negatif" },
  { id: "netral", label: "Netral" },
];

export function ReviewList({ reviews }: { reviews: Prediction[] }) {
  const [aspect, setAspect] = useState<Aspect | "all">("all");
  const [sentiment, setSentiment] = useState<Label | "all">("all");
  const [limit, setLimit] = useState(10);

  const filtered = useMemo(() => {
    return reviews.filter((r) => {
      if (aspect === "all") {
        if (sentiment === "all") return true;
        return ASPECTS.some((a) => r[a] === sentiment);
      }
      const v = r[aspect];
      if (sentiment === "all") return v !== "tidak_disebut";
      return v === sentiment;
    });
  }, [reviews, aspect, sentiment]);

  const visible = filtered.slice(0, limit);

  return (
    <div className="rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex flex-wrap items-center gap-3 border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
        <span className="text-xs uppercase tracking-wide text-zinc-500">Filter</span>
        <select
          value={aspect}
          onChange={(e) => {
            setAspect(e.target.value as Aspect | "all");
            setLimit(10);
          }}
          className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-800"
        >
          <option value="all">Semua aspek</option>
          {ASPECTS.map((a) => (
            <option key={a} value={a} className="capitalize">
              {a}
            </option>
          ))}
        </select>
        <select
          value={sentiment}
          onChange={(e) => {
            setSentiment(e.target.value as Label | "all");
            setLimit(10);
          }}
          className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-sm dark:border-zinc-700 dark:bg-zinc-800"
        >
          {SENTIMENTS.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
        <span className="ml-auto text-xs text-zinc-500">
          {filtered.length} review match
        </span>
      </div>

      <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
        {visible.length === 0 ? (
          <li className="px-4 py-8 text-center text-sm text-zinc-500">
            Tidak ada review yang cocok dengan filter.
          </li>
        ) : null}
        {visible.map((r) => (
          <li key={r.review_id} className="px-4 py-3">
            <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded bg-amber-100 px-1.5 py-0.5 font-semibold text-amber-800 dark:bg-amber-950/50 dark:text-amber-300">
                {r.rating}★
              </span>
              {ASPECTS.map((a) => {
                const v = r[a];
                if (v === "tidak_disebut") return null;
                const style = LABEL_STYLE[v];
                return (
                  <span
                    key={a}
                    className={`rounded px-1.5 py-0.5 ${style.bg} ${style.text}`}
                  >
                    {a}: {style.label.toLowerCase()}
                  </span>
                );
              })}
            </div>
            <p className="text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">
              {r.text}
            </p>
          </li>
        ))}
      </ul>

      {visible.length < filtered.length ? (
        <div className="border-t border-zinc-200 px-4 py-3 text-center dark:border-zinc-800">
          <button
            onClick={() => setLimit(limit + 20)}
            className="text-sm text-zinc-700 hover:underline dark:text-zinc-300"
          >
            Tampilkan {Math.min(20, filtered.length - visible.length)} lagi
          </button>
        </div>
      ) : null}
    </div>
  );
}
