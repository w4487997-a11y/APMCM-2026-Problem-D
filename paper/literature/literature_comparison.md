# Literature Comparison Matrix — Q1 v1

This is an initial evidence-bounded comparison. It must be updated after full-text review of remaining candidates.

| Dimension | Ward et al. 2016 | Chen et al. 2024 | Ghosh & Chowdhury 2024 | Kusuma et al. (2025 publication) | Competition Q1 v1 |
|---|---|---|---|---|---|
| Material scope | Broad inorganic materials | ABX3 and double perovskites | ABN3 nitride perovskites | ABX3 and double perovskites | Competition-defined ABX3 candidate space |
| Input representation | 145 composition-derived attributes | Nearly 300 Matminer descriptors (publisher abstract) | 117 initial, 10 selected descriptors | Composition features indicated; details pending | Ordered A/B/X site categories; categorical encoding |
| Targets | Multiple inorganic-material properties | Perovskite band-gap/property prediction | Band gap | Multiple material properties | Five-term competition violation score V |
| Models | Multiple ML algorithms; material-family partitioning | Six ML models; XGBoost best in abstract | SVR, MLP, GBDT, RF | SVM, RF, XGB, NN indicated | Frozen HistGradientBoosting hgb_gap_mix with property heads, positive-gap classifier and penalty mixture |
| Validation | Cross-validation and material grouping | Full protocol pending full text | Random train/test split reported | Full protocol pending | Ordered (A,B)-grouped folds on 02; official 03 validation |
| Theoretical role | Composition descriptors and property-dependent attribute relevance | Descriptor-rich ABX3 prediction | Electronic/chemical descriptors for nitride band gaps | Multi-property screening and feature selection | Competition-specific V formula and composition-only site representation |

## Interpretation
1. Ward is a foundational representation reference, not a direct reproduction of Q1.
2. Chen is the strongest currently identified 2024 direct ABX3 ML candidate, but its descriptor set and target differ from Q1.
3. Ghosh is ABX3-family adjacent evidence but specifically concerns ABN3 nitride perovskites; its feature and random-split design differ.
4. Kusuma is a useful multi-property comparator; publisher publication date is 2025 despite DOI year 2024. Full text is still needed.
5. No paper's reported MAE/RMSE should be numerically ranked against Q1's V-MAE unless targets, units, data distributions and split protocols are comparable.

## Q1 evidence anchor
- Actual model implementation: q1/surrogates.py
- V formula: q1/violation.py
- Frozen Q1 report: experiments/q1_ablation_v1/REPORT.md
- Supplementary evidence: experiments/q1_v12/REPORT.md
- Model-selection chronology: experiments/q1_v12/model_selection.md
