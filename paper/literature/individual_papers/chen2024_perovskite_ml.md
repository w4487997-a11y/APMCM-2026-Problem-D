# Chen et al. (2024): machine learning for perovskite properties

**Citation:** Chen, Z., Wang, J., Li, C., Liu, B., Luo, D., Min, Y., Fu, N., & Xue, Q. (2024). Highly versatile and accurate machine learning methods for predicting perovskite properties. Journal of Materials Chemistry C, 12, 15444–15453. https://doi.org/10.1039/D4TC02268H

**Reading status:** VERIFIED-METADATA; ABSTRACT-REVIEWED. Full article and supplementary information are still required for full review.

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
