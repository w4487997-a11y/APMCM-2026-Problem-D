# L1 Completion Report

**Date:** 2026-11-27 (Asia/Shanghai)  
**Branch:** `codex/latex-environment-audit` (local only)  
**Result:** PASS — official-template minimum paper engineering established

## 1. Environment diagnosis and repair

The host initially had no TeX Live/MacTeX command-line distribution. A user-scoped TinyTeX / TeX Live 2026 installation was established and the required standard LaTeX/font collections were installed. The official recommendation to test PDFLaTeX first was followed. The current environment, repair history, font distinction, and package inventory are recorded in `compliance/latex_environment_report.md`.

The earlier Times New Roman failure belonged to the XeTeX/Tectonic path. Under PDFLaTeX the unmodified official class intentionally uses `newtxtext` and `newtxmath`; embedded TeX Gyre Termes/NewTX fonts were confirmed in the output PDF.

## 2. Compiler and version

- TinyTeX / TeX Live 2026
- pdfTeX 3.141592653-2.6-1.40.29
- Latexmk 4.89
- BibTeX 0.99e
- Primary manuscript engine: PDFLaTeX

## 3. Official template inventory

The organizer ZIP hash is `8afaef1208964095f5bae06e2a47d294fe3affd979d6b05ade4c91973f0aee7c`. It was extracted into `official_template/` without copying temporary `.aux`, `.log`, `.toc`, or `.synctex.gz` files.

Core hashes:

| File | SHA-256 |
|---|---|
| `main.tex` | `35ef7b39a32b6ddd7bf851a732644d0fba972f7d1251881489c717214b8fc5bf` |
| `apmcmthesis.cls` | `22bb5c34ee56760d2cd6af3286083e05084ea5bddf78160d8e7a4ef9b7220f26` |
| `apmcmthesis.cfg` | `5977897c04bcdcf0e34dbd7958ddbf636cd9d2413f2250a126e8b0bbd5fc882a` |
| `ControlSheet.tex` | `4ee85a304372f31f2b1a1effbcedcc0ce4ba57100069190c75655c81d104d89c` |

All official files, sizes, hashes, and roles are in `compliance/template_manifest.json`. The official sources are also snapshotted under `paper/template_original/`. Working class/config copies are byte-identical to the official versions.

## 4. Files created or modified

Official baseline:

- Extracted nine organizer-supplied source/reference/form files under `official_template/`.
- Updated `official_template/README.md` to describe the extracted, protected baseline.
- Replaced the repository's prior non-official Control Sheet starter with the byte-exact ZIP original; the starter remains recoverable from Git history.

Paper engineering:

- Added `paper/main.tex`, official class/config working copies, and `template_original/`.
- Added nine English section modules under `paper/sections/`.
- Added `paper/references.bib`.
- Added appendix entry and source-code inventory.
- Added build and PDF-check scripts.
- Added environment, template, diff, rules, page, reference, and final-PDF compliance records.
- Added this completion report.
- Added `tests/test_paper_scaffold.py` and `/paper/build/` to `.gitignore`.

No research data, model, metric, QUBO parameter, experiment result, or failed-run evidence was edited.

## 5. Actual build command

From `paper/`:

```bash
latexmk -pdf -interaction=nonstopmode -file-line-error -halt-on-error -outdir=build main.tex
python3 scripts/check_pdf.py build/main.pdf
```

The uniform entry point is:

```bash
./scripts/build.sh
```

## 6. PDF result

- Output: `paper/build/main.pdf`
- SHA-256: `aa1807eb5a774b07cdd08cec74afeaf5d45ef146052e738cf7bd850044a0e998`
- Pages: 9
- Media box: A4, 595.276 × 841.890 pt on every page
- Summary Sheet: physical page 1
- Contents: begins on physical page 2; the nine-section outline spans two pages
- Main body: begins after contents and restarts at page 1
- Fonts: embedded TeX Gyre Termes/NewTX under the official PDFLaTeX branch
- Bibliography: BibTeX completed and numbered reference rendered
- Fatal errors: none
- Structural PDF check: PASS
- Visual review: Summary Sheet, both contents pages, and first body page reviewed

The long team-number placeholder wraps within the official Summary Sheet table, and the official class emits a `headheight` warning. These are recorded non-fatal L1 limitations; the real shorter team number must replace the placeholder before release.

## 7. L1 acceptance checklist

- [x] Official original template preserved and hashed.
- [x] Official `ControlSheet.tex` independently compiles.
- [x] Working class/config remain byte-identical to official originals.
- [x] Formal `paper/` directory established.
- [x] Modular `main.tex` established.
- [x] Nine required section files established.
- [x] Summary Sheet is first.
- [x] Contents begins second.
- [x] Body follows contents with official header/page numbering.
- [x] Official PDFLaTeX font branch loads.
- [x] Mathematics and English symbols render.
- [x] Table, figure/caption, and numbered-reference mechanisms render.
- [x] Uniform build script runs.
- [x] README documents environment, ownership placeholders, figures, tables, references, build, and page checks.
- [x] Pending Q2/Q3, Kaiwu, precision, cost, 107-variable, and blind-pool work remains explicitly tied to task IDs.
- [x] No fabricated result or team identity was inserted.
- [x] No automatic push, merge, release, or platform submission occurred.

## 8. Unfinished items

L1 is an engineering scaffold, not a scientific-paper completion. The main open gates are:

- O-03 through O-07: final data/hash audit and Q1 independent sign-off.
- O-08/O-09: accepted Q2/Q3 matrices, mappings, offsets, and independent energy audits.
- O-10: optional 107-variable projection comparison.
- O-11: real-matrix precision adaptation and penalty scan.
- O-12/O-13: Kaiwu SDK closure and, only with complete evidence, real hardware execution.
- O-14: independent blind-pool matrices and solver calls if included.
- O-15: four-layer error attribution and complete cost ledger.
- O-16 through O-20: release figures, reference audit, disclosure, independent review, final PDF and submission evidence.
- Verified team number, team roles, and signed Control Sheet remain human inputs.

## 9. L2 plan

After user confirmation, L2 should add automated and manual format checks without writing scientific results:

1. Detect placeholders, Chinese body text, template sample residue, unresolved references, missing labels, and unreferenced figures/tables.
2. Separate Summary/contents/body/references/appendix page counts and enforce the final 25-page body rule when the manuscript is mature enough.
3. Inspect fonts, font size, headers, page numbering, citations, and PDF media boxes.
4. Render every page for visual review and record items that require human judgment as `MANUAL REVIEW`.
5. Keep submission naming, real team information, AI disclosure, Control Sheet signatures, and platform fields blocked until verified human input is available.

## 10. Verification evidence

Fresh verification on the completed tree produced:

```text
paper/scripts/build.sh: PASS
paper/scripts/check_pdf.py: PASS (9 A4 pages; Summary/Contents/body order)
tests/test_paper_scaffold.py: 10 passed
full pytest suite: 24 passed, 22 subtests passed
```

The project-pinned SciPy 1.15.3 wheel could not load `_spropack` on macOS 27.0.1. For verification only, the ignored `.venv-l1` environment used SciPy 1.16.3 with scikit-learn 1.7.2; the repository requirement file and research code were not changed. The official ZIP sources and both paper snapshots were re-hashed after the build and matched the recorded manifest.

`git diff --check` reports one pre-existing trailing space in the byte-exact official `ControlSheet.tex`. It is intentionally retained to preserve the organizer file hash and is not present in authored paper sources.
