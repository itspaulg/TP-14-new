"use client";

import { useState } from "react";
import { ASPECTS } from "@/lib/types";
import { STRATEGY_STYLE, fmtPct, fmtGap } from "@/lib/colors";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

interface AspectResult {
  positif: number;
  negatif: number;
  netral: number;
  tidak_disebut: number;
  volume: number;
  decisive: number;
  positive_share: number | null;
  net_sentiment: number | null;
  market_share: number | null;
  strategy: keyof typeof STRATEGY_STYLE;
  rationale: string;
  actionable: string[];
}

interface AnalyzeResult {
  name: string;
  place_title: string;
  review_count: number;
  with_text: number;
  market: Record<string, number | null>;
  aspects: Record<string, AspectResult>;
}

export default function AnalyzePage() {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [target, setTarget] = useState(80);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);

  async function run() {
    setError(null);
    setResult(null);
    if (!url.trim()) {
      setError("Masukkan URL Google Maps dulu.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, name: name || null, target }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      setResult(await res.json());
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.includes("Failed to fetch")) {
        setError(
          "Tidak bisa connect ke backend. Pastikan API jalan: `cd api && uvicorn main:app --port 8000`",
        );
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 sm:text-3xl">
          Analyze UMKM baru (live)
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-600 dark:text-zinc-400">
          Tempel URL Google Maps UMKM F&B apa pun. Sistem akan scrape review,
          jalankan IndoBERT untuk 3 aspek, lalu bandingkan dengan median pasar
          nasi goreng Medan. Proses ini <strong>tidak instan</strong> — scraping
          butuh ~1-2 menit.
        </p>
      </div>

      <div className="space-y-3 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
            URL Google Maps
          </label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.google.com/maps/place/..."
            className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="flex-1 min-w-[200px]">
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
              Nama (opsional)
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="auto-detect dari Maps"
              className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
          <div className="w-32">
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
              Target review
            </label>
            <input
              type="number"
              value={target}
              min={20}
              max={300}
              onChange={(e) => setTarget(Number(e.target.value))}
              className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="rounded-md bg-zinc-900 px-5 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
        >
          {loading ? "Menganalisis… (~1-2 menit)" : "Analyze"}
        </button>
      </div>

      {loading ? (
        <div className="flex items-center gap-3 rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-zinc-100" />
          <div className="text-sm text-zinc-600 dark:text-zinc-400">
            Scraping review dari Google Maps lalu inference IndoBERT… jangan tutup
            tab ini.
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-bold tracking-tight">{result.name}</h2>
            <p className="text-sm text-zinc-500">
              {result.review_count} review di-scrape · {result.with_text} berteks
              · dibandingkan dengan median pasar nasi goreng Medan
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {ASPECTS.map((asp) => {
              const a = result.aspects[asp];
              const style = STRATEGY_STYLE[a.strategy];
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
                    pasar {fmtPct(a.market_share)} · gap{" "}
                    <span className="font-mono">
                      {fmtGap(a.positive_share, a.market_share)}
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-4 gap-1 text-center text-xs">
                    <div className="rounded bg-emerald-50 py-1 dark:bg-emerald-950/30">
                      <div className="font-semibold text-emerald-700 dark:text-emerald-400">
                        {a.positif}
                      </div>
                      <div className="text-zinc-500">pos</div>
                    </div>
                    <div className="rounded bg-red-50 py-1 dark:bg-red-950/30">
                      <div className="font-semibold text-red-700 dark:text-red-400">
                        {a.negatif}
                      </div>
                      <div className="text-zinc-500">neg</div>
                    </div>
                    <div className="rounded bg-amber-50 py-1 dark:bg-amber-950/30">
                      <div className="font-semibold text-amber-700 dark:text-amber-400">
                        {a.netral}
                      </div>
                      <div className="text-zinc-500">neu</div>
                    </div>
                    <div className="rounded bg-zinc-100 py-1 dark:bg-zinc-800">
                      <div className="font-semibold text-zinc-600 dark:text-zinc-400">
                        {a.tidak_disebut}
                      </div>
                      <div className="text-zinc-500">td</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">
              Recommendation
            </h3>
            {ASPECTS.map((asp) => {
              const a = result.aspects[asp];
              const style = STRATEGY_STYLE[a.strategy];
              return (
                <div
                  key={asp}
                  className="overflow-hidden rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <div
                    className={`flex items-center gap-2 border-b border-zinc-200 px-4 py-2 dark:border-zinc-800 ${style.bg}`}
                  >
                    <span className="font-semibold capitalize">{asp}</span>
                    <span className={`text-xs font-bold ${style.text}`}>
                      {style.label.toUpperCase()}
                    </span>
                  </div>
                  <div className="space-y-2 px-4 py-3">
                    {a.rationale ? (
                      <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
                        {a.rationale}
                      </p>
                    ) : null}
                    {a.actionable.length > 0 ? (
                      <ul className="space-y-1 text-sm">
                        {a.actionable.map((todo, i) => (
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

          <p className="text-xs text-zinc-500">
            Catatan: median pasar dihitung dari 9 UMKM nasi goreng Medan. Untuk
            kategori F&B yg sangat berbeda, akurasi model dan relevansi
            benchmark bisa berkurang (domain shift).
          </p>
        </div>
      ) : null}
    </div>
  );
}
