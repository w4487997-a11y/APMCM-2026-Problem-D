# Manon et al. (2026): SHAP-guided ABX3 band-gap prediction and inverse design

**Citation:** Aldrin Manon, Rajiv Kumar Gill, Vijay Kumar, Kapil Joshi, Arvind Dhaka, and Amita Nandal. “SHAP-guided Machine Learning for Interpretable Band Gap Prediction and Inverse Design in ABX3 Perovskites.” *International Journal of Computational Intelligence Systems* (2026). DOI: https://doi.org/10.1007/s44196-026-01454-1

**Reading status:** VERIFIED-METADATA; ABSTRACT AND APPENDIX FEATURE-CATEGORY SUMMARY REVIEWED. Open-access full-text detailed review remains pending.

## Publisher-reported method
The paper reports a gradient-boosted-tree framework with SHAP-guided feature engineering. Its 68 features are grouped as 28 elemental descriptors, 8 structural descriptors, 12 physics-inspired descriptors and 20 engineered/SHAP-guided interaction features. It reports band-gap MAE of 0.2644 eV, inverse-design screening for candidates in a 1.5–2.5 eV interval, and quantile-regression/conformal-prediction mechanisms for identifying out-of-domain predictions.

## Relevance and limitations
This is a recent ABX3 gradient-boosting and screening comparator, particularly useful for discussing the contrast between richer physical/structural descriptors and the project's compact site-category input. It predicts band gap, not the competition V objective. Its reported MAE cannot be compared directly with Q1 V-MAE.

## Four-dimensional comparison
- **Prior methods:** gradient-boosted trees, SHAP, engineered descriptor interactions, uncertainty-aware screening.
- **Theoretical basis:** elemental and structural features encode chemistry and geometry relevant to band-gap behavior.
- **Problem-specific adaptation:** project Q1 uses ordered A/B/X categorical identities and a penalty-mixture objective; the article uses 68 richer descriptors for direct band-gap prediction.
- **Empirical contribution:** an open-access recent ABX3 study with uncertainty-aware inverse design; full-text details need further review.

## Sources
- Springer Nature article: https://link.springer.com/article/10.1007/s44196-026-01454-1
- DOI: https://doi.org/10.1007/s44196-026-01454-1
