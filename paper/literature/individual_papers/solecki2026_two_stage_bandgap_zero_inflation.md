# Solecki & Zhu (2026): two-stage band-gap modeling and split strategy

**Citation:** Evan Solecki and Peifen Zhu. “Evaluation of machine-learned band gaps: Two-stage modeling and the effects of data representation and split strategy.” *Computational Materials Science* (2026), article 115106. DOI: https://doi.org/10.1016/j.commatsci.2026.115106

**Reading status:** VERIFIED-METADATA; PUBLISHER ABSTRACT/HIGHLIGHTS REVIEWED. Full article is behind publisher access in the inspected source; full-text review remains a priority.

## Publisher-reported scope
The study examines six public band-gap datasets containing 1,306 to 106,113 materials, with experimental, computed or surrogate band gaps. The publisher highlights that:
- many zero-gap entries can make aggregate accuracy misleading;
- non-zero MAE exposes regression error hidden by aggregate metrics;
- descriptor enrichment explains much of the apparent gain from two-stage modeling;
- random and grouped splits answer different questions, with grouped splits testing held-out-chemistry extrapolation.

## Why this is especially relevant
This is the closest identified methodological comparator to Q1's zero/positive-gap branch and grouped validation design. It does **not** prove that the project's penalty-mixture method is novel. Instead, it reinforces the need to isolate the contribution of the mixture architecture from representation changes, report non-zero/low-tail metrics separately, and preserve grouped-split evidence.

## Four-dimensional comparison
- **Prior methods:** single-stage versus two-stage band-gap prediction across several public datasets.
- **Theoretical basis:** zero-inflated/zero-heavy target distributions and chemistry-dependent data similarity affect both error summaries and generalization.
- **Problem-specific adaptation:** Q1 v1 estimates the probability of positive gap and mixes zero-gap penalty with conditional positive-gap penalty inside the official V objective; the paper's exact target and two-stage architecture must be checked in the full text before claiming equivalence.
- **Empirical contribution:** cross-dataset analysis of representation and split strategy, with an explicit warning against interpreting aggregate metrics alone.

## Required follow-up
Obtain the full paper; extract exact definitions of the two-stage model, datasets, descriptor ablations, grouped split units, statistical tests and non-zero MAE. Compare those design choices with Q1's frozen architecture without retroactively changing Q1's model-selection history.

## Sources
- Publisher page: https://www.sciencedirect.com/science/article/pii/S0927025626006257
- DOI: https://doi.org/10.1016/j.commatsci.2026.115106
