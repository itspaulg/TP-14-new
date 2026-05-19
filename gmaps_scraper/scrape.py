#!/usr/bin/env python3
"""
Google Maps reviews scraper for UMKM F&B (TP-I014 - Aspect-Based Sentiment Analysis).

Usage:
  python scrape.py                                          # interactive prompt
  python scrape.py --url "<gmaps url>" --id <slug>          # CLI
  python scrape.py --url "..." --id slug --target 300
  python scrape.py --url "..." --id slug --headless
  python scrape.py --url "..." --id slug --profile akun2    # rotate Google profile

Output: output/raw/<umkm_id>.csv
Columns: umkm_id, author, rating, date_relative, text
"""

import argparse
import csv
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).parent
USER_DATA_ROOT = ROOT / "user_data"
OUTPUT_DIR = ROOT / "output" / "raw"


# ---------- consent.google.com handling ----------

def handle_consent(page, attempts: int = 2) -> bool:
    """If redirected to consent.google.com, click reject/accept to bypass.
    Returns True if no longer on consent page after handling."""
    for _ in range(attempts):
        if "consent.google.com" not in page.url:
            return True
        print(f"[consent] on {page.url}")
        # Order: prefer Reject (no login required, less tracking).
        # In Maps consent, the primary form buttons have aria-labels in current locale.
        selectors = [
            'button[aria-label="Reject all"]',
            'button[aria-label="Tolak semua"]',
            'button:has-text("Reject all")',
            'button:has-text("Tolak semua")',
            'button[aria-label="Accept all"]',
            'button[aria-label="Setujui semua"]',
            'button:has-text("Accept all")',
            'button:has-text("Setujui semua")',
            # last-resort: any form submit button
            'form button[type="submit"]',
        ]
        clicked = False
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    loc.click(timeout=3000)
                    print(f"[consent] clicked {sel!r}")
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            print("[consent] no known button found; waiting for manual click...")
        # wait for redirect
        try:
            page.wait_for_url(lambda u: "consent.google.com" not in u, timeout=30000)
        except PWTimeout:
            pass
    return "consent.google.com" not in page.url


# ---------- review tab + sort ----------

def click_first_visible(page, selectors, label: str, timeout_each: int = 2000) -> bool:
    for sel in selectors:
        loc = page.locator(sel).first
        try:
            if loc.count() > 0 and loc.is_visible():
                loc.click(timeout=timeout_each)
                print(f"[{label}] clicked {sel!r}")
                return True
        except Exception:
            continue
    return False


def open_reviews_tab(page) -> bool:
    selectors = [
        'button[role="tab"][aria-label*="ulasan" i]',
        'button[role="tab"][aria-label*="review" i]',
        'button[aria-label*="Lainnya ulasan" i]',
        'button[aria-label*="More reviews" i]',
    ]
    return click_first_visible(page, selectors, "reviews-tab")


def sort_by_newest(page) -> bool:
    sort_btn_sels = [
        'button[aria-label*="urutkan" i]',
        'button[aria-label*="Sort review" i]',
        'button[data-value*="Sort" i]',
    ]
    if not click_first_visible(page, sort_btn_sels, "sort-button", timeout_each=3000):
        return False
    page.wait_for_timeout(500)
    option_sels = [
        '[role="menuitemradio"]:has-text("Terbaru")',
        '[role="menuitemradio"]:has-text("Newest")',
        '[role="menuitem"]:has-text("Terbaru")',
        '[role="menuitem"]:has-text("Newest")',
        'div:has-text("Terbaru")[role^="menu"]',
    ]
    return click_first_visible(page, option_sels, "sort-option", timeout_each=3000)


# ---------- scroll + extract (JS) ----------

_OUTER_FN = r"""
  const outerItems = () => Array.from(document.querySelectorAll('[data-review-id]'))
    .filter(el => {
      const p = el.parentElement;
      return !p || !p.closest('[data-review-id]');
    });
"""

JS_SCROLL = r"""
() => {
""" + _OUTER_FN + r"""
  // Pick the feed that actually contains review items — search-style URLs
  // show a second role=feed (search results) on the left which must be ignored.
  let el = null;
  const feeds = document.querySelectorAll('div[role="feed"]');
  for (const f of feeds) {
    if (f.querySelector('[data-review-id]')) { el = f; break; }
  }
  if (!el) {
    const item = document.querySelector('[data-review-id]');
    if (item) {
      let p = item.parentElement;
      while (p && p !== document.body) {
        const s = window.getComputedStyle(p);
        if ((s.overflowY === 'auto' || s.overflowY === 'scroll') && p.scrollHeight > p.clientHeight) {
          el = p;
          break;
        }
        p = p.parentElement;
      }
    }
  }
  if (el) {
    el.scrollTop = el.scrollHeight;
    return { found: true, count: outerItems().length };
  }
  return { found: false, count: outerItems().length };
}
"""

JS_COUNT = r"""
() => {
""" + _OUTER_FN + r"""
  return outerItems().length;
}
"""

JS_EXPAND = r"""
() => {
  let n = 0;
  document.querySelectorAll('button').forEach(b => {
    const t = (b.innerText || '').trim().toLowerCase();
    if (t === 'more' || t === 'selengkapnya' || t === 'lainnya') {
      try { b.click(); n++; } catch (e) {}
    }
  });
  return n;
}
"""

JS_EXTRACT = r"""
() => {
""" + _OUTER_FN + r"""
  const items = outerItems();
  return items.map(el => {
    const reviewId = el.getAttribute('data-review-id') || '';

    // author
    let author = '';
    const aSel = ['.d4r55', '[class*="d4r55"]', 'div[class*="author"]'];
    for (const s of aSel) {
      const a = el.querySelector(s);
      if (a && a.innerText.trim()) { author = a.innerText.trim().split('\n')[0]; break; }
    }

    // rating
    let rating = null;
    const ratingEls = el.querySelectorAll('[role="img"][aria-label]');
    for (const r of ratingEls) {
      const lab = r.getAttribute('aria-label') || '';
      // examples: "5 stars", "4 bintang", "Rated 5.0 out of 5"
      const m = lab.match(/(\d+(?:[.,]\d+)?)\s*(?:bintang|star)/i) || lab.match(/(\d+(?:[.,]\d+)?)/);
      if (m) { rating = parseFloat(m[1].replace(',', '.')); break; }
    }

    // date_relative
    let dateRel = '';
    const dSel = ['.rsqaWe', '[class*="rsqaWe"]', '.DU9Pgb > span:not([role="img"])', 'span.xRkPPb'];
    for (const s of dSel) {
      const d = el.querySelector(s);
      if (d && d.innerText.trim()) { dateRel = d.innerText.trim(); break; }
    }

    // text
    let text = '';
    const tSel = ['.wiI7pd', '[class*="wiI7pd"]', '.MyEned span', 'span[class*="review-full-text"]'];
    for (const s of tSel) {
      const t = el.querySelector(s);
      if (t && t.innerText.trim()) { text = t.innerText.trim(); break; }
    }

    return { reviewId, author, rating, dateRel, text };
  });
}
"""


def collect_reviews(page, target: int, max_stagnant: int = 12, sleep_ms: int = 1600) -> list:
    """Scroll the reviews feed, extracting incrementally so we don't lose items
    to DOM virtualization. Returns a list of unique review dicts."""
    collected: dict[str, dict] = {}
    last_unique = 0
    stagnant = 0
    it = 0
    while True:
        it += 1
        page.evaluate(JS_SCROLL)
        page.wait_for_timeout(sleep_ms)
        # expand "More" buttons on currently-visible items
        page.evaluate(JS_EXPAND)
        page.wait_for_timeout(300)
        batch = page.evaluate(JS_EXTRACT)
        for r in batch:
            rid = r.get("reviewId") or ""
            if not rid:
                continue
            if rid not in collected:
                collected[rid] = r
            else:
                # update if the text is now non-empty (e.g. "More" expanded after scroll)
                if not collected[rid].get("text") and r.get("text"):
                    collected[rid]["text"] = r["text"]
        unique = len(collected)
        if it == 1 or it % 3 == 0 or unique >= target:
            print(f"[scroll] iter={it} unique={unique} dom_batch={len(batch)}")
        if unique >= target:
            break
        if unique == last_unique:
            stagnant += 1
            if stagnant >= max_stagnant:
                print(f"[scroll] stagnant {max_stagnant} iters; stopping at {unique}")
                break
        else:
            stagnant = 0
            last_unique = unique
    return list(collected.values())


# ---------- main flow ----------

def scrape(url: str, umkm_id: str, target: int, headless: bool, profile: str) -> int:
    user_data_dir = USER_DATA_ROOT / profile
    user_data_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{umkm_id}.csv"

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=headless,
            locale="id-ID",
            timezone_id="Asia/Jakarta",
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()

        print(f"[goto] {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)

        if not handle_consent(page):
            print("[consent] WARNING: still on consent page; please intervene manually.")

        try:
            page.wait_for_selector("h1", timeout=20000)
        except PWTimeout:
            print("[warn] no <h1> after 20s — continuing")

        title = ""
        try:
            title = page.locator("h1").first.inner_text(timeout=2000)
        except Exception:
            pass
        print(f"[place] {title!r}")

        opened = open_reviews_tab(page)
        print(f"[reviews] tab opened: {opened}")
        page.wait_for_timeout(2000)

        sorted_ok = sort_by_newest(page)
        print(f"[sort] newest: {sorted_ok}")
        page.wait_for_timeout(2000)

        try:
            page.wait_for_selector("[data-review-id]", timeout=25000)
        except PWTimeout:
            print("[fatal] no [data-review-id] elements appeared.")
            context.close()
            return 0

        reviews = collect_reviews(page, target)
        print(f"[collect] {len(reviews)} unique reviews")

        written = 0
        with out_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            w.writerow(["umkm_id", "author", "rating", "date_relative", "text"])
            for r in reviews:
                w.writerow([
                    umkm_id,
                    (r.get("author") or "").strip(),
                    r.get("rating") if r.get("rating") is not None else "",
                    (r.get("dateRel") or "").strip(),
                    (r.get("text") or "").replace("\r", " ").strip(),
                ])
                written += 1
        print(f"[save] {written} rows → {out_path}")

        context.close()
        return written


def parse_args():
    p = argparse.ArgumentParser(description="Scrape Google Maps reviews for one UMKM.")
    p.add_argument("--url", help="Google Maps place URL")
    p.add_argument("--id", dest="umkm_id", help="Output slug, e.g. nasi_goreng_surya")
    p.add_argument("--target", type=int, default=200, help="Minimum reviews to collect (default 200)")
    p.add_argument("--headless", action="store_true", help="Run headless (default: headed)")
    p.add_argument("--profile", default="default", help="Browser profile name (for account rotation)")
    return p.parse_args()


def main():
    a = parse_args()
    if not a.url:
        a.url = input("Paste Google Maps URL: ").strip()
    if not a.umkm_id:
        a.umkm_id = input("UMKM ID (slug): ").strip()
    if not a.url or not a.umkm_id:
        sys.exit("URL and UMKM ID are required.")

    n = scrape(a.url, a.umkm_id, target=a.target, headless=a.headless, profile=a.profile)
    print(f"\nDONE. Saved {n} reviews to output/raw/{a.umkm_id}.csv")
    if n < a.target:
        print(f"NOTE: collected {n} < target {a.target}. Either fewer reviews exist or scroll stagnated.")


if __name__ == "__main__":
    main()
