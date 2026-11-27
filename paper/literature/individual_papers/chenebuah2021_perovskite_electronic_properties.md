# Chenebuah, Nganbe & Tchagang (2021): comparative ML for perovskite electronic properties

**Citation:** Ericsson Tetteh Chenebuah, Michel Nganbe, and Alain Beaudelaire Tchagang. “Comparative analysis of machine learning approaches on the prediction of the electronic properties of perovskites: A case study of ABX3 and A2BB’X6.” *Materials Today Communications* 27 (2021), 102462. DOI: https://doi.org/10.1016/j.mtcomm.2021.102462

**Reading status:** VERIFIED-METADATA; PUBLISHER ARTICLE PREVIEW AND AUTHORS' REPRODUCTION REPOSITORY REVIEWED.

## Study scope
The study compares machine-learning methods for formation energy and band-gap prediction across ABX3 and double-perovskite structures. The article reports 1,453 samples: 829 ABX3 and 624 A2BB'X6. It develops 57 generalized input descriptors from elemental, stability and crystallographic information, and also examines adding energy above hull. Twelve ML models are compared. The paper reports a 90:10 initial train/test split and investigates sample-size effects.

## Reported findings
The abstract reports SVR as strongest for formation energy (MAE 0.055 eV/atom; RMSE 0.096 eV/atom; R2 about 99%) and notes Gradient Boosting Regression and Random Forest Regression as better suited to band-gap prediction than SVR in the sample-size study. These metrics are specific to the paper's datasets, feature definitions and split protocol.

## Relevance to Q1
This is a strong methodological comparator for multi-property perovskite prediction and model-family selection. However, the project's frozen Q1 v1 uses ordered A/B/X categorical site inputs and predicts the competition-defined V score. It does not use the paper's 57 descriptors or energy-above-hull input. The paper's random 90:10 split is not equivalent to the project's ordered-(A,B)-grouped folds.

## Four-dimensional comparison
- **Prior methods:** broad comparison of 12 regression algorithms and generalized descriptors.
- **Theoretical basis:** elemental, stability and structural descriptors as proxies for electronic/material properties.
- **Problem-specific adaptation:** project Q1 maps the official five penalty terms into V and evaluates low-V screening under grouped A/B validation.
- **Empirical contribution:** comparative results across two perovskite structure families, with open code/data claimed by the authors.

## Reproducibility resources
The authors' repository is public and contains scripts/data:
https://github.com/chenebuah/perovskite-ML

Do not merge its external data into competition training data or use it to infer hidden labels. It is a literature reproduction resource only.

## Sources
- Publisher article: https://www.sciencedirect.com/science/article/pii/S2352492821004542
- Authors' repository: https://github.com/chenebuah/perovskite-ML
- DOI: https://doi.org/10.1016/j.mtcomm.2021.102462
