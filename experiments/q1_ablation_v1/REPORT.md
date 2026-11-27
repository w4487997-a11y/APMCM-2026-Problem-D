# A Band-Gap Penalty Mixture for Rare-Target Perovskite Screening

Internal Q1 research material, 27 November 2026. The primary result is a composition-only surrogate that uses histogram gradient boosting to predict material properties and combine the zero- and positive-gap penalties. On official validation file 03 it achieved MAE 2.4715, RMSE 4.5827 and Spearman correlation 0.9383. Its Top-25 and Top-50 overlap rates were 32% and 40%.

## Task and data

Each candidate is represented by its ordered A-site element, B-site element and anion family X. Formation energy screens the energetics of candidate formation. The band gap and band edges screen the electronic properties. The official thresholds are 0.21 eV for formation energy, a 1.4–3.1 eV gap window, 5.73 eV for the valence-band maximum and 4.50 eV for the conduction-band minimum. Let `h(d) = [max(0,d)/0.5]^2`. The official violation score sums h over deviations `e_form−0.21`, `1.4−gap`, `gap−3.1`, `5.73−VBM` and `CBM−4.50`.

We reconstructed labels for 11,256 training records and 3,969 validation records. Neither public labeled split contained a zero-violation sample. Zero gaps comprised 96.16% of 02 and 96.45% of 03. A zero gap contributes 7.84 even if all other penalties vanish. The holdout consists of 3,703 composition records with the labels removed. The organizer reports 19 zero-violation records and 15 strictly feasible records. Under the squared-hinge score, equality incurs zero penalty. The organizer's README additionally uses a closed gap interval alongside strict formation-energy and band-edge limits in its prose definition. [Official problem, pp. 2–5](../../2026%20APMCM%20Problem%20D/2026%20APMCM%20Problem%20D.pdf) · [Organizer's data README, §2](../../2026%20APMCM%20Problem%20D/date/README_数据集说明.md)

The README documents the separate hash orderings and the organizer's assignment of the 19 zero-violation groups to 04. We verified the observed group sizes and the absence of zero scores in 02 and 03. The identity of each holdout target remains unobserved. Section 7 documents six-decimal rounding. The largest local label-reconstruction discrepancy was 1.0189444e-5, and every public label passed its rounding check. [Organizer's data README, §§5, 7](../../2026%20APMCM%20Problem%20D/date/README_数据集说明.md) · [Data audit](../../audit/q1_label_audit.json)

## Surrogate and controls

For direct regression, the inputs are A, B and X. The median, one-hot Ridge and random-forest controls are inherited from the verified baseline. Histogram gradient boosting uses separate categorical encodings for A, B and X, fitted within each training partition. The same boosting settings are applied to the direct and property-based comparisons. A Ridge feature ablation adds A:X, B:X and an A=B indicator. A direct boosting loss ablation weights each training record by `1 + 4 exp(−V/5)`. Neither feature construction requires external descriptors. [Estimator documentation](https://scikit-learn.org/1.7/modules/ensemble.html#histogram-based-gradient-boosting)

In the selected model, three regression heads estimate formation energy, VBM and CBM. Let g be the sum of the two official band-gap penalties. A classifier estimates `q = P(gap > 0 | A,B,X)` and a regression head trained on positive-gap records estimates `g_plus`, the positive-gap magnitude in eV. For inference, `g_plus` is floored at zero before applying the penalty. The band-gap contribution is

```text
G_mix = (1 − q) g(0) + q g(g_plus)
      = (1 − q) 7.84 + q g(g_plus).
V_hat = h(e_form_hat − 0.21) + h(5.73 − VBM_hat)
        + h(CBM_hat − 4.50) + G_mix.
```

The hard gate uses a 0.5 threshold. The mean-gap fusion computes `g(q g_plus)`. Convexity of g implies that mean-gap fusion is at most the mixture of point penalties for the same inputs. We also fitted the conditional expected positive-gap penalty directly and then mixed with g(0). That control tests the impact of the plug-in approximation to the positive branch. The final mixture output is a violation score in the official units. It does not estimate the probability of strict feasibility.

## Grouped development results

The five folds in 02 are disjoint by ordered (A,B) pair. Each method sees identical fit and validation groups. Top-K overlap is the size of the intersection between the predicted and observed lowest-K sets, divided by K. ID is the secondary sorting key. The screening score averages Top-25 and Top-50 overlap. The internal global-MAE limit of 4.4980 was fixed at 105% of the strongest original direct baseline.

| Configuration | MAE | V < 5 MAE | Top-25 | Top-50 | Screening score |
| --- | ---: | ---: | ---: | ---: | ---: |
| Median | 7.781 | 20.404 | 1.6% | 1.6% | 1.6% |
| Direct Ridge | 4.323 | 12.463 | 12.8% | 16.0% | 14.4% |
| Direct random forest | 4.284 | 13.901 | 16.0% | 15.2% | 15.6% |
| Ridge with site–X interactions | 3.346 | 11.615 | 15.2% | 20.0% | 17.6% |
| Property Ridge | 4.204 | 9.942 | 14.4% | 17.2% | 15.8% |
| Direct boosting | 2.877 | 11.442 | 28.0% | 26.0% | 27.0% |
| Tail-weighted direct boosting | 3.047 | 9.181 | 29.6% | 33.6% | 31.6% |
| Property boosting, ordinary gap | 2.860 | 7.327 | 32.8% | 34.0% | 33.4% |
| Property boosting, hard gate | 2.617 | 9.473 | 37.6% | 35.2% | 36.4% |
| Property boosting, mean-gap fusion | 2.705 | 7.969 | 36.8% | 41.2% | 39.0% |
| Property boosting, conditional penalty | 2.647 | 10.243 | 36.0% | 34.4% | 35.2% |
| **Property boosting, penalty mixture** | **2.649** | **9.398** | **40.0%** | **39.6%** | **39.8%** |

The penalty mixture improved the screening score against direct boosting on all five matched folds, by 12.8 percentage points on average with a paired standard deviation of 9.1 points. Against the ordinary-gap property model, the improvement was 6.4 points with a paired standard deviation of 3.5 points. The 0.8-point lead over mean-gap fusion varied in sign across folds. Ordinary-gap property boosting had the smallest low-tail MAE. These trade-offs are visible in [paired ablations](paired_ablation.csv) and the [grouped comparison figure](figures/grouped_ablation.svg).

The positive-gap classifier had pooled out-of-fold average precision of 0.485 on 02 and average precision of 0.577 on 03. At the 0.5 cutoff, 49 of the 70 03 records with V < 5 would be assigned zero gap. The conditional regression head had raw MAE 0.829 eV over the 141 positive-gap validation records. This high miss count explains the decision to compare soft combinations even though the classifier is informative. [Precision–recall curve](figures/positive_gap_precision_recall.svg) · [03 property plots](figures/validation_properties.svg)

## Official validation and choice

The four finalists were frozen before fitting and scoring the official validation panel. The 03 MAE limit was set at 105% of the best shortlisted direct model's MAE, or 2.8432. A 2-percentage-point screening tie band allows a comparison of low-tail MAE when models are nearly tied.

| Frozen candidate | MAE | RMSE | Spearman | V < 5 MAE | Top-25 hits | Top-50 hits | Top-50 zero-gap records |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct boosting | 2.7078 | 4.6876 | 0.9267 | 11.2603 | 4 | 13 | 29 |
| Tail-weighted direct boosting | 2.8655 | 4.7992 | 0.9223 | 8.3598 | 10 | 18 | 22 |
| Mean-gap fusion | 2.5278 | 4.6885 | 0.9377 | 6.3517 | 7 | 19 | 17 |
| **Penalty mixture** | **2.4715** | **4.5827** | **0.9383** | **8.2654** | **8** | **20** | **13** |

The tail-weighted model had a screening score of 38% and exceeded the MAE limit. The penalty mixture attained 36%, compared with 33% for mean-gap fusion and 21% for standard direct boosting. Mean-gap fusion had the smaller low-tail absolute error, with its screening score outside the specified tie band. At budgets 10, 25, 50 and 100 the selected model had 1, 8, 20 and 41 overlaps. The minimum observed V among the selected rows was 0.0196 at each budget. The 03 least-violating row was therefore present in each list.

The standard direct boosting comparator isolates the benefit of the scoring architecture within the same model family. Relative to it, the mixture reduced 03 MAE by 8.7%, doubled the Top-25 hits and raised Top-50 hits from 13 to 20. It reduced the number of zero-gap candidates in the Top-50 from 29 to 13. The rejected variants, fold-level timings and ranking measurements remain in the release. The expanded V1.2 diagnostics were computed after this selection. They report the complete gap comparison, the five-penalty decomposition and the additional stability tests. [Frozen 03 panel](../../handoff/v1/validation_metrics.csv) · [Configuration and freeze](frozen_shortlist.json) · [V1.2 appendix](../q1_v12/REPORT.md)

## Scope of the results

CV and 03 evaluate unseen ordered pairs among observed elements. Official 03 was used to choose the specification. Since 03 contains no V=0 record and the labels for 04 are unavailable, the recall of true rare targets and holdout MAE are unknown. The estimates do not establish physical feasibility. The 03 VBM and CBM MAE increased from 0.061 and 0.061 eV globally to 0.667 and 0.664 eV in the low-V subset. This limits the reliability of the estimated order among the most promising compositions. The classifier probability was used without separate probability calibration. No claim about unfamiliar element identities or an energy-reference constraint is needed.

Q1 model weights were fitted on 02 and scored on 04. After freezing the specification, a separate model was fitted on 02+03 to score the Q2/Q3 candidates. During a recorded single-thread run, the final Q1 heads fitted in 1.06 s and scored 3,703 rows in 0.32 s. The Q2/Q3 heads fitted in 1.20 s and scored 8,112 distinct compositions in 0.61 s. [Release configuration and timings](../../handoff/v1/manifest.json)

## References

1. Organizing Committee of APMCM. *2026 Asia and Pacific Mathematical Contest in Modeling, Problem D*. 2026, pp. 2–5. [Official task](../../2026%20APMCM%20Problem%20D/2026%20APMCM%20Problem%20D.pdf)
2. Friedman, J. H. Greedy function approximation: A gradient boosting machine. *The Annals of Statistics*, 2001, 29(5), 1189–1232. [DOI](https://doi.org/10.1214/aos/1013203451)
3. Scikit-learn developers. *Histogram-Based Gradient Boosting*, version 1.7.2. [Implementation documentation](https://scikit-learn.org/1.7/modules/ensemble.html#histogram-based-gradient-boosting)
