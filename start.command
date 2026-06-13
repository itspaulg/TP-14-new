#!/bin/bash
# ===================================================================
# TP-I014 ABSA Dashboard — launcher
# Double-click file ini dari Finder untuk jalanin semuanya.
# Browser akan terbuka otomatis ke http://localhost:3000
# Tekan Ctrl+C di window ini untuk stop semua.
# ===================================================================

# pastikan node + python ketemu walau dijalanin dari Finder
export PATH="/usr/local/bin:/opt/homebrew/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"

cd "$(dirname "$0")"
PROJECT="$(pwd)"

echo "==============================================="
echo "  TP-I014 ABSA Dashboard"
echo "==============================================="
echo ""

# --- 1. backend live-analyze (opsional, kalau model ada) ---
BACKEND_PID=""
if [ -f "$PROJECT/absa/models/indobert-absa/model.safetensors" ]; then
  echo "[backend] menyalakan live-analyze API di :8000 ..."
  ( cd "$PROJECT/api" && python3 -m uvicorn main:app --port 8000 >/tmp/tp14-api.log 2>&1 ) &
  BACKEND_PID=$!
else
  echo "[backend] model belum ada — fitur live analyze nonaktif (dashboard tetap jalan)."
  echo "          aktifkan dgn: cd absa && python3 train.py --epochs 5 --no-class-weight"
fi
echo ""

# --- 2. buka browser otomatis begitu dashboard siap ---
( for i in $(seq 1 40); do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
      open http://localhost:3000
      break
    fi
    sleep 1
  done ) &

# --- 3. dashboard (foreground — log muncul di window ini) ---
echo "[dashboard] menyalakan di http://localhost:3000 ..."
echo ""
echo ">>> Browser terbuka otomatis. Tekan Ctrl+C untuk stop semua. <<<"
echo ""

cleanup() {
  echo ""
  echo "menutup..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  exit 0
}
trap cleanup INT TERM

cd "$PROJECT/dashboard"
npm run dev

# kalau npm berhenti, matiin backend juga
[ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
