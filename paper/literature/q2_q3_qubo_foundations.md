# Q2/Q3 QUBO Foundations — Literature and Repository Boundary

This note records foundational sources for binary quadratic optimization and constraint-to-penalty encodings. It is not yet a final literature review of the project's completed Q2/Q3 implementation.

## 1. Core sources

### Lucas (2014)
Andrew Lucas, “Ising formulations of many NP problems,” *Frontiers in Physics* 2 (2014), article 5. DOI: https://doi.org/10.3389/fphy.2014.00005

Open-access review covering mappings of NP-hard/NP-complete problems to Ising Hamiltonians. It shows how equality and inequality constraints can be represented by penalty Hamiltonians, discusses auxiliary binary variables for inequalities, and emphasizes choosing penalty coefficients so that violating a constraint cannot become energetically preferable to improving the objective. This is the primary theoretical source for explaining why one-hot constraints are squared and converted into quadratic penalties.

### Glover, Kochenberger & Du (2019)
Fred Glover, Gary Kochenberger, and Yu Du, “Quantum Bridge Analytics I: a tutorial on formulating and using QUBO models,” *4OR* 17 (2019), 335–371. DOI: https://doi.org/10.1007/s10288-019-00424-y

A tutorial/survey on QUBO as a unified model for combinatorial optimization and quantum/hybrid optimization. Use it to define the QUBO form, variable conventions, and the modeling workflow. It is a general optimization reference, not proof that a particular hardware backend provides a quantum speedup.

## 2. Repository evidence inspected

The current main branch contains an earlier D-00 pre-feasibility implementation:
- deliverable/code/build_matrices.py
- deliverable/code/verify_qubo.py
- deliverable/results/matrix_build.json
- deliverable/results/qubo_verify.json
- deliverable/README.md

That code documents:
- binary variables and one-hot penalty terms with lambda=2;
- Q2: 104 variables and 2,704 candidate pairs;
- Q3: 208 variables and 8,112 candidate triples;
- a matrix convention H(x)=x^T Q x + constant with an upper-triangular Q;
- min-max cost scaling to [0,1];
- exact energy-versus-cost checks for every candidate in the recorded pool;
- toy exhaustive checks over 16 Q2 and 256 Q3 states.

The D-00 README also states that Kaiwu SDK, quantization and hardware tests had not yet been completed at that stage. These artifacts are a historical/pre-feasibility evidence layer. Before writing the final Q2/Q3 method, the manuscript writer must inspect the later handoff/V1.2_Q2Q3_交付包.zip, final code, final matrices, solver logs and acceptance reports. Do not present the D-00 Ridge baseline or its matrices as the final Q2/Q3 solver unless the later handoff confirms that they are still the adopted implementation.

## 3. Four-dimensional comparison framework for Q2/Q3

- **Prior methods:** QUBO/Ising formulations and penalty-based constraint encoding.
- **Theoretical foundations:** binary decision variables, quadratic objective, one-hot constraints, penalty dominance, and energy-minimization interpretation.
- **Problem-specific adaptation:** the project encodes A/B or A/B/X candidate choices, combines candidate costs with one-hot constraints, and later connects the QUBO to the actual Kaiwu solving workflow. Exact final mapping must be sourced from the latest accepted code.
- **Empirical contribution:** report only verified matrix equivalence, feasible-solution checks, solver output, energy, constraint satisfaction, quantization and hardware precision audits from the final handoff.

## 4. Writing cautions

1. Do not claim quantum advantage merely because a QUBO or Ising representation is used.
2. Distinguish mathematical QUBO correctness from solver optimality and from hardware execution.
3. State the penalty coefficient rationale and show that feasible minima are preserved; do not rely on an arbitrary lambda without a bound or empirical verification.
4. State the exact binary-variable order and Q-matrix convention to avoid factor-of-two errors in off-diagonal terms.
5. If the final solver is classical simulated annealing or hybrid, name it accurately; do not call it quantum annealing unless the execution logs show that backend.
6. Separate exact enumeration on toy instances from full-scale optimization results.
