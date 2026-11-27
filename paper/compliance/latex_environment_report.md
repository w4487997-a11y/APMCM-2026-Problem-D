# LaTeX Environment Report

**Date:** 2026-11-27 (Asia/Shanghai)  
**Repository branch:** `codex/latex-environment-audit` (local only)  
**Stage A result:** PASS for the official PDFLaTeX route

## Host

| Item | Result |
|---|---|
| Operating system | macOS 27.0.1, Darwin 27.0.0 |
| CPU | Apple M5 Pro, `arm64` |
| LaTeX distribution | TinyTeX / TeX Live 2026, user-scoped at `/Users/ile/Library/TinyTeX` |
| Installation size | 794 MiB after `collection-latexextra` and `collection-fontsrecommended` |
| `pdflatex` | pdfTeX 3.141592653-2.6-1.40.29 |
| `xelatex` | XeTeX 0.999998 |
| `latexmk` | 4.89 |
| `tectonic` | 0.17.0 at `/Users/ile/.local/bin/tectonic` |

The TinyTeX binary directory and the user Tectonic directory were added to `/Users/ile/.zprofile`. No administrator privilege was used.

## Diagnostic and repair record

The initial machine had no TeX Live/MacTeX command-line distribution. Tectonic was installed first and proved that system Times New Roman is present and readable from a normal terminal process, but the official sample exposed two separate source-package issues: missing sample images and a legacy XeTeX-incompatible `\CJK` command. These were not treated as font failures.

TinyTeX was then installed at user scope because the user authorized environment repair and the official `main.tex` recommends PDFLaTeX first. The official TinyTeX archive had SHA-256 `c65e092eecab5638cb1e17be1533230ff52dd733c5132b723c07ca4d5c654474`. The installed standard collections supply the official template dependencies, including `newtx`, `CJK`, `titlesec`, `titletoc`, `lastpage`, `multirow`, `cprotect`, `listings`, `caption`, `enumitem`, `ulem`, `appendix`, and `fancyhdr`.

Representative diagnostics:

```bash
uname -a
uname -m
command -v pdflatex xelatex latexmk tectonic
pdflatex --version
xelatex --version
latexmk --version
system_profiler SPFontsDataType
```

macOS did not provide `fc-match` or `fc-list`; native font inspection was used instead. Times New Roman is installed under `/System/Library/Fonts/Supplemental/`. The PDFLaTeX branch does not request that system font: the unmodified official class deliberately loads `newtxtext` and `newtxmath`, producing embedded TeX Gyre Termes/NewTX fonts. This is the official PDFLaTeX font configuration, not an unauthorized substitution.

## Compilation acceptance

Primary command:

```bash
latexmk -pdf -interaction=nonstopmode -file-line-error -halt-on-error -outdir=build main.tex
```

Results:

- Official `ControlSheet.tex`: PASS, one-page A4 PDF, no fatal error.
- Official sample `main.tex`: reaches the sample figure at line 116, then fails because `cat` (and subsequently `gongzhonghao`) is absent from the organizer ZIP.
- L1 working manuscript using byte-identical official class/config: PASS, nine-page A4 PDF, bibliography and cross-references resolved, no fatal error.
- Mathematics, English characters, symbols, table, figure/caption mechanism, numbered references, Summary Sheet, contents, and body headers: PASS.

The sample-resource omission is recorded in `official_template_acceptance.md`; it does not require or justify editing the official class/config.

## Integrity and safety

The source archive hash is `8afaef1208964095f5bae06e2a47d294fe3affd979d6b05ade4c91973f0aee7c`. Official source hashes are recorded in `template_manifest.json`. No official TeX source was edited after extraction. No research result, raw data, Git remote, release, or competition platform was modified.
