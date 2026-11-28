# Final Submission Acceptance Report

Date: 2026-11-29  
Branch: `codex/p0-paper-revisions`  
Team number used in the manuscript and file names: `apmcm26312030`

## Manuscript build

- Engine: pdfTeX 1.40.29 (TeX Live 2026), invoked through `latexmk -pdf`.
- Command: `latexmk -pdf -interaction=nonstopmode -file-line-error -halt-on-error -outdir=build main.tex`.
- Result: 34 A4 physical pages; 3 front matter, 24 body, 1 reference, and 6 appendix pages.
- The conclusion ends on numbered page 24, one page below the 25-page main-body maximum.
- No fatal error, undefined citation or cross-reference, or Overfull box remains.
- The official-class `fancyhdr` head-height warning, font substitutions up to 0.5 pt, and Underfull boxes in narrow appendix cells remain. Rendered inspection found no clipping, overlap, or lost content.

Final PDF:

- Path: `submission/final/Dapmcm26312030.pdf`
- SHA-256: `0eb9d87e75774a3451643ce0ea633d2c94ff8ad2eacf96954eb50208c3ec0630`

## Template integrity

- `paper/apmcmthesis.cls` and `official_template/apmcmthesis.cls` share SHA-256 `22bb5c34ee56760d2cd6af3286083e05084ea5bddf78160d8e7a4ef9b7220f26`.
- `paper/apmcmthesis.cfg` and `official_template/apmcmthesis.cfg` share SHA-256 `5977897c04bcdcf0e34dbd7958ddbf636cd9d2413f2250a126e8b0bbd5fc882a`.
- Git reports no change to the official template class, configuration, `main.tex`, or `ControlSheet.tex` originals.

## AI tool disclosure

The supplied official Word template was copied and filled without changing its seven-table structure. The completed four-page document records a qualitative 70% team / 30% AI contribution split; it describes ChatGPT and Codex assistance in method discussion, partial code writing/debugging, evidence analysis, LaTeX engineering, and English polishing. It also states that the team led the research questions, model route, experiments, verification, interpretation, and final conclusions. Representative prompts are explicitly identified as record-based summaries rather than verbatim historical transcripts.

- Path: `submission/final/AI工具使用详情说明_apmcm26312030.docx`
- SHA-256: `02dce6ada1e3e85605cd76dce5e6bc070a20961fe00cf8ba158874482cea6b77`
- Source-template SHA-256: `00cb1a33c52bbb03487fa495477464fed55100de1b953e7fc857257e7b70ba67`
- Historical model versions and exact interaction times are marked pending because the available project records do not establish them.
- The team must perform the template's final authenticity confirmation before submission.

## Control Sheet and package status

No signed Control Sheet could be verified in the accessible workspace. The candidate `/Users/ile/Desktop/APMCM2026/2026 APMCM Control Sheet.docx` was rendered and found to contain blank signature/name fields. It was therefore not modified, renamed, or placed in `submission/final/` as a signed document.

The final directory currently contains the verified manuscript PDF and the completed AI-use disclosure. Platform submission is **not fully ready** until the team supplies the genuinely signed Control Sheet and confirms the pending AI-disclosure metadata and authenticity statement.
