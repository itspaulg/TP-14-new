import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
      <p className="text-sm font-mono text-zinc-500">404</p>
      <h1 className="text-2xl font-bold tracking-tight">Halaman tidak ditemukan</h1>
      <p className="max-w-sm text-center text-sm text-zinc-600 dark:text-zinc-400">
        Pastikan slug UMKM benar. Klik tombol di bawah untuk balik ke overview.
      </p>
      <Link
        href="/"
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        Kembali ke overview
      </Link>
    </div>
  );
}
