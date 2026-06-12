import Link from "next/link";
import { SearchBox } from "./SearchBox";

export function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-zinc-200 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="text-lg font-semibold tracking-tight">TP-I014</span>
          <span className="hidden text-xs text-zinc-500 sm:inline">
            ABSA Dashboard
          </span>
        </Link>

        <div className="order-last w-full sm:order-none sm:ml-2 sm:w-auto sm:flex-1">
          <SearchBox />
        </div>

        <nav className="flex items-center gap-1 text-sm">
          <Link
            href="/"
            className="rounded-md px-3 py-1.5 text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Overview
          </Link>
          <Link
            href="/recommendations"
            className="rounded-md px-3 py-1.5 text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Recommendations
          </Link>
          <Link
            href="/analyze"
            className="rounded-md px-3 py-1.5 text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Analyze
          </Link>
        </nav>
      </div>
    </header>
  );
}
