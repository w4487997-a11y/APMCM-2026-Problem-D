# Ohno & Togawa (2026): precision errors and coefficient reduction after embedding

**Citation:** Kentaro Ohno and Nozomu Togawa. “Mitigating Precision Errors in Quantum Annealing via Coefficient Reduction of Embedded Hamiltonians.” *IEEE Transactions on Quantum Engineering* 7 (2026), 1–22. DOI: https://doi.org/10.1109/TQE.2026.3678999

**Reading status:** VERIFIED-METADATA; PUBLISHER ABSTRACT AND TECHNICAL SECTION EXCERPTS REVIEWED. Full article review remains pending.

## Study question
The paper studies the effect of finite coefficient precision on quantum-annealing solution quality, emphasizing that the relevant dynamic range is that of the minor-embedded Hamiltonian, not only the logical Ising model.

## Methods summarized by the publisher
It evaluates three coefficient-reduction approaches (IEM, BCE and ALM) and measures the effects after minor embedding. The workflow includes embedding, scaling-factor evaluation, and a search over chain strength using hardware samples. The publisher reports that IEM improved sample quality on tested instances, while BCE and ALM had limited or instance-dependent effects.

## Relevance to D-01
D-01 found that the project's large one-hot penalties can dominate local fields and that direct int8 scaling destroys many material-interaction coefficients. This paper supports the general principle that coefficient reduction must be assessed after all hardware transformations. It also highlights that a method that improves the logical Hamiltonian may fail or behave differently after embedding and chain-strength selection.

## Transfer boundary
The paper's hardware experiments use D-Wave Advantage and minor embedding. The project's Kaiwu SPQC platform has its own SDK and precision pipeline. Do not assume D-Wave chain strength, embedding graph or IEM/BCE/ALM APIs exist in Kaiwu. Use this paper to formulate hypotheses and audits, not to claim a ready-made solution.

## Required follow-up
Read the full article before choosing a coefficient-reduction method. Extract exact IEM/BCE/ALM definitions, chain-strength optimization protocol, hardware topology assumptions and coefficient range. Then test only compatible variants on the project's real Q2/Q3 matrices.

## Sources
- IEEE publisher record: https://ieeexplore.ieee.org/document/11025222
- DOI: https://doi.org/10.1109/TQE.2026.3678999
- arXiv: https://arxiv.org/abs/2604.03546
