# Deng et al. (2025): ABX3 formation-energy prediction with feature screening

**Citation:** Ziliang Deng, Kailing Fang, Chong Guo, Zhichao Gong, Haojie Yue, Huacheng Zhang, Kang Li, Kun Guo, Zhiyong Liu, Bing Xie, Jinshan Lu, Kui Yao, and Francis Eng Hock Tay. “Prediction of ABX3 Perovskite Formation Energy Using Machine Learning.” *Materials* 18(13) (2025), 2927. DOI: https://doi.org/10.3390/ma18132927

**Reading status:** FULLTEXT-REVIEWED (publisher HTML text and supplementary-material description reviewed).

## Study design
The authors start with 4,358 ABX3 compounds, preprocess to 2,703, generate 168 features, filter highly correlated features (Pearson correlation threshold 0.8), and compare six learners using a 4:1 train/test split. The selected XGBoost model is further reduced to nine features. The paper reports an improvement from R2=0.928/RMSE=0.301 eV per atom to R2=0.939/RMSE=0.278 eV per atom after feature reduction. It also compares predictions with first-principles calculations for selected generated compounds.

## Relevance and caution
This is a useful formation-energy and feature-selection comparator. It illustrates a feature-engineering workflow and the importance of verifying ML predictions against first-principles calculations. However, its feature set is substantially richer than the competition Q1 v1, its target is formation energy rather than V, and its 4:1 random split is not the project's grouped ordered-(A,B) validation. It must not be used as a direct numerical baseline.

## Four-dimensional comparison
- **Prior methods:** LR, SVR, MLP, decision tree, RF and XGBoost; correlation filtering and SHAP feature selection.
- **Theoretical basis:** composition/element descriptors and formation energy as a stability-related property.
- **Problem-specific adaptation:** project Q1 combines multiple official threshold penalties into V and uses A/B/X categories; Deng et al. predict E_form directly from a rich descriptor set.
- **Empirical contribution:** reported feature reduction and first-principles spot verification on their own material dataset.

## Sources
- Publisher full text: https://www.mdpi.com/1996-1944/18/13/2927
- PubMed/PMC record: https://pubmed.ncbi.nlm.nih.gov/40649415/
- DOI: https://doi.org/10.3390/ma18132927
