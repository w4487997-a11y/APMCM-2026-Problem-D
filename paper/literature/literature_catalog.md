# Literature Catalog — Q1

Last checked: 2026-11-27. This is an initial verified catalog, not a claim that every candidate has been read in full.

## Core methodological reference

### Ward et al. (2016) — VERIFIED-METADATA; FULLTEXT-REVIEWED
Logan Ward, Ankit Agrawal, Alok Choudhary, Christopher Wolverton. “A general-purpose machine learning framework for predicting properties of inorganic materials.” npj Computational Materials 2, 16028 (2016). DOI: https://doi.org/10.1038/npjcompumats.2016.28. Publisher full text: https://www.nature.com/articles/npjcompumats201628

Relevance: foundational composition-derived materials attributes, elemental-property statistics, and materials-aware partitioning. The article describes 145 attributes across stoichiometric, elemental-property statistical, electronic-structure, and ionic-compound categories. It is background for descriptor design, not evidence that this project uses those 145 attributes.

## ABX3/perovskite candidates

### Chen et al. (2024) — VERIFIED-METADATA; ABSTRACT-REVIEWED
Ziming Chen, Jing Wang, Canjie Li, Baiquan Liu, Dongxiang Luo, Yonggang Min, Nianqing Fu, Qifan Xue. “Highly versatile and accurate machine learning methods for predicting perovskite properties.” Journal of Materials Chemistry C 12 (2024), 15444–15453. DOI: https://doi.org/10.1039/D4TC02268H. Publisher: https://pubs.rsc.org/en/content/articlelanding/2024/tc/d4tc02268h/unauth

Publisher abstract reports 3,720 ABX3 and 2,660 double-perovskite compounds, nearly 300 Matminer descriptors, six ML models, and best reported XGBoost performance of R²=0.873 / RMSE=0.5868 eV for the study's band-gap task. Strong 2024 ABX3 candidate. Full article and supplementary information still require detailed reading.

### Ghosh & Chowdhury (2024) — VERIFIED-METADATA; FULLTEXT-REVIEWED
Swarup Ghosh and Joydeep Chowdhury. “Predicting band gaps of ABN3 perovskites: an account from machine learning and first-principle DFT studies.” RSC Advances 14 (2024), 6385–6397. DOI: https://doi.org/10.1039/D4RA00402G. Publisher full text: https://pubs.rsc.org/en/content/articlehtml/2024/ra/d4ra00402g

The paper studies 1,563 nitride perovskites, starts from a 145-descriptor family, selects 10 features, and compares SVR, MLP, GBDT and random forest. It is relevant to ABX3-family band-gap prediction and descriptors, but its X=N chemistry is not automatically equivalent to the competition's X-site candidate domain. Treat it as adjacent-domain evidence, not a direct benchmark.

### Kusuma et al. — VERIFIED-DOI; publication year 2025, not 2024
Frendy Jaya Kusuma, Eri Widianto, Wahyono, Iman Santoso, Sholihun, Moh. Adhib Ulil Absor, Setyawan Purnomo Sakti, Kuwat Triyana. “Multi-Properties prediction of perovskite materials using Machine learning and Meta-Heuristic feature selection.” Solar Energy (published 15 January 2025), article 113189. DOI: https://doi.org/10.1016/j.solener.2024.113189.

The DOI contains 2024, but the publisher record gives publication date 15 January 2025. Cite as 2025 if using publisher publication date. Search summary indicates ABX3 and double perovskites, composition-only features, SVM/RF/XGB/NN and metaheuristic feature selection. Full text review required.

## Search expansion required
Continue searching for work directly related to formation-energy and band-edge prediction, rare-target/low-tail regression, categorical site representations, grouped validation, gradient boosting and classifier-regressor mixtures. Add papers only when they support a specific Q1 method or claim.


---

## Extended Q1 materials-ML literature

### Gladkikh et al. (2020) — VERIFIED-METADATA; ABSTRACT/SI PREVIEW
Vladislav Gladkikh, Dong Yeon Kim, Amir Hajibabaei, Atanu Jana, Chang Woo Myung, Kwang S. Kim. “Machine Learning for Predicting the Band Gaps of ABX3 Perovskites from Elemental Properties.” *J. Phys. Chem. C* 124(16) (2020), 8905–8918. DOI: 10.1021/acs.jpcc.9b11768. Small-data nonlinear elemental-property mapping; ACE and alternative regressors. Direct ABX3 context, but non-zero band-gap target and elemental descriptors differ from Q1 V.

### Liu et al. (2022) — VERIFIED-METADATA; ABSTRACT/PUBLISHER PREVIEW
Yiming Liu, Wensheng Yan, Heng Zhu, Yiteng Tu, Li Guan, Xinyu Tan. “Study on bandgap predications of ABX3-type perovskites by machine learning.” *Organic Electronics* 101 (2022), 106426. DOI: 10.1016/j.orgel.2021.106426. Reports 227 experimental band-gap records collected from 1,254 publications, 204/23 split in publisher preview, and RMSE as low as 0.55. Small test sample and target mismatch must be discussed.

### Obada et al. (2023) — FULLTEXT-REVIEWED
David O. Obada et al. “Explainable machine learning for predicting the band gaps of ABX3 perovskites.” *Materials Science in Semiconductor Processing* 161 (2023), 107427. DOI: 10.1016/j.mssp.2023.107427. Uses 199 HSE06-derived ABX3 samples, 12 elemental features, six learners and SHAP; discusses zero/non-zero gap entries. It is not the same two-head penalty-mixture model as Q1.

### Chenebuah et al. (2021) — PUBLISHER PREVIEW/REPOSITORY REVIEWED
Ericsson Tetteh Chenebuah, Michel Nganbe, Alain Beaudelaire Tchagang. “Comparative analysis of machine learning approaches on the prediction of the electronic properties of perovskites: A case study of ABX3 and A2BB’X6.” *Materials Today Communications* 27 (2021), 102462. DOI: 10.1016/j.mtcomm.2021.102462. Reports 1,453 samples (829 ABX3, 624 double perovskites), 57 descriptors and 12 learners. Authors' code/data repository: https://github.com/chenebuah/perovskite-ML.

### Chenebuah & Chenebuah (2023) — PREPRINT
“An inorganic ABX3 perovskite materials dataset for target property prediction and classification using machine learning.” arXiv:2312.11335. DOI: 10.48550/arXiv.2312.11335. Describes 16,323 ABX3 structures and 61 generalized features. This is a preprint/data resource, not a direct benchmark. Never join it against competition blind pools or infer hidden labels.

### Fang et al. (2023) — ABSTRACT-REVIEWED
Xu Fang et al. “A2BB’X6/ABX3-type high-performance perovskites screening based on ensemble learning and high throughput screening.” *Solar Energy* 262 (2023), 111795. DOI: 10.1016/j.solener.2023.111795. Multi-property ensemble screening of formation energy, energy above hull and band gap; full-text details and units remain to be checked.

### Deng et al. (2025) — FULLTEXT-REVIEWED
Ziliang Deng et al. “Prediction of ABX3 Perovskite Formation Energy Using Machine Learning.” *Materials* 18(13) (2025), 2927. DOI: 10.3390/ma18132927. Reports descriptor filtering and XGBoost formation-energy prediction; 4:1 random split, so not directly comparable with grouped Q1 validation.

### Solecki & Zhu (2026) — ABSTRACT/HIGHLIGHTS-REVIEWED; HIGH PRIORITY FULL TEXT
“Evaluation of machine-learned band gaps: Two-stage modeling and the effects of data representation and split strategy.” *Computational Materials Science* (2026), 115106. DOI: 10.1016/j.commatsci.2026.115106. Six zero-heavy public band-gap datasets; highlights non-zero MAE and random-vs-grouped split differences. This is particularly relevant to Q1's zero/positive-gap branch, but the full article is still required before detailed claims.

### Manon et al. (2026) — ABSTRACT/APPENDIX SUMMARY REVIEWED
“SHAP-guided Machine Learning for Interpretable Band Gap Prediction and Inverse Design in ABX3 Perovskites.” *International Journal of Computational Intelligence Systems* (2026). DOI: 10.1007/s44196-026-01454-1. Reports 68 elemental/structural/physics-inspired/interaction features, gradient-boosted trees, SHAP and uncertainty-aware screening. Open access; full-text detailed review remains pending.

## Reproducibility and optimization foundations

### Persaud, Ward & Hattrick-Simpers (2024) — OPEN-ACCESS FULL-TEXT PREVIEW REVIEWED
“Reproducibility in materials informatics: lessons from ‘A general-purpose machine learning framework for predicting properties of inorganic materials’.” *Digital Discovery* 3 (2024), 281–286. DOI: 10.1039/D3DD00199G. Important for evidence traceability and the limitations of reproducing older materials-ML releases.

### Lucas (2014) — OPEN-ACCESS REVIEW
“Ising formulations of many NP problems.” *Frontiers in Physics* 2 (2014), 5. DOI: 10.3389/fphy.2014.00005. Foundational constraint-to-penalty and Ising/QUBO mapping reference.

### Glover, Kochenberger & Du (2019) — QUBO TUTORIAL
“Quantum Bridge Analytics I: a tutorial on formulating and using QUBO models.” *4OR* 17 (2019), 335–371. DOI: 10.1007/s10288-019-00424-y.

Full individual notes are in individual_papers/; Q2/Q3 theory summary is q2_q3_qubo_foundations.md.
