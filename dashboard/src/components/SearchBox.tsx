"use client";

import { useRouter } from "next/navigation";
import { useMemo, useRef, useState } from "react";
import { snapshot } from "@/lib/data";
import { umkmName } from "@/lib/types";

interface Entry {
  id: string;
  name: string;
  reviews: number;
}

export function SearchBox() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const blurTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const entries: Entry[] = useMemo(
    () =>
      Object.keys(snapshot.per_umkm)
        .map((id) => ({
          id,
          name: umkmName(id),
          reviews: snapshot.per_umkm[id]._count,
        }))
        .sort((a, b) => a.name.localeCompare(b.name)),
    [],
  );

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter(
      (e) => e.name.toLowerCase().includes(q) || e.id.includes(q),
    );
  }, [entries, query]);

  function go(id: string) {
    setQuery("");
    setOpen(false);
    router.push(`/umkm/${id}`);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, matches.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (matches[activeIdx]) go(matches[activeIdx].id);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div className="relative w-full max-w-xs">
      <input
        type="text"
        value={query}
        placeholder="Cari UMKM…"
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
          setActiveIdx(0);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          blurTimer.current = setTimeout(() => setOpen(false), 120);
        }}
        onKeyDown={onKeyDown}
        className="w-full rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
      />
      {open && matches.length > 0 ? (
        <ul
          className="absolute z-40 mt-1 max-h-80 w-full overflow-auto rounded-md border border-zinc-200 bg-white py-1 shadow-lg dark:border-zinc-700 dark:bg-zinc-900"
          onMouseDown={() => {
            if (blurTimer.current) clearTimeout(blurTimer.current);
          }}
        >
          {matches.map((e, i) => (
            <li key={e.id}>
              <button
                type="button"
                onClick={() => go(e.id)}
                onMouseEnter={() => setActiveIdx(i)}
                className={`flex w-full items-center justify-between px-3 py-1.5 text-left text-sm ${
                  i === activeIdx
                    ? "bg-zinc-100 dark:bg-zinc-800"
                    : "hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                }`}
              >
                <span className="text-zinc-800 dark:text-zinc-200">{e.name}</span>
                <span className="text-xs text-zinc-400">{e.reviews} review</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {open && query.trim() && matches.length === 0 ? (
        <div className="absolute z-40 mt-1 w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-500 shadow-lg dark:border-zinc-700 dark:bg-zinc-900">
          Tidak ada UMKM cocok.
        </div>
      ) : null}
    </div>
  );
}
