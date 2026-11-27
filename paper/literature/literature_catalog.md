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
