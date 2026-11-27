# Mücke, Gerlach & Piatkowski (2025): optimum-preserving QUBO parameter compression

**Citation:** Sascha Mücke, Thore Gerlach, and Nico Piatkowski. “Optimum-preserving QUBO parameter compression.” *Quantum Machine Intelligence* 7, article 1 (2025; first published 17 December 2024). DOI: https://doi.org/10.1007/s42484-024-00219-3

**Reading status:** FULLTEXT-REVIEWED (open-access publisher article; theory, bounds, experiments and conclusion reviewed).

## Research problem
The paper studies how finite parameter precision and hardware noise distort QUBO coefficients and can change the set of minimizing bit vectors. It formalizes optimum inclusion/preservation and defines dynamic range from the largest and smallest non-zero differences among matrix coefficients.

## Method
The authors derive bounds on parameter modifications that preserve an optimum, then use these bounds to alter QUBO coefficients while reducing dynamic range. They develop greedy parameter-update strategies and test them on random QUBO instances, BinClustering and SubsetSum. The paper distinguishes simple scaling/rounding from optimum-preserving coefficient changes: scaling alone does not reduce dynamic range, and aggressive rounding can change the argmin.

## Results and relevance
The article reports that lower dynamic range improves robustness to finite precision. In its D-Wave experiments, compression improved the probability of observing the optimum on the studied BinClustering and SubsetSum instances. This is directly relevant to the project's D-01 finding that direct int8 quantization destroyed Q2/Q3 candidate ranking and even admitted lower-energy infeasible states.

## Four-dimensional comparison
- **Prior methods:** QUBO coefficient scaling, rounding and precision adaptation.
- **Theoretical basis:** optimum inclusion, energy-gap bounds and dynamic-range minimization.
- **Problem-specific adaptation:** the project must test whether the paper's bounds/updates can be applied to the exact Kaiwu/SPQC coefficient and penalty model, preserving both legal minima and constraint feasibility.
- **Empirical contribution:** formal optimum-preservation bounds and hardware experiments on other QUBO problem classes.

## Critical limitations for transfer
1. The paper's experimental hardware is D-Wave, not the project's Kaiwu SPQC backend.
2. Its methods do not automatically preserve the project's one-hot constraints unless those constraints are part of the proven full QUBO argmin set and the required bounds are satisfied.
3. It is not evidence that the project's current 104/208-variable matrices can be compressed successfully.
4. Any adapted method must be independently tested on all legal candidates, illegal-state energy bounds, quantized matrices and original objective regret.

## Sources
- Open-access full text: https://link.springer.com/article/10.1007/s42484-024-00219-3
- DOI: https://doi.org/10.1007/s42484-024-00219-3
