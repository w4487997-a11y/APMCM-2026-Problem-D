# Chen et al. (2024): machine learning for perovskite properties

**Citation:** Chen, Z., Wang, J., Li, C., Liu, B., Luo, D., Min, Y., Fu, N., & Xue, Q. (2024). Highly versatile and accurate machine learning methods for predicting perovskite properties. Journal of Materials Chemistry C, 12, 15444–15453. https://doi.org/10.1039/D4TC02268H

**Reading status:** VERIFIED-METADATA; ABSTRACT AND OFFICIAL 11-PAGE ESI REVIEWED. Main article full-text review remains pending.

## Publisher-reported scope
The publisher abstract reports 3,720 ABX3 perovskites and 2,660 A2B(I)B(II)X6 double perovskites; nearly 300 Matminer-generated descriptors; six ML models including XGBoost; and best reported XGBoost performance of R²=0.873 and RMSE=0.5868 eV for the study's band-gap task. The article also reports SHAP analysis of influential descriptors.

## Relevance to Q1
This is a high-priority direct ABX3 materials-ML comparator because it concerns perovskite property prediction and includes ABX3 data. Its descriptor-rich representation differs from competition Q1 v1, which currently uses ordered A/B/X site categories. Its target is band gap/property prediction, not the competition's five-term violation score V. Comparison must be methodological and task-aware, not a raw metric ranking.

## Required full-text follow-up
Identify exact predicted properties and whether the reported dataset mixes ABX3 and double perovskites in every experiment; extract descriptor definitions and feature-selection protocol; verify data splitting and leakage controls; inspect hyperparameters, performance tables, SHAP interpretation, limitations and supplementary information.

## Four-dimensional comparison (preliminary)
- Prior methods: Matminer composition/material descriptors with several supervised ML algorithms.
- Theoretical basis: composition and elemental-property descriptors encode chemical information related to electronic properties.
- Problem adaptation: this project predicts aggregate competition-defined V from A/B/X categories and evaluates ordered-pair grouped splits; Chen's task/data protocol is distinct.
- Empirical contribution: publisher abstract reports its own dataset and metrics; those results do not validate this project's model.

## Sources
Publisher record: https://pubs.rsc.org/en/content/articlelanding/2024/tc/d4tc02268h/unauth
DOI: https://doi.org/10.1039/D4TC02268H


## Official supplementary information review (11-page PDF)
The RSC publisher page links the official 11-page ESI PDF. The ESI separates ABX3 and A2B(I)B(II)X6 results, which prevents the overall abstract metric from being misreported as the ABX3-only score.

- For ABX3 band-gap prediction, Table S4 reports XGBoost R2=0.7995 and RMSE=0.7419 eV; the double-perovskite XGBoost result is R2=0.8688 and RMSE=0.5742 eV.
- For ABX3 formation-energy prediction, Table S2 reports XGBoost R2=0.9336 and RMSE=0.2546 (units as defined in the article).
- Table S8 reports standard deviations across 100 band-gap training sessions; the XGBoost values are 0.0567 for R2 and 0.1284 for RMSE under Strategy 1, and 0.0518 / 0.1166 under Strategy 2.
- Table S1 identifies selected descriptors including Magpie statistics, transition-metal fraction, unfilled d/f electron counts, electronegativity difference and unit-cell volume.
- The ESI lists model-specific hyperparameters and feature-engineering feature counts.

**Interpretation:** the abstract's R2=0.873 / RMSE=0.5868 eV is the high-level reported result and must not be substituted for the ABX3-only XGBoost values in Table S4. The study uses descriptor-rich inputs and its own split/data protocol; no direct metric ranking against Q1 V is valid.

**Official ESI:** https://www.rsc.org/suppdata/d4/tc/d4tc02268h/d4tc02268h1.pdf
**Publisher landing page:** https://pubs.rsc.org/en/content/articlelanding/2024/tc/d4tc02268h/unauth
