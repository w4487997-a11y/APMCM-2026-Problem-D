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


---

## Extended comparison: ABX3 property prediction and Q1 v1

| Study | Representation | Target | Validation / scale | Key relevance | Non-equivalence to Q1 |
|---|---|---|---|---|---|
| Gladkikh et al. 2020 | Element-specific properties; ACE and ML | Non-zero ABX3 band gap | Small-data study | Nonlinear chemistry-to-gap mapping | Not V; no zero-gap penalty mixture |
| Liu et al. 2022 | Composition-related predictors | Experimental band gap | 227 records; publisher preview 204/23 split | Experimental labels and literature curation | Small test set; not V |
| Obada et al. 2023 | 12 elemental features; CatBoost/XGB/etc.; SHAP | Direct/indirect gap | 199 HSE06 samples; 95:5 and 80:20 splits | ABX3, zero/non-zero gap context, explainability | Does not implement Q1's expected gap-penalty mixture |
| Chenebuah et al. 2021 | 57 descriptors; 12 learners | Formation energy and band gap | 1,453 ABX3/double-perovskite samples; 90:10 split | Multi-property perovskite ML and public code | Random split and richer features; not V |
| Chenebuah & Chenebuah 2023 | 61 generalized features | Formation energy, gap, crystal class | 16,323 ABX3 preprint dataset | Dataset/benchmark context | Preprint; not same feature contract or V |
| Fang et al. 2023 | Ensemble feature pipeline | Formation energy, Ehull, gap | Full protocol pending | Multi-property screening | Abstract-level only; no V target |
| Deng et al. 2025 | 168→30→9 descriptors; XGBoost | Formation energy | 2,703 preprocessed; 4:1 split | Feature screening and FPC check | Not V; random split |
| Solecki & Zhu 2026 | Representation and two-stage comparisons | Band gap with many zero values | Six datasets; 1,306–106,113 | Most direct context for zero-heavy target and split strategy | Abstract-level; full method must be read |
| Manon et al. 2026 | 68 elemental/structural/physics/interaction features | ABX3 band gap | Open-access recent study | Gradient boosting, SHAP, uncertainty and inverse design | Not V; richer descriptors |

### Synthesis for the manuscript
1. Existing ABX3 literature already uses elemental descriptors, tree ensembles, XGBoost/CatBoost, SHAP, and multi-property screening. These are established methods, not innovations of this project.
2. Q1's distinctive task formulation is the official five-term violation score V and its use as a common candidate-ranking objective.
3. Q1 v1's input is compact ordered A/B/X categorical composition; do not state it uses Magpie/Matminer descriptors.
4. The zero-gap branch is a task-specific modeling choice. The 2026 two-stage study makes full-text follow-up especially important before claiming novelty.
5. Grouped (A,B) validation is an important project-specific design. Compare it with random splits in literature as different generalization questions, not as a claim that all random-split studies are invalid.
6. External performance metrics are not directly comparable where targets, units, datasets, label sources or split protocols differ.

## Q2/Q3 foundational theory comparison

| Source | Main theoretical contribution | Use in this project | Caution |
|---|---|---|---|
| Lucas 2014 | Ising encodings, penalty Hamiltonians, auxiliary variables and penalty-dominance logic | Explain binary constraints and one-hot penalty terms | Need derive the actual bound for the project's objective and coefficient range |
| Glover et al. 2019 | QUBO formulation tutorial and combinatorial optimization mappings | Define QUBO notation, objective/constraint formulation | Does not prove quantum advantage or solver success |

## Reproducibility comparison
Persaud et al. (2024) documents the importance of dependency/version logs, complete scripts, and links between paper claims and executable artifacts. This directly supports the project's evidence-index and experiment-freeze requirements.
