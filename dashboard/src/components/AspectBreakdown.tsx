"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { UmkmSnapshot } from "@/lib/types";
import { ASPECTS } from "@/lib/types";

export function AspectBreakdown({ umkm }: { umkm: UmkmSnapshot }) {
  // one row per aspek, stacked by sentiment category
  const stacked = ASPECTS.map((asp) => {
    const a = umkm.aspects[asp];
    return {
      aspek: asp,
      positif: a.positif,
      netral: a.netral,
      negatif: a.negatif,
      td: a.tidak_disebut,
    };
  });

  return (
    <div className="h-72 w-full rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={stacked} layout="vertical" stackOffset="expand" margin={{ left: 10, right: 30, top: 10, bottom: 0 }}>
          <XAxis type="number" hide domain={[0, 1]} />
          <YAxis
            type="category"
            dataKey="aspek"
            tickLine={false}
            axisLine={false}
            width={80}
            tick={{ fill: "currentColor", fontSize: 12 }}
            tickFormatter={(v) => v.charAt(0).toUpperCase() + v.slice(1)}
          />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
            formatter={(value, name) => [`${value}`, String(name)]}
          />
          <Bar dataKey="positif" stackId="a" fill="#10b981" />
          <Bar dataKey="netral" stackId="a" fill="#f59e0b" />
          <Bar dataKey="negatif" stackId="a" fill="#ef4444" />
          <Bar dataKey="td" stackId="a" fill="#d4d4d8" />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-zinc-600 dark:text-zinc-400">
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-sm bg-[#10b981]" /> Positif
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-sm bg-[#f59e0b]" /> Netral
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-sm bg-[#ef4444]" /> Negatif
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-sm bg-[#d4d4d8]" /> Tidak disebut
        </span>
      </div>
    </div>
  );
}
