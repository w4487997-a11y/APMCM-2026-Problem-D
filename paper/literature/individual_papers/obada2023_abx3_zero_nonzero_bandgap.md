# Obada et al. (2023): explainable ML for ABX3 band gaps

**Citation:** David O. Obada, Emmanuel Okafor, Simeon A. Abolade, Aniekan M. Ukpong, David Dodoo-Arhin, and Akinlolu Akande. “Explainable machine learning for predicting the band gaps of ABX3 perovskites.” *Materials Science in Semiconductor Processing* 161 (2023), 107427. DOI: https://doi.org/10.1016/j.mssp.2023.107427

**Reading status:** FULLTEXT-REVIEWED (open university repository PDF; main methods, data, results and tables reviewed).

## Study scope and data
The paper models ABX3 perovskite band gaps and explicitly discusses a dataset containing zero and non-zero band-gap entries. The reported modeling dataset consists of 199 perovskite compounds whose band gaps were calculated using the HSE06 functional in the cited source dataset. The paper also discusses direct and indirect band-gap prediction.

## Representation and models
Each A, B and X element is represented by four element-specific descriptors: electronegativity, covalent radius, first ionization energy and periodic-table row, giving 12 inputs per composition. The compared learners include Decision Tree, Random Forest, CatBoost, XGBoost, LightGBM and CompoundNet (a neural network). The paper uses SHAP for model interpretation and reports B-site Pauling electronegativity as an important predictor.

## Validation and results
The paper reports experiments using 95:5 and 80:20 train/test partitions. Its abstract reports CatBoost and XGBoost as strong approaches with test R2 at or above 0.88. The tables report separate direct- and indirect-gap metrics. These are small-data, within-dataset random-split results and should not be treated as directly comparable to the competition's pair-grouped validation.

## Four-dimensional comparison
- **Prior methods:** ensemble tree models and a neural network for DFT-derived ABX3 band-gap prediction.
- **Theoretical basis:** elemental electronegativity, radius, ionization energy and periodic-table position are used as chemically interpretable predictors.
- **Problem-specific adaptation:** this project predicts the competition's five-term violation score V from ordered A/B/X categories, not direct/indirect band gap alone; it has a distinct zero-gap penalty mixture.
- **Empirical contribution:** the paper demonstrates explainable prediction on a 199-compound HSE06 dataset. It does not validate the competition V target or the current model's grouped split.

## Important distinction
Although the article discusses zero and non-zero band gaps, it must not be cited as evidence that it uses the same classifier-plus-positive-gap-conditional-penalty mixture as Q1 v1. Similarity of data phenomenon is not identity of model architecture.

## Sources
- Publisher record: https://www.sciencedirect.com/science/article/pii/S1369800123001208
- Open full-text copy: https://ugspace.ug.edu.gh/server/api/core/bitstreams/aef71f1e-9a2b-45fb-b017-d1f1d7ce714e/content
- DOI: https://doi.org/10.1016/j.mssp.2023.107427
