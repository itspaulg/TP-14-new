import type { StrategyCode, Label } from "./types";

export const STRATEGY_STYLE: Record<StrategyCode, { bg: string; text: string; label: string; emoji: string }> = {
  ATTACK: { bg: "bg-red-100 dark:bg-red-950/50", text: "text-red-800 dark:text-red-300", label: "Attack", emoji: "🚨" },
  FIX: { bg: "bg-orange-100 dark:bg-orange-950/50", text: "text-orange-800 dark:text-orange-300", label: "Fix", emoji: "⚠️" },
  MONITOR: { bg: "bg-zinc-100 dark:bg-zinc-800", text: "text-zinc-700 dark:text-zinc-300", label: "Monitor", emoji: "👁" },
  PROMOTE: { bg: "bg-sky-100 dark:bg-sky-950/50", text: "text-sky-800 dark:text-sky-300", label: "Promote", emoji: "📣" },
  DEFEND: { bg: "bg-emerald-100 dark:bg-emerald-950/50", text: "text-emerald-800 dark:text-emerald-300", label: "Defend", emoji: "🛡" },
  NO_DATA: { bg: "bg-zinc-50 dark:bg-zinc-900", text: "text-zinc-500 dark:text-zinc-500", label: "No Data", emoji: "—" },
};

export const LABEL_STYLE: Record<Label, { bg: string; text: string; label: string }> = {
  positif: { bg: "bg-emerald-100 dark:bg-emerald-950/50", text: "text-emerald-700 dark:text-emerald-300", label: "Positif" },
  negatif: { bg: "bg-red-100 dark:bg-red-950/50", text: "text-red-700 dark:text-red-300", label: "Negatif" },
  netral: { bg: "bg-amber-100 dark:bg-amber-950/50", text: "text-amber-700 dark:text-amber-300", label: "Netral" },
  tidak_disebut: { bg: "bg-zinc-100 dark:bg-zinc-800", text: "text-zinc-500 dark:text-zinc-500", label: "TD" },
};

/** Return hex color for heatmap cell based on positive_share. */
export function heatColor(share: number | null): string {
  if (share === null) return "rgb(244 244 245)";
  // gradient: red (0) -> yellow (0.5) -> green (1)
  const x = Math.max(0, Math.min(1, share));
  if (x < 0.5) {
    // red to amber
    const t = x * 2;
    const r = 239 + (245 - 239) * t;
    const g = 68 + (158 - 68) * t;
    const b = 68 + (11 - 68) * t;
    return `rgb(${Math.round(r)} ${Math.round(g)} ${Math.round(b)})`;
  }
  // amber to green
  const t = (x - 0.5) * 2;
  const r = 245 + (16 - 245) * t;
  const g = 158 + (185 - 158) * t;
  const b = 11 + (129 - 11) * t;
  return `rgb(${Math.round(r)} ${Math.round(g)} ${Math.round(b)})`;
}

export function fmtPct(x: number | null): string {
  if (x === null) return "—";
  return `${(x * 100).toFixed(1)}%`;
}

export function fmtGap(umkmShare: number | null, marketShare: number | null): string {
  if (umkmShare === null || marketShare === null) return "—";
  const gap = (umkmShare - marketShare) * 100;
  const sign = gap >= 0 ? "+" : "";
  return `${sign}${gap.toFixed(1)}pp`;
}
