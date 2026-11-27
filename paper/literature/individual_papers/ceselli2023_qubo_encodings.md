# Ceselli & Premoli (2023): good encodings for quantum annealer and digital solvers

**Citation:** Alberto Ceselli and Marco Premoli. “On good encodings for quantum annealer and digital optimization solvers.” *Scientific Reports* 13, 5628 (2023). DOI: https://doi.org/10.1038/s41598-023-32232-0

**Reading status:** FULLTEXT-REVIEWED (open-access publisher article; encoding, constraint, experiment and conclusion sections reviewed).

## Study design
The paper compares different QUBO encodings of the cardinality-constrained quadratic knapsack problem, including alternative constraint penalties and variable encodings. It benchmarks D-Wave Advantage quantum annealing, digital probabilistic solvers and mathematical programming.

## Key methodological points
- Constrained optimization must be transformed into unconstrained QUBO through penalty terms; penalty multipliers affect solution quality.
- Variable encoding and penalty formulation are modeling decisions, not neutral implementation details.
- A QUBO solution is not guaranteed to satisfy the original constraints; feasibility must be checked after each solve and may require repair/post-processing.
- Interaction-graph structure and hardware connectivity affect embedding cost; dense formulations can require substantial chain overhead.
- The paper compares linear and quadratic penalty formulations for an inequality-constrained problem and finds that the linear form can improve the tested solver performance.

## Relevance to Q2/Q3
This supports the project's need to compare encodings rather than assume the initial one-hot penalty formulation is optimal. It also supports explicit feasibility checks, post-solve decoding, and comparison with classical solvers. However, its test problem is a cardinality-constrained quadratic knapsack, not the project's material-pair/triple selection task.

## Four-dimensional comparison
- **Prior methods:** alternative binary encodings and penalty formulations for constrained combinatorial optimization.
- **Theoretical basis:** constraint relaxation into penalty terms and graph-embedding requirements.
- **Problem-specific adaptation:** the project uses one-hot A/B or (A,X)/B selection groups; alternatives must preserve the exact legal candidate set and objective.
- **Empirical contribution:** experimental comparison across quantum hardware and digital solvers for a specific constrained knapsack benchmark.

## Limitations
The hardware results are D-Wave-specific. Do not infer that the same embedding overhead, linear penalty formulation or solver performance applies to Kaiwu SPQC. A different encoding is acceptable only after exact equivalence, constraint preservation and original-objective regret are independently demonstrated.

## Sources
- Publisher full text: https://www.nature.com/articles/s41598-023-32232-0
- PubMed: https://pubmed.ncbi.nlm.nih.gov/37024525/
- DOI: https://doi.org/10.1038/s41598-023-32232-0
