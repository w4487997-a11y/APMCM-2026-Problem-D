# Fang et al. (2023): ensemble-learning high-throughput perovskite screening

**Citation:** Xu Fang, Zhengxin Chen, Qian Ma, Jiang Wu, Jia Lin, Jiawei Li, Wenhao Li, Chaofan Liu, Hongtao Shen, and Linhong You. “A2BB’X6/ABX3-type high-performance perovskites screening based on ensemble learning and high throughput screening.” *Solar Energy* 262 (2023), 111795. DOI: https://doi.org/10.1016/j.solener.2023.111795

**Reading status:** VERIFIED-METADATA; PUBLISHER ABSTRACT REVIEWED. Full text not yet available in the inspected sources.

## Publisher-reported scope
The abstract describes an ensemble-learning workflow involving data cleaning, feature engineering, model training and evaluation. It predicts formation energy, energy above hull and band gap for ABX3/double-perovskite systems. The abstract reports MAE values of 0.146 eV, 0.041 eV and 0.396 eV for these three properties, respectively; units and target-specific details must be checked in the full paper before quoting them in the manuscript.

## Relevance
This paper connects multi-property prediction to high-throughput candidate screening. It is useful as context for the broader D problem, where multiple property constraints are combined to rank candidate materials. It does not predict the competition's five-term V score and does not establish the correctness of our Q1/Q2/Q3 pipeline.

## Four-dimensional comparison
- **Prior methods:** ensemble learning and high-throughput screening.
- **Theoretical basis:** multiple predicted physical properties can be used as screening criteria.
- **Problem-specific adaptation:** this project combines official threshold deviations into V and then passes predicted candidate costs into discrete Q2/Q3 optimization.
- **Empirical contribution:** abstract-level evidence of multi-property ensemble prediction and candidate screening.

## Follow-up
Obtain the full text and inspect dataset provenance, descriptor definitions, train/test split, model ensembles, property units, screening criteria and any external validation.

## Sources
- Publisher record: https://www.sciencedirect.com/science/article/abs/pii/S0038092X23004127
- DOI: https://doi.org/10.1016/j.solener.2023.111795
