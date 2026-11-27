# Official Template Acceptance

**Date:** 2026-11-27 (Asia/Shanghai)  
**Decision:** PASS for the official class/config and the L1 working manuscript  
**Primary engine:** PDFLaTeX

## Official baseline and hashes

The organizer ZIP is the sole official baseline. Its SHA-256 is `8afaef1208964095f5bae06e2a47d294fe3affd979d6b05ade4c91973f0aee7c`. The complete file manifest is in `template_manifest.json`. Core source hashes are:

| File | SHA-256 |
|---|---|
| `main.tex` | `35ef7b39a32b6ddd7bf851a732644d0fba972f7d1251881489c717214b8fc5bf` |
| `apmcmthesis.cls` | `22bb5c34ee56760d2cd6af3286083e05084ea5bddf78160d8e7a4ef9b7220f26` |
| `apmcmthesis.cfg` | `5977897c04bcdcf0e34dbd7958ddbf636cd9d2413f2250a126e8b0bbd5fc882a` |
| `ControlSheet.tex` | `4ee85a304372f31f2b1a1effbcedcc0ce4ba57100069190c75655c81d104d89c` |

After extraction the four official TeX source files were made read-only. The repository previously tracked a later D-question Control Sheet starter under the official directory; it was not byte-identical to the ZIP. It was replaced by the ZIP original, and the prior version remains recoverable from Git history.

## Compiler and commands

- pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026)
- Latexmk 4.89

```bash
latexmk -pdf -interaction=nonstopmode -file-line-error -halt-on-error -outdir=build main.tex
latexmk -pdf -interaction=nonstopmode -file-line-error -halt-on-error -outdir=build ControlSheet.tex
```

## Original-source results

| Test | Result | Evidence |
|---|---|---|
| Original `main.tex` with PDFLaTeX | FAIL at sample resource | Class/config and all packages load; compilation stops at line 116 because image `cat` is absent from the ZIP. `gongzhonghao` is also absent. |
| Original `ControlSheet.tex` with PDFLaTeX | PASS | Generated a one-page A4 PDF with no fatal error. |
| Official class/config with L1 paper | PASS | Generated the modular nine-page PDF with no fatal error. |

The original `main.tex` failure is a missing demonstration-asset issue, not a class/config, font, engine, or macro-package incompatibility. The authorization permits class/config acceptance with an isolated working copy, so L1 proceeded without editing the official sources.

## Format and visual acceptance

| Requirement | Result |
|---|---|
| A4 page size | PASS; 595.276 × 841.890 pt for every checked page |
| Summary Sheet | PASS; physical page 1 |
| Contents | PASS; begins on physical page 2 and spans two pages for the nine-section L1 outline |
| Body start | PASS; follows the contents and restarts at page 1 |
| Main header | PASS; official team-number and `Page n of N` mechanism retained |
| Official font configuration | PASS; PDFLaTeX loads unmodified `newtxtext/newtxmath`; embedded TeX Gyre Termes/NewTX fonts verified |
| Mathematics | PASS; official score and QUBO equations render correctly |
| English and symbols | PASS by render and text extraction |
| Figure/table mechanism | PASS; labeled table and explicit L1 figure placeholder render |
| Reference mechanism | PASS; BibTeX produces a numbered citation and reference |
| Control Sheet | PASS as an independently compiled official source |
| Fatal errors | None in Control Sheet or L1 paper |

Visual inspection covered Summary Sheet, both contents pages, and the first body page. The official class emits a `headheight` warning and the deliberately long team-number placeholder wraps on the Summary Sheet; neither changes layout rules or blocks L1. The placeholder must be replaced with the verified team number before release.

## Working-copy changes

No compatibility repair was required in `paper/apmcmthesis.cls` or `paper/apmcmthesis.cfg`; both remain byte-identical to the originals. Only `paper/main.tex` and new modular content differ. The reasons and before/after excerpts are recorded in `template_working_copy_diff.md`.

## Final conclusion

The official `apmcmthesis` class/config are accepted under the organizer-recommended PDFLaTeX path. The L1 manuscript preserves the official page size, typography branch, Summary Sheet, contents, page styles, formula, figure/table, and reference mechanisms. L1 may proceed; the generated PDF is a structural manuscript, not a competition-ready release.
