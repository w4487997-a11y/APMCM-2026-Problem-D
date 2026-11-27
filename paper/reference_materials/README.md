# APMCM D Paper Reference Materials

This directory contains source-grounded reference notes for the four materials supplied by the team on 2026-11-27.

## Files

### Past D-problem papers
- `sample_papers/2022_D题优秀论文_结构分析.md` — structure, model derivation, parameter comparison, two-method optimization comparison, recommendation letter, evaluation and limitations.
- `sample_papers/2024_D题优秀论文_结构分析.md` — multi-problem paper structure and the sequence from classical model to binary encoding, QUBO, solver, decoding and testing.

### Paper quality and language review
- `review_prompts/AI痕迹检测提示词_V5.0_执行要点.md` — 10-dimension language and style diagnostic, with explicit limits on AI-detection claims.
- `review_prompts/APMCM论文16维度自查_V1.3_执行要点.md` — 16-dimension competition-paper review checklist mapped to seven stated judging principles, with official-rule verification requirements.

## Source-file handling

The original uploads were:
1. `2022年D题优秀论文.pdf`
2. `2024年D题优秀论文.pdf`
3. `AI痕迹检测！2026APMCM亚太杯AI痕迹检测提示词.docx`
4. `AI论文检查！2026APMCM亚太杯论文全维度自查与获奖预测提示词.docx`

The two PDF papers are represented here by analytical notes rather than full-text reproductions. The two DOCX prompts are represented by structured implementation notes rather than byte-identical DOCX files. The notes preserve the relevant structure, checks and source-specific cautions needed by the writing workflow. Original PDF page references are retained in the sample-paper notes.

## How Chat 1 / Codex must use these materials

1. Read this README before drafting.
2. Read both sample-paper analyses before deciding the final paper structure.
3. Use the 2022 sample for question-by-question exposition, physical/mathematical derivation, parameter interpretation, comparison and practical recommendations—not for its topic-specific equations or results.
4. Use the 2024 sample for explaining variable encoding, QUBO construction, penalty terms, solver setup, decoding, stability and limitations—not for unsupported claims of quantum advantage or any copied results.
5. Use the 10-dimension AI trace document only as an editorial diagnostic. Do not attempt to evade AI detectors, add artificial human-like errors, or report unsupported AI-generation probabilities.
6. Use the 16-dimension checklist after the draft is substantive. Verify every purported official requirement against current official APMCM materials in the repository.
7. Do not copy text, formulas, tables, figures or results from either sample paper. Learn only from their organization and reasoning techniques.
8. The 2026 paper must present the actual Q1→Q2→Q3 research pipeline, not three unrelated application stories.
