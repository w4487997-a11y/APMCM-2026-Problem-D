# Q1 v1 Academic Positioning (evidence-bounded)

## Actual implementation
The repository's q1/surrogates.py defines composition-only site inputs using ordered A, B and X categories. For HistGradientBoosting, an OrdinalEncoder is fitted on training data and the three sites are passed as categorical features. The frozen configuration is hgb_gap_mix. It predicts non-gap physical-property penalty components and combines a positive-gap probability with the positive-gap conditional penalty and the zero-gap penalty. q1/violation.py implements the five squared-hinge penalties and a separate strict-feasibility predicate.

The project does not currently use the 145 Ward/Magpie attributes or the nearly 300 Matminer descriptors described in some literature. The A:X and B:X interaction features and A=B indicator appear in a separate Ridge ablation design, not the frozen model's primary input. This distinction must remain explicit.

## Evidence-backed contribution candidates
Subject to final independent team review:
1. A competition-specific surrogate target: the official five-term violation score V, rather than a single property such as band gap or formation energy.
2. A site-aware composition-only model using ordered A/B/X categories under the competition's data contract.
3. A probability-weighted mixture for zero-gap and positive-gap branches, reflecting the high zero-gap prevalence and nonlinear penalty structure.
4. Evaluation focused on grouped ordered-(A,B) validation and screening/ranking metrics in addition to global regression error.
5. Reproducible separation between frozen model selection and post-freeze supplementary comparisons.

These are task-specific modeling/validation contributions, not claims of a new general-purpose descriptor theory or new gradient-boosting algorithm.

## Empirical support and limits
The repository report records Q1 v1 hgb_gap_mix on validation file 03: MAE 2.4715, RMSE 4.5827, Spearman 0.9383, Top-25 overlap 8/25, Top-50 overlap 20/50, and V<5 subset MAE 8.2654. The report also records limitations in the low-V tail and positive-gap classification recall. The model-selection record must be read alongside the supplementary report to preserve freeze chronology.

Pool 04 contains hidden labels. Predictions may be reported as generated/delivered if repository evidence supports it, but actual 04 accuracy, hit rate, or error must not be reported without authorized labels.

## What must not be claimed
- Do not claim Q1 uses Magpie's 145 descriptors or Matminer’s nearly 300 features.
- Do not claim the project introduced HistGradientBoosting as an algorithm.
- Do not call the 2024/2016 studies direct performance baselines without matched data, target and split.
- Do not describe a post-freeze model as the frozen winner.
- Do not claim hidden-pool accuracy or identify the 19 hidden V=0 samples.
- Do not claim causal physical discovery from categorical inputs alone.

## Manuscript placement
- Introduction / Related Work: materials informatics, ABX3 ML, composition-based descriptors.
- Methodology: exact ordered-site representation, V formula, gap-mixture construction.
- Experiments: internal matched baselines, ablations and grouped validation; external literature is contextual unless a fair common benchmark is possible.
- Discussion: benefits and limitations of compact site-category representation versus richer elemental descriptors.
