# Doucet et al. (2026): thermodynamic significance of QUBO encoding

**Citation:** Emery Doucet, Zakaria Mzaouali, Reece Robertson, Bartłomiej Gardas, Sebastian Deffner, and Krzysztof Domino. “Thermodynamic significance of QUBO encoding on quantum annealers.” *New Journal of Physics* 28 (2026), 054512. DOI: https://doi.org/10.1088/1367-2630/ae6e98

**Reading status:** OPEN-ACCESS PUBLISHER FULL-TEXT PREVIEW REVIEWED (abstract, introduction, methods outline, experimental results and conclusion sections reviewed).

## Study question
The paper studies how different penalty choices for the same constrained task alter the energy landscape, solver success and thermodynamic behavior of a quantum annealer.

## Method and findings
Using a Job Shop Scheduling instance, the authors vary two penalty weights: one-hot/sum constraints and precedence constraints. They compare classical annealing-inspired solvers and D-Wave Advantage experiments. The reported results show regime changes: penalties that are too weak leave low-energy infeasible states, while penalties that are too strong suppress the effective objective energy scale and can reduce solution quality and thermodynamic efficiency.

## Relevance to D-01
This directly contextualizes the project's observed conflict between one-hot penalty strength and material-objective coefficients. D-01 reports that the one-hot local-field contribution grows with group size, while the material interactions become difficult to preserve under int8 scaling. The paper supports treating penalty tuning as a balance between feasibility and objective resolution, rather than simply increasing lambda.

## Four-dimensional comparison
- **Prior methods:** QUBO encodings with tunable one-hot and pairwise penalty weights.
- **Theoretical basis:** penalty terms reshape the spectrum and energy landscape seen by finite-temperature, noisy hardware.
- **Problem-specific adaptation:** project Q2/Q3 must tune/derive penalties for the actual material objective, group sizes and Kaiwu precision constraints.
- **Empirical contribution:** experimental mapping between penalty regimes, solver success and thermodynamic quantities on a 10-qubit Job Shop instance.

## Limitations
The studied problem and D-Wave hardware differ from APMCM D and Kaiwu SPQC. It is not a numerical parameter recommendation for lambda in Q2/Q3. Its value is conceptual and methodological: penalty sweeps must be paired with feasibility, objective regret and coefficient-range audits.

## Sources
- IOP publisher page: https://doi.org/10.1088/1367-2630/ae6e98
- DOI: https://doi.org/10.1088/1367-2630/ae6e98
