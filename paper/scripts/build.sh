#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PAPER_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$PAPER_DIR"
mkdir -p build

if ! command -v latexmk >/dev/null 2>&1; then
  echo "latexmk was not found on PATH. Add the TinyTeX/TeX Live binary directory." >&2
  exit 127
fi

latexmk -pdf -interaction=nonstopmode -file-line-error -halt-on-error -outdir=build main.tex

if command -v python3 >/dev/null 2>&1; then
  python3 scripts/check_pdf.py build/main.pdf
else
  echo "python3 was not found; PDF structural validation was skipped." >&2
  exit 126
fi
