# Official Template to Working Copy Diff

## File-level result

| Official source | Working copy | Result |
|---|---|---|
| `official_template/apmcmthesis.cls` | `paper/apmcmthesis.cls` | Byte-identical; SHA-256 `22bb5c34ee56760d2cd6af3286083e05084ea5bddf78160d8e7a4ef9b7220f26` |
| `official_template/apmcmthesis.cfg` | `paper/apmcmthesis.cfg` | Byte-identical; SHA-256 `5977897c04bcdcf0e34dbd7958ddbf636cd9d2413f2250a126e8b0bbd5fc882a` |
| `official_template/main.tex` | `paper/template_original/main.tex` | Byte-identical snapshot |
| `official_template/main.tex` | `paper/main.tex` | Intentionally modularized as described below |

## Main-file changes

The working `main.tex` preserves these official statements and ordering:

```diff
 \documentclass{apmcmthesis}
-\tihao{A}
-\baominghao{apmcm263XXXXX}
+\tihao{D}
+\baominghao{TEAM-NUMBER-PLACEHOLDER}
 \begin{document}
 \pagestyle{frontmatterstyle}
 \begin{abstract}
-[official demonstration text]
+[evidence-bounded L1 structural summary]
 \end{abstract}
 \newpage
 \tableofcontents
 \newpage
 \pagestyle{mainmatterstyle}
 \setcounter{page}{1}
```

The long official demonstration body was replaced by modular chapter calls:

```diff
-[generic sample sections, missing sample images, legacy Chinese caption,
- sample bibliography, and demonstration MATLAB listing]
+\input{sections/01_introduction}
+\input{sections/02_problem_formulation}
+\input{sections/03_data_and_audit}
+\input{sections/04_q1_surrogate}
+\input{sections/05_q2_qubo}
+\input{sections/06_q3_qubo}
+\input{sections/07_hardware_and_precision}
+\input{sections/08_results_and_discussion}
+\input{sections/09_conclusion}
+\bibliographystyle{plain}
+\bibliography{references}
+\input{appendix/appendix}
```

## Reasons and impact

1. Problem A and the demonstration team number were replaced with Problem D and an explicit unknown-team placeholder.
2. The official sample references `cat` and `gongzhonghao`, but those assets are absent from the ZIP. The sample-only block was not copied into the paper; no official source was edited.
3. Generic sample prose and sample citations were removed so they cannot be mistaken for project evidence.
4. The nine required chapter files, verified bibliography entry, and appendix inventory were added.
5. Page size, margins, line spacing, font branch, Summary Sheet, contents mechanism, headers, page numbering, captions, tables, and class behavior remain controlled by the unmodified official class/config.

No font replacement, class patch, config patch, geometry change, or official-file rename was made.
