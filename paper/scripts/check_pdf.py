#!/usr/bin/env python3
"""Check the structural properties of an APMCM manuscript PDF."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


A4_WIDTH_PT = 595.276
A4_HEIGHT_PT = 841.890
TOLERANCE_PT = 1.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        from pypdf import PdfReader
    except ImportError:
        print("pypdf is required: python3 -m pip install pypdf", file=sys.stderr)
        return 2

    if not args.pdf.is_file():
        print(f"missing PDF: {args.pdf}", file=sys.stderr)
        return 2

    reader = PdfReader(str(args.pdf))
    errors: list[str] = []
    if len(reader.pages) < 3:
        print("FAIL: expected at least Summary Sheet, contents, and one body page")
        return 1

    for number, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if abs(width - A4_WIDTH_PT) > TOLERANCE_PT or abs(height - A4_HEIGHT_PT) > TOLERANCE_PT:
            errors.append(f"page {number} is not A4: {width:.3f} x {height:.3f} pt")

    first = reader.pages[0].extract_text() or ""
    second = reader.pages[1].extract_text() or ""
    if "summary sheet" not in first.lower():
        errors.append("page 1 does not contain the Summary Sheet marker")
    if "contents" not in second.lower():
        errors.append("page 2 does not contain the contents marker")

    body_page = None
    for page in reader.pages[2:]:
        text = page.extract_text() or ""
        if "Team #" in text and "Page 1 of" in text:
            body_page = text
            break
    if body_page is None:
        errors.append("could not locate the first body page after the contents")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print(f"PASS: {args.pdf} has {len(reader.pages)} A4 pages with Summary/Contents/body ordering")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
