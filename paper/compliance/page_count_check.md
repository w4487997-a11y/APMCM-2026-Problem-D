# Page Count Check

Final draft check on 2026-11-28 using `pdfinfo` and the PDFLaTeX build log:

- Physical PDF: 29 A4 pages.
- Summary Sheet: 1 page (physical page 1).
- Contents: 2 pages (physical pages 2--3).
- Main body and references: 24 numbered pages (physical pages 4--27).
- Appendix: 2 numbered pages, A.1--A.2 (physical pages 28--29; body page counter 25--26).
- Main-body maximum: **PASS**; the body and references end on numbered page 24, within the 25-page limit.

The appendix begins after the references and is reported separately rather
than counted as main-body prose.  No font-size, margin, or official class
change was used to meet the limit.
