# APMCM Problem D Paper Engineering

This directory contains the V2 manuscript for 2026 APMCM Problem D. It is
based on the official `apmcmthesis` template extracted from the
organizer-provided ZIP. Byte-exact template sources are retained in
`../official_template/` and `template_original/`; the manuscript uses separate
working files.

## Build environment

- macOS 27.0.1 on Apple Silicon (`arm64`)
- TinyTeX / TeX Live 2026
- pdfTeX 3.141592653-2.6-1.40.29
- Latexmk 4.89
- Primary engine: PDFLaTeX, matching the recommendation in the official `main.tex`
- PDFLaTeX font path: official `newtxtext` and `newtxmath` packages (Times-compatible TeX fonts)

Ensure the TinyTeX binary directory is on `PATH`, then run from `paper/`:

```bash
./scripts/build.sh
```

The underlying command is:

```bash
latexmk -pdf -interaction=nonstopmode -file-line-error -halt-on-error -outdir=build main.tex
```

The generated manuscript is `build/main.pdf`. Intermediate files remain under `build/`, which is ignored by Git.

## Directory guide

- `main.tex`: modular working manuscript; preserves the official class, Summary Sheet, contents page, and page styles.
- `apmcmthesis.cls`, `apmcmthesis.cfg`: byte-identical working copies of the official class/config.
- `template_original/`: read-only source snapshot.
- `sections/`: nine English chapter modules.
- `figures/`, `tables/`: generated or reviewed paper assets only.
- `appendix/`: appendix entry and source-code inventory.
- `compliance/`: environment, template, page, reference, and release checks.
- `scripts/`: uniform build and PDF validation entry points.
- `build/`: generated output; never edit source here.

## Ownership placeholders

- Q1 / Data sections: `OWNER-A-PLACEHOLDER`
- Q2 / Q3 formulation: `OWNER-B-PLACEHOLDER`
- Kaiwu / precision / integration: `OWNER-C-PLACEHOLDER`
- Team number: `apmcm26312030`

Replace placeholders only with verified team information. Do not submit a PDF that still contains placeholders.

## Evidence and reproduction status

- Q1 model development, file-03 selection, retrospective budget replay and
  file-04 blind predictions are archived under `experiments/` and `handoff/v1_2/`.
- Q2/Q3 candidates are numerical argmins of the frozen proxy tables. The
  adopted two-level 104-variable QUBOs use the known group argmin and are
  precision-mapping tests, not independent discovery algorithms.
- Kaiwu SDK 1.4.3 results are CPU-local. Kaiwu 1.4.4 is used only for mapping
  controls. O-14 is local simulated annealing; O-13 contains four final
  SPQC-550 task returns.
- O-11 0/300 versus 8/300, O-14/O-15 README versus CSV/JSON timing, SDK short
  versus full timing, and the two local-SA totals remain UNVERIFIED. The quota
  ledger has seven debits but only six archived task receipts.
- Entry points, seeds, versions, matrix hashes and output paths are indexed in
  `appendix/source_code_inventory.md`; claim-to-source reading levels are in
  `compliance/reference_audit.md`.

## Adding figures and tables

Put reproducible figures in `figures/` with descriptive English filenames. Every figure and table needs an English caption, a `\label{...}`, a textual reference, and a traceable source record. Prefer editable LaTeX tables in `tables/`; use `\input{tables/name.tex}` for larger tables.

## References

Add only verified records to the single bibliography at `literature/references.bib`. Cite them with `\cite{key}`. The build invokes BibTeX through Latexmk and uses numbered citations. Record the reference audit in `compliance/reference_audit.md`.

## Final PDF and page checks

`scripts/build.sh` compiles and then runs `scripts/check_pdf.py`. Install its sole Python dependency in the chosen environment if needed:

```bash
python3 -m pip install pypdf
```

For release, count the main body separately from the Summary Sheet, contents,
references, and appendix as required by the official rules. A built PDF is not
submission-ready while the team number, AI disclosure, Control Sheet, or
platform fields remain unverified.
