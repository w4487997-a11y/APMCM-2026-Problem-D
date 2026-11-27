# Literature Status Matrix — APMCM D

Last updated: 2026-11-27. This matrix is the single quick-reference index for the literature notes. Status describes what was actually inspected, not the amount of work still required.

| Key paper | Topic | Reading status | Main note |
|---|---|---|---|
| Ward et al. (2016) | Magpie/material descriptors; chemistry-aware partitioning; screening | Publisher full text reviewed; SI package not fully audited | individual_papers/ward2016_magpie_framework.md |
| Chen et al. (2024) | ABX3/double-perovskite multi-property ML | Metadata, abstract and official 11-page ESI reviewed; main article full-text review pending | individual_papers/chen2024_perovskite_ml.md |
| Ghosh & Chowdhury (2024) | ABN3 band gap; descriptor selection; DFT | Publisher full-text sections reviewed; SI pending | individual_papers/ghosh2024_abn3_bandgap.md |
| Kusuma et al. (2025 publication) | Multi-property perovskite prediction | DOI and publisher record/summary reviewed; full text pending | individual_papers/kusuma_2025_mult_properties.md |
| Gladkikh et al. (2020) | ABX3 band gap from elemental properties; ACE | Metadata, abstract and SI preview reviewed | individual_papers/gladkikh2020_abx3_bandgap_elemental_properties.md |
| Liu et al. (2022) | Experimental ABX3 band gaps | Metadata, abstract and publisher preview reviewed | individual_papers/liu2022_experimental_abx3_bandgap.md |
| Obada et al. (2023) | ABX3 zero/non-zero gaps; ensemble ML; SHAP | Open full-text body and key tables reviewed | individual_papers/obada2023_abx3_zero_nonzero_bandgap.md |
| Chenebuah et al. (2021) | ABX3/double perovskites; formation energy and gap | Publisher preview and authors' repository reviewed | individual_papers/chenebuah2021_perovskite_electronic_properties.md |
| Chenebuah & Chenebuah (2023) | ABX3 dataset and ML benchmark | Preprint metadata/abstract and repository README reviewed | individual_papers/chenebuah2023_abx3_dataset_preprint.md |
| Fang et al. (2023) | Multi-property ensemble high-throughput screening | Publisher abstract reviewed; full text pending | individual_papers/fang2023_perovskite_ensemble_screening.md |
| Deng et al. (2025) | ABX3 formation energy; feature screening | Publisher full-text body reviewed | individual_papers/deng2025_abx3_formation_energy.md |
| Solecki & Zhu (2026) | Zero-heavy band gaps; two-stage model; grouped split | Publisher abstract/highlights reviewed; full text high priority | individual_papers/solecki2026_two_stage_bandgap_zero_inflation.md |
| Manon et al. (2026) | ABX3 band gap; SHAP; inverse design; uncertainty | Metadata, abstract and feature appendix summary reviewed; full-text detailed review pending | individual_papers/manon2026_shap_abx3_inverse_design.md |
| Persaud et al. (2024) | Materials informatics reproducibility | Publisher full-text preview reviewed | individual_papers/persaud2024_materials_informatics_reproducibility.md |
| Lucas (2014) | Ising/QUBO mappings and penalty constraints | Open-access full text reviewed in QUBO foundations note | q2_q3_qubo_foundations.md |
| Glover et al. (2019) | QUBO formulation tutorial | Bibliographic record and abstract reviewed in QUBO foundations note | q2_q3_qubo_foundations.md |
| Ceselli & Premoli (2023) | Alternative QUBO encodings; feasibility and solvers | Open-access full text reviewed | individual_papers/ceselli2023_qubo_encodings.md |
| Mücke et al. (2025) | Optimum-preserving coefficient compression | Open-access full text reviewed | individual_papers/muecke2025_optimum_preserving_qubo_compression.md |
| Ohno & Togawa (2026) | Coefficient reduction after embedding; precision | Metadata, abstract and technical excerpts reviewed; full text pending | individual_papers/ohno2026_quantum_annealing_precision.md |
| Doucet et al. (2026) | QUBO penalty regimes and thermodynamic effects | Open-access publisher full-text sections reviewed | individual_papers/doucet2026_qubo_penalty_thermodynamics.md |

## Full-text priorities
1. Solecki & Zhu (2026): obtain full text and extract exact two-stage architecture, datasets, split units and non-zero MAE.
2. Chen et al. (2024): review main article in detail; official ESI has already been reviewed.
3. Manon et al. (2026): full-text review of descriptors, uncertainty quantification and inverse-design validation.
4. Ohno & Togawa (2026): full-text review of coefficient reduction methods and post-embedding precision.
5. Liu (2022), Gladkikh (2020), Fang (2023), Kusuma (2025): complete publisher full-text review where lawful access permits.

## Citation discipline
- Only cite exact claims supported by the corresponding note and inspected source.
- Do not quote numerical metrics from abstract-only papers as if full experiments were audited.
- Do not compare different targets, units, datasets or split protocols by raw MAE/RMSE.
- Do not use any external materials database to identify or infer competition pool 04 hidden labels.
