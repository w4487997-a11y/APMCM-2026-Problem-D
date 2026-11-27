# V1.2 Supplementary Evidence for the Q1 Surrogate

This appendix reports matched validation diagnostics added after the v1 specification was frozen. All supplementary validation models were trained on 02 and scored on the same 3,969 rows of 03. The frozen model and its published predictions retain their original scores. [Frozen selection and full method](../q1_ablation_v1/REPORT.md)

## Official data conventions

The problem paper reports 19 zero-violation records and 15 records meeting the strict feasibility conditions. A zero squared-hinge score includes threshold equality. The paper's strict target uses an open band-gap window, while its penalty table uses closed gap limits. Section 2 of the organizer's README describes a mixed convention with a closed gap window and strict formation-energy, VBM and CBM limits. We used the five official penalties to define V and kept strict feasibility as a separate indicator. [Problem paper, pp. 2–5](../../2026%20APMCM%20Problem%20D/2026%20APMCM%20Problem%20D.pdf) · [Organizer's data README, §2](../../2026%20APMCM%20Problem%20D/date/README_数据集说明.md)

Section 5 states that the 19 zero-violation rows belong to distinct ordered A–B pairs locked into 04, with the remaining pairs partitioned by the documented hash procedure. This organizer statement is separate from our CSV checks. We verified the public group membership and the absence of zero-violation samples in 02 and 03. The identities of the blind targets remain unobserved. Section 7 documents six decimal places and a maximum rounding difference of about 1.02e-5. We recomputed all public labels, observed maximum absolute discrepancy 1.0189444e-5 and checked every row against its rounding interval. [Organizer's data README, §§5, 7](../../2026%20APMCM%20Problem%20D/date/README_数据集说明.md) · [Row-wise checks](../../audit/label_checks.csv)

| Strict individual criterion | 02 (11,256 rows) | 03 (3,969 rows) |
| --- | ---: | ---: |
| Formation energy below threshold | 160 | 71 |
| Band gap in the open target window | 128 | 34 |
| VBM above threshold | 6,782 | 2,465 |
| CBM below threshold | 134 | 49 |
| All four strict criteria | 0 | 0 |

## Matched official validation controls

| Boosting variant | MAE | RMSE | V < 5 MAE | Lowest-10% MAE | Top-25 hits | Top-50 hits | Screening score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct | 2.7078 | 4.6876 | 11.2603 | 3.8093 | 4 | 13 | 21% |
| Property model, ordinary gap | 2.6402 | 4.7749 | 5.2955 | 3.2071 | 9 | 19 | 37% |
| Property model, hard gate | 2.4379 | 4.6031 | 8.5482 | 3.1230 | 8 | 16 | 32% |
| Property model, mean gap | 2.5278 | 4.6885 | 6.3517 | 3.0268 | 7 | 19 | 33% |
| Property model, point penalty mixture (v1) | 2.4715 | 4.5827 | 8.2654 | 3.1043 | 8 | 20 | 36% |
| Property model, directly fitted conditional expected gap penalty | 2.4624 | 4.5298 | 8.9205 | 3.1688 | 11 | 19 | 41% |

The property comparisons share the same fitted formation-energy, VBM and CBM heads. The post-freeze results favor the directly fitted expected penalty on the combined screening metric on 03. It scored 35.2% in the original grouped development folds, versus 39.8% for the frozen point-penalty mixture. The ordinary gap models also obtained lower low-tail MAE. These additional 03 comparisons describe the trade-offs. Model selection had already used 03 and remains recorded separately. The lowest-10% column covers 397 rows and V < 5 covers 70. [Full 03 comparison](model_comparison.csv) · [Selection history](model_selection.md)

The positive-gap classifier's average precision was 0.5774 and the trapezoidal area under its PR curve was 0.5762. At threshold 0.5 its precision and recall were 0.8500 and 0.2411. It missed 49 of the 70 observed low-V rows. The conditional gap MAE after flooring negative gaps was 0.8290 eV over 141 positives. We also report error propagation in a ±0.2 eV band at each official threshold and the observed V distribution in each top-K list. [Classifier metrics](gap_classifier_metrics.json) · [Threshold errors](threshold_errors.csv) · [Screened V distributions](screening_true_v_distribution.csv)

## Stability on the ordered pairs of 02

We varied the estimator seed across 42, 1729 and 31415 on the original five folds. The compared boosting metrics were unchanged across seeds for the fixed training partitions. With the estimator seed fixed at 42, two alternate grouped allocations yielded screening scores of 40.2% and 42.6% for the frozen mixture, against 28.0% and 26.0% for direct boosting. Each allocation kept all X values of a pair together. This test used only 02. [Fifty fold-level results](stability.csv) · [Stability summary](stability_summary.csv)

## Figures

- **Decomposition of the five violation penalties on file 03.** Mean observed and predicted penalty components over all 3,969 rows and the 70 records with observed V < 5. The probability mixture uses separate lower-gap and upper-gap penalties. [SVG](figures/five_penalty_decomposition.svg) · [PNG](figures/five_penalty_decomposition.png) · [Underlying values](penalty_decomposition.csv)
- **Ordinary four-property surrogate on file 03.** Predictions for all four physical quantities. The band-gap panel shows clipped nonnegative predictions. [SVG](figures/ordinary_four_properties.svg) · [PNG](figures/ordinary_four_properties.png)
- **Positive-gap classification on file 03.** Precision and recall curve with the hard gate at 0.5 and the prevalence reference. [SVG](figures/gap_pr_03.svg) · [PNG](figures/gap_pr_03.png)
