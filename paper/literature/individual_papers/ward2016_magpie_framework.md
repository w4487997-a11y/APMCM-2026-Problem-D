# Ward et al. (2016): composition-derived materials attributes

**Citation:** Ward, L., Agrawal, A., Choudhary, A., & Wolverton, C. (2016). A general-purpose machine learning framework for predicting properties of inorganic materials. npj Computational Materials, 2, 16028. https://doi.org/10.1038/npjcompumats.2016.28

**Reading status:** FULLTEXT-REVIEWED (publisher HTML body reviewed); supplementary information not yet reviewed.

## Research question and contribution
The paper develops a reusable machine-learning framework for inorganic materials based on composition-derived attributes and a strategy for partitioning chemically similar materials into groups before fitting separate models.

## Representation / descriptors
The article reports 145 attributes in four broad categories:
1. stoichiometric attributes;
2. statistics (mean, mean absolute deviation, range, minimum, maximum and mode) of 22 elemental properties;
3. electronic-structure attributes based on s/p/d/f valence-shell fractions;
4. ionic-compound attributes related to oxidation-state feasibility and electronegativity-derived ionic character.

The central rationale is that attributes should uniquely represent compositions while reflecting relevant physical/chemical factors. Attribute relevance varies by target property and material class.

## Models and validation
The article evaluates multiple ML algorithms and uses cross-validation to choose algorithms and material-group partition strategies. It emphasizes that the best attributes differ by property and material family. Its examples include OQMD crystalline compounds and metallic-glass data.

## Relation to this project
The current Q1 code (q1/surrogates.py) does not implement Ward's 145 Magpie attributes. Its primary input is the ordered site tuple (A, B, X), transformed with categorical encoders for tree models. The frozen model is hgb_gap_mix; it combines predicted non-gap penalty terms with a probability-weighted zero-gap / positive-gap penalty contribution.

Ward is therefore a theoretical and methodological comparator for composition representation, not a direct description of the project's current feature set. It can motivate a future, separately controlled descriptor ablation only if competition rules permit and the team explicitly authorizes such an experiment. It must not be retroactively claimed as part of the frozen v1 model.

## Four-dimensional comparison
- Prior methods: composition-derived elemental statistics and materials-aware data partitioning.
- Theoretical foundation: elemental composition and elemental property distributions can encode chemically meaningful differences relevant to material properties.
- Problem-specific adaptation: this project uses the competition's ordered A/B/X categorical site identities and strict data contract; it does not use the 145-attribute representation.
- Empirical contribution: Ward demonstrates broad utility on its own materials datasets. It does not validate this project's V score, competition split, or Q1 results.

## Limitations / cautions
Do not compare reported metrics numerically with competition Q1 results: datasets, targets, splits and evaluation protocols differ. Supplementary information should be checked before quoting exact Magpie attribute definitions or implementation details.

## Source
Publisher full text: https://www.nature.com/articles/npjcompumats201628
DOI: https://doi.org/10.1038/npjcompumats.2016.28


## Additional full-text details reviewed
The publisher article reports 228,676 OQMD compounds selected as lowest-energy entries per unique composition for its crystalline-property example. It evaluates algorithms with 10-fold cross-validation. For a screening demonstration, it compares random selection, a single global model and a chemically partitioned model for selecting 30 compounds from a held-out set: the reported fraction within the target band-gap range rises from just over 12% (random) to about 46% (single model) and about 67% (partitioned model). The hierarchical partition first predicts a band-gap range and then partitions by anion family. This supports the value of screening metrics and chemistry-aware partitioning, but is not the same partition rule as this project's ordered-(A,B) grouped folds.

The paper's 145 attributes comprise stoichiometric attributes, statistics over 22 elemental properties, valence-shell fractions and ionic-compound attributes. The article notes that descriptor importance varies by property and material family; 145 is not a universal complete descriptor set.

## Reproducibility caveat from later literature
Persaud, Ward and Hattrick-Simpers (2024) specifically revisited reproducibility of this framework and reported that the Ward supplementary package did not contain all band-gap training, prediction and analysis scripts needed for full reproduction. Therefore, distinguish the original article's published method and available SI from a fully executable reproduction package. See paper/literature/individual_papers/persaud2024_materials_informatics_reproducibility.md.
