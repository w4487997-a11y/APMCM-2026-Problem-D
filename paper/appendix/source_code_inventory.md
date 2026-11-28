# Source Code Inventory

Status: V2 reproducibility index, updated 2026-11-28. Historical artifacts are
retained in place; this table identifies the entry points used by the paper.

| Area | Entry point / output | Version, seed or scope | Status and boundary |
|---|---|---|---|
| Data and labels | `audit/phase1/`, `q1/violation.py` | Official hashes and grouped folds; fold seed 42 | Complete machine audit; human sign-off pending. |
| Q1 training and delivery | `q1/experiments.py`, `q1/v12_supplement.py`, `q1/v12_handoff.py`; outputs `experiments/q1_ablation_v1/`, `experiments/q1_v12/`, `handoff/v1_2/` | HGB seeds 42/1729/31415; grouped splits recorded in artifacts | Frozen Q1 result complete; file 03 budget replay is retrospective. |
| Budget baseline | `experiments/q1_random_search_03/REPORT.md`, `comparison.csv` | Exact hypergeometric calculation; no Monte Carlo seed | Complete for file 03 only. |
| QUBO/Ising controls | `handoff/q23_fix/scripts/stage1_sdk_ising.py`, `stage2_quant_partition.py`, `stage7_entry.py` | Kaiwu 1.4.4 mapping audit; SDK 1.4.3 CPU solve; 30 seeds × at most 10 reads | Two-level 104-variable construction is oracle-assisted; 208-variable result is a floating control. |
| Negative/regression tests | `handoff/q23_fix/scripts/stage8_negative_validation.py`, `stage9_regression.py` | 13 negative classes and R1--R4 | Archived checks passed within stated scope. |
| O-10 projection | `handoff/q23_supplement/scripts/o10_projection.py`; outputs `O10/` | 107 variables, 8,112 candidates, 300 local-SA samples | Adverse control; changes the low-tail argmin. |
| O-11 precision | `o11_metrics.py`, `o11_mcc_merge.py`; outputs `O11/` | 18 $K\times\lambda$ cases | 0/300 versus 8/300 conflict remains UNVERIFIED. |
| O-13 SPQC | `o13_prepare.py`, `decode_platform.py`, `o13_manifest.py`; outputs `O13/` | Four final 104-variable tasks; matrix SHAs listed below | Limited task returns; seven ledger debits, six receipts. |
| O-14 blind pools | `o14_blind.py`; outputs `O14/` | Four float + four integer matrices; seeds 30, samples 10, iterations 300, $\alpha=0.99$ | Local SA only; README timing provenance unresolved. |
| O-15 cost/error | `o15_audit.py`; outputs `O15/error_attribution.csv`, `timings.csv`, `resource_cost.csv` | Four error layers kept separate | Timing conflicts and complete platform cost remain UNVERIFIED/NA. |
| Paper build | `paper/scripts/build.sh`, `paper/scripts/check_pdf.py` | PDFLaTeX/Latexmk; output `paper/build/main.pdf` | Official class/config remain unchanged. |

Final SPQC matrix SHA-256 values are: Q2/NO2 and Q3/NO2
`fee2320be71979ba3dad4283ed917d957758e0b3f9966141c33a51d2c81bee5c`,
Q3/O3 `26d234efa34c11cde626801c353b6491aeaab07247a07140873566970a8a82ef`,
and Q3/FO2 `5b49510e78219db65b1a9eab7240f34222cc6a7b253f37ac95226f65c6fb7309`.
The floating Q2 control QUBO SHA is
`967b13d1957b40dd720de006f26ece2900b2dbaefd8bde793936e635bad6d95a`;
the joint 208-variable Q3 control SHA is
`f3b447a1edb675da67cf76ebe09cb8bc4f4c5c908052faa248752f4cfe1b7b32`.
Full O-14 float/integer matrix hashes are in
`handoff/q23_supplement/O14/results/o14_results.json`.

Do not package credentials, private account data, raw organizer datasets, or
unreviewed build artifacts.
