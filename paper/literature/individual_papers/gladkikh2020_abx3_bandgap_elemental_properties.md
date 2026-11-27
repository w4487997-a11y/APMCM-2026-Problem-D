# Gladkikh et al. (2020): ABX3 band-gap prediction from elemental properties

**Citation:** Vladislav Gladkikh, Dong Yeon Kim, Amir Hajibabaei, Atanu Jana, Chang Woo Myung, and Kwang S. Kim. “Machine Learning for Predicting the Band Gaps of ABX3 Perovskites from Elemental Properties.” *The Journal of Physical Chemistry C* 124(16) (2020), 8905–8918. DOI: https://doi.org/10.1021/acs.jpcc.9b11768

**Reading status:** VERIFIED-METADATA; ABSTRACT AND PUBLISHER SUPPORTING-INFORMATION PREVIEW REVIEWED. Full article access may require subscription.

## Study focus
The paper studies nonlinear mappings between non-zero ABX3 perovskite band gaps and elemental properties, with an emphasis on small-data modeling. It uses Alternating Conditional Expectations (ACE) and compares with other machine-learning approaches; the related literature reports Kernel Ridge Regression and Extremely Randomized Trees as competitive methods.

## Relevance
This is a direct ABX3 band-gap representation reference. It supports the premise that elemental properties can be mapped nonlinearly to band-gap behavior, while also highlighting small-sample modeling. Its elemental-property representation differs from the competition Q1 v1's categorical A/B/X input, and its target is band gap rather than the five-term violation score V.

## Four-dimensional comparison
- **Prior methods:** ACE transformations and comparisons with kernel/tree-based regressors.
- **Theoretical basis:** nonlinear dependence of electronic band gaps on constituent-element properties.
- **Problem-specific adaptation:** Q1 v1 uses categorical site identities and an expected penalty mixture for the zero/positive-gap branches; this paper focuses on non-zero gap regression from elemental descriptors.
- **Empirical contribution:** a small-data ABX3 band-gap modeling study; its results are not a direct benchmark for Q1 V.

## Sources
- ACS publisher page: https://pubs.acs.org/doi/10.1021/acs.jpcc.9b11768
- DOI: https://doi.org/10.1021/acs.jpcc.9b11768
- Supporting-information preview: https://pubs.acs.org/doi/pdf/10.1021/acs.jpcc.9b11768
