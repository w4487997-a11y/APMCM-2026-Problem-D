# Liu et al. (2022): experimental ABX3 band-gap prediction

**Citation:** Yiming Liu, Wensheng Yan, Heng Zhu, Yiteng Tu, Li Guan, and Xinyu Tan. “Study on bandgap predications of ABX3-type perovskites by machine learning.” *Organic Electronics* 101 (2022), 106426. DOI: https://doi.org/10.1016/j.orgel.2021.106426

**Reading status:** VERIFIED-METADATA; ABSTRACT AND PUBLISHER SECTION PREVIEW REVIEWED. Full text/supplementary information still requires complete review.

## Study design
The authors assemble 227 experimental perovskite band-gap records from 1,254 publications, compare 24 machine-learning approaches, and report a final set of four models. The available publisher preview describes a 204/23 train/test split. The abstract reports RMSE as low as 0.55 and Pearson correlation up to 0.99, and uses SHAP to analyze compositional effects.

## Relevance and limitations
This is important because the labels are experimental band gaps rather than exclusively DFT outputs. However, the sample size is small relative to the source literature count, and the test set contains only 23 samples in the previewed split. Its target is experimental band gap, not the competition's aggregate V. Before making claims about generalization, the full paper's data extraction, duplicate handling, split construction and uncertainty reporting should be inspected.

## Four-dimensional comparison
- **Prior methods:** comparison of many ML learners on literature-collected experimental data.
- **Theoretical basis:** composition-dependent electronic properties, interpreted using SHAP.
- **Problem-specific adaptation:** Q1 v1 predicts V using A/B/X categories and a two-branch gap-penalty expectation; Liu et al. predict band gap itself.
- **Empirical contribution:** a literature-curated experimental ABX3 band-gap dataset and a small held-out test evaluation.

## Sources
- Publisher record: https://www.sciencedirect.com/science/article/pii/S1566119921003591
- DOI: https://doi.org/10.1016/j.orgel.2021.106426
