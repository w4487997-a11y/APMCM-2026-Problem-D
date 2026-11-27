# Ghosh & Chowdhury (2024): ABN3 nitride-perovskite band-gap prediction

**Citation:** Ghosh, S., & Chowdhury, J. (2024). Predicting band gaps of ABN3 perovskites: an account from machine learning and first-principle DFT studies. RSC Advances, 14, 6385–6397. https://doi.org/10.1039/D4RA00402G

**Reading status:** FULLTEXT-REVIEWED (publisher HTML sections on methods, data preparation, features and results reviewed); supplementary information still to be reviewed.

## Study design and results
The paper studies nitride perovskites ABN3. It initially identifies 5,566 candidates, applies formation-energy screening, and focuses on 1,563 compounds with band gaps around 1.0–3.1 eV. It starts from 117 features drawn from a 145-feature descriptor family, reduces to 10 features after correlation-based filtering, and compares SVR, MLP, GBDT and random forest. Its reported random-forest test results are MAE 0.03 eV, RMSE 0.11 eV and R² 0.94. It also performs DFT studies on CeMoN3 and CeWN3.

## Relation to Q1
This paper is relevant as a perovskite-family descriptor and band-gap modeling example. However, ABN3 is a nitride-specific chemistry and is not a direct match to the competition's anion candidate space. The study predicts band gap, whereas Q1 predicts the competition-defined five-penalty aggregate V using only site categories. It should support background/method comparison, not a direct benchmark.

## Four-dimensional comparison
- Prior methods: descriptor-based regression using SVR, MLP, GBDT and random forest, with feature reduction.
- Theoretical basis: electronegativity, d-valence electron count, covalent radius and related descriptors encode chemical/electronic influences on band gap.
- Problem-specific adaptation: this project follows the competition's ordered A/B/X representation, label formula and pair-grouped split; the ABN3 work uses a nitride-specific dataset and random train/test partitioning.
- Empirical contribution: the article reports its own band-gap results and DFT follow-up. These results cannot be compared numerically with Q1's V-MAE.

## Cautions
The publisher article body was reviewed; supplementary details and complete reproducibility have not yet been independently checked. Do not transfer its reported metrics to the competition model.

## Sources
Publisher full text: https://pubs.rsc.org/en/content/articlehtml/2024/ra/d4ra00402g
DOI: https://doi.org/10.1039/D4RA00402G
