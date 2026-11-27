"""Complete the V1.2 comparison panel and stability checks after the v1 freeze."""

import argparse
import json
import platform
from importlib.metadata import version
from itertools import groupby
from pathlib import Path
from statistics import mean, stdev
from tempfile import TemporaryDirectory
from time import perf_counter

import joblib
import numpy as np
from sklearn.metrics import auc, precision_recall_curve
from threadpoolctl import threadpool_limits

from q1.baselines import FEATURES, ROOT, load_inputs, sha256, write_table
from q1.delivery import score_pool_group
from q1.experiments import (BASELINES, CV_DIR, metric_row, official, positive_diagnostic, property_rows,
                            write_json, write_predictions, xy)
from q1.metrics import SCREENING_BUDGETS
from q1.surrogates import SEED, SPECS, fit_batch
from q1.violation import PENALTY_NAMES, PROPERTY_NAMES


OUTPUT = ROOT / 'experiments' / 'q1_v12'
FROZEN = ROOT / 'handoff' / 'v1'
ORDINARY = ('ridge_indirect', 'hgb_indirect')
GAP_PANEL = ('hgb_indirect', 'hgb_gap_hard', 'hgb_gap_soft', 'hgb_gap_mix', 'hgb_gap_expected')
STABILITY_MODELS = ('hgb_direct', 'hgb_gap_mix')
ESTIMATOR_SEEDS = (42, 1729, 31415)
GROUP_SEEDS = (1729, 31415)
THRESHOLD_WINDOW = 0.2


def deviations(properties):
    f, g, vb, cb = (np.asarray(properties[k]) for k in PROPERTY_NAMES)
    return np.column_stack((f - 0.21, 1.4 - g, g - 3.1, 5.73 - vb, cb - 4.50))


def penalties(values):
    return 4 * np.maximum(values, 0.0) ** 2


def predicted_terms(parts, gap):
    if gap is not None:
        return penalties(deviations({**parts, 'gap': gap}))
    if 'gap_positive' not in parts:
        return None
    positive = np.maximum(parts['gap_positive'], 0.0)
    probability = parts['positive']
    return (probability[:, None] * penalties(deviations({**parts, 'gap': positive}))
            + (1.0 - probability[:, None]) * penalties(deviations({**parts, 'gap': np.zeros_like(positive)})))


def screen_distribution(ids, truth, model, pred):
    order = np.lexsort((ids, pred))
    rows = []
    for k in SCREENING_BUDGETS:
        vals = truth[order[:k]]
        rows.append({'model': model, 'K': k, 'true_V_min': vals.min(),
                     'true_V_p25': np.quantile(vals, 0.25), 'true_V_median': np.median(vals),
                     'true_V_p75': np.quantile(vals, 0.75), 'true_V_max': vals.max(),
                     'true_V_mean': vals.mean(), 'true_V_lt_5': (vals < 5).sum()})
    return rows


def save_vehicle(directory, name, model, splits):
    directory.mkdir(parents=True, exist_ok=True)
    bundle = {'version': name, 'name': name, 'model': model, 'train_splits': splits, 'features': FEATURES}
    joblib.dump(bundle, directory / f'{name}.joblib', compress=3)
    return bundle


def comparison_panel(out, train, validation, train_info, validation_info):
    x, y, v = xy(train)
    valid_x, valid_y, truth = xy(validation)
    ids = np.array([int(row['id']) for row in validation])
    names = tuple(SPECS)
    models, runtimes = fit_batch(x, y, v, names)
    scores, metrics, properties, physical_rows, boundaries, penalty_rows = {}, [], [], [], [], []
    clipping_rows, distribution, classifier = [], [], None
    actual_dev = deviations(valid_y)
    actual_terms = penalties(actual_dev)
    low = truth < 5
    for name, model in models.items():
        start = perf_counter()
        pred, raw, gap, parts = model.predict_details(valid_x)
        runtime = (*runtimes[name], perf_counter() - start)
        scored = metric_row(name, '03', ids, truth, valid_y['gap'], pred, raw, runtime)
        metrics.append(scored)
        scores[name] = pred
        distribution.extend(screen_distribution(ids, truth, name, pred))
        before = metric_row(name, '03', ids, truth, valid_y['gap'], raw, raw, runtime)
        fields = ('mae', 'rmse', 'spearman', 'low_V_mae', 'low_10pct_mae', 'screening_score',
                  *(f'top_{k}_{m}' for k in SCREENING_BUDGETS for m in ('boundary_ties', 'overlap_rate')))
        clipping_rows.append({'model': name, 'negative_before': int(np.sum(raw < 0)),
                              'negative_after': int(np.sum(pred < 0)),
                              **{f'{field}_{when}': rec[field] for field in fields
                                 for when, rec in (('before', before), ('after', scored))}})
        if name in BASELINES or name == 'hgb_direct':
            save_vehicle(out / 'models' / 'baseline', name, model, ['02'])
        if model.spec.direct:
            continue
        estimated = predicted_terms(parts, gap)
        properties.extend(property_rows(name, '03', valid_y, truth, gap, parts))
        if name in ORDINARY:
            ordinary = {**parts, 'gap': gap}
            predicted_dev = deviations(ordinary)
            for i, term in enumerate(PENALTY_NAMES):
                near = np.abs(actual_dev[:, i]) <= THRESHOLD_WINDOW
                crossed = (actual_dev[:, i] > 0) != (predicted_dev[:, i] > 0)
                boundaries.append({'model': name, 'penalty': term, 'window_eV': THRESHOLD_WINDOW,
                                   'near_rows': near.sum(), 'mismatches_near': crossed[near].sum(),
                                   'penalty_mae_near': np.mean(np.abs(estimated[near, i] - actual_terms[near, i])),
                                   'raw_negative_gap_rows': np.sum(parts['gap'] < 0)})
        if estimated is not None:
            if not np.allclose(estimated.sum(axis=1), pred, rtol=1e-12, atol=1e-12):
                raise ValueError(f'Five-term assembly disagrees for {name}')
            for index, term in enumerate(PENALTY_NAMES):
                for scope, chosen in (('all', np.ones(len(truth), dtype=bool)), ('V_lt_5', low)):
                    penalty_rows.append({'model': name, 'scope': scope, 'term': term, 'rows': chosen.sum(),
                                         'true_penalty_mean': actual_terms[chosen, index].mean(),
                                         'pred_penalty_mean': estimated[chosen, index].mean(),
                                         'penalty_mae': np.abs(estimated[chosen, index] - actual_terms[chosen, index]).mean()})
        if name == 'hgb_gap_hard':
            truth_pos = valid_y['gap'] > 0
            prob = parts['positive']
            precision, recall, _ = precision_recall_curve(truth_pos, prob)
            raw_positive = parts['gap_positive'][truth_pos]
            classifier = {**positive_diagnostic('03', valid_y['gap'], truth, parts),
                          'pr_auc_trapezoidal': auc(recall, precision), 'hard_threshold': 0.5,
                          'clipped_conditional_gap_mae_eV': float(np.mean(
                              abs(np.maximum(raw_positive, 0.0) - valid_y['gap'][truth_pos])))}
            write_table(out / 'gap_probabilities_03.csv', [
                {'id': sample_id, 'true_gap': g, 'p_positive': p}
                for sample_id, g, p in zip(ids, valid_y['gap'], prob)])
        for i, row in enumerate(validation):
            physical_rows.append({
                'model': name, 'id': row['id'], **{key: row[key] for key in FEATURES},
                **{f'true_{key}': value[i] for key, value in valid_y.items()},
                **{f'pred_{key}': parts[key][i] if key in parts else None
                   for key in ('e_form', 'vbm', 'cbm', 'positive', 'gap_positive', 'gap_penalty_positive')},
                'pred_gap_raw': parts['gap'][i] if 'gap' in parts else None,
                'pred_gap': gap[i] if gap is not None else None, 'V_true': truth[i], 'V_hat': pred[i],
                **{f'pred_{term}': estimated[i, j] if estimated is not None else None
                   for j, term in enumerate(PENALTY_NAMES)},
            })

    by_model = {r['model']: r for r in metrics}
    write_predictions(out / 'validation_predictions_03.csv', validation, ['03'] * len(validation), truth, scores)
    keep = [name for name in names if SPECS[name].direct]
    write_predictions(out / 'val_predictions_baseline.csv', validation, ['03'] * len(validation), truth,
                      {name: scores[name] for name in (*BASELINES, 'hgb_direct')})
    write_table(out / 'baseline_metrics.csv', [by_model[n] for n in (*BASELINES, 'hgb_direct')])
    write_table(out / 'model_comparison.csv', [by_model[n] for n in names])
    write_table(out / 'indirect_metrics.csv', properties)
    write_table(out / 'val_physics_predictions.csv', physical_rows)
    write_table(out / 'direct_vs_indirect.csv', [by_model[n] for n in ('ridge', 'ridge_indirect', 'hgb_direct', 'hgb_indirect')])
    write_table(out / 'gap_ablation.csv', [by_model[n] for n in GAP_PANEL])
    write_table(out / 'tail_ablation.csv', [by_model[n] for n in ('hgb_direct', 'hgb_tail')])
    write_table(out / 'feature_ablation.csv', [by_model[n] for n in ('ridge', 'ridge_interaction')])
    write_table(out / 'ablation.csv', [by_model[n] for n in (*keep, *[n for n in names if n not in keep])])
    write_table(out / 'score_clipping_compare.csv', clipping_rows)
    write_table(out / 'screening_true_v_distribution.csv', distribution)
    write_table(out / 'threshold_errors.csv', boundaries)
    write_table(out / 'penalty_decomposition.csv', penalty_rows)
    write_json(out / 'gap_classifier_metrics.json', classifier)

    ordinary = models['hgb_indirect']
    directory = out / 'models' / 'four_properties'
    directory.mkdir(parents=True)
    for head, estimator in ordinary.estimators.items():
        joblib.dump({'property': head, 'estimator': estimator, 'encoder': ordinary.encoder,
                     'features': FEATURES, 'train_splits': ['02'], 'gap_floor_for_inference': head == 'gap'},
                    directory / f'{head}.joblib', compress=3)
    write_json(out / 'run_config.json', {
        'purpose': 'V1.2 supplemental verification after selection. No influence on frozen v1.',
        'sources': {'02': train_info, '03': validation_info},
        'seed': SEED, 'near_threshold_window_eV': THRESHOLD_WINDOW,
        'frozen_release_sha256': sha256(FROZEN / 'manifest.json'),
        'frozen_model_names': json.loads((FROZEN / 'manifest.json').read_text(encoding='utf-8'))['shortlist'],
        'frozen_cv_config_sha256': sha256(CV_DIR / 'frozen_shortlist.json'),
        'fit_seconds': {n: {'encoder': e, 'heads': h} for n, (e, h) in runtimes.items()},
        'configuration_reference': 'experiments/q1_ablation_v1/frozen_shortlist.json',
        'python': platform.python_version(),
        'packages': {name: version(name) for name in ('numpy', 'scipy', 'scikit-learn', 'joblib', 'threadpoolctl')},
    })

    joint, props, y = xy(train + validation)
    precheck, time = fit_batch(joint, props, y, ['ridge'])
    directory = out / 'baseline_v0'
    bundle = save_vehicle(directory, 'baseline_v0', precheck['ridge'], ['02', '03'])
    pools, original = {}, {}
    for key in ('07', '08'):
        pools[key], original[key] = official(key, labeled=False)
    baseline_scores, stats, cost = score_pool_group(bundle, pools)
    for n, key in enumerate(('07', '08'), 2):
        write_table(directory / f'q{n}_pool_predictions.csv',
                    [{**row, 'pool': row['source_pool']} for row in baseline_scores[key]])
    write_json(directory / 'manifest.json', {'model_version': 'baseline_v0', 'scope': 'temporary interface baseline',
                                             'inputs': original, 'training': [train_info, validation_info],
                                             'fit_seconds': time['ridge'], 'outputs': stats, 'predict_cost': cost,
                                             'evaluation_used_for_v1': False})
    print(f'03 comparisons complete: {len(metrics)} configurations, {len(validation):,} rows each.', flush=True)


def group_assignment(x, seed):
    from hashlib import sha256 as digest

    pairs = list(map(tuple, x[:, :2]))
    ordered = sorted(set(pairs), key=lambda p: digest(f'q1_v12|{seed}|{p[0]}|{p[1]}'.encode()).digest())
    lookup = {pair: index % 5 + 1 for index, pair in enumerate(ordered)}
    return np.array([lookup[pair] for pair in pairs])


def run_stability(out, train):
    ids, _, _, frozen, _ = load_inputs()
    x, y, truth = xy(train)
    rows = []
    scenarios = [('estimator_seed', seed, 42, frozen) for seed in ESTIMATOR_SEEDS]
    scenarios += [('group_assignment', 42, seed, group_assignment(x, seed)) for seed in GROUP_SEEDS]
    for scenario, seed, group_seed, groups in scenarios:
        for fold in range(1, 6):
            fit = groups != fold
            held = ~fit
            if set(map(tuple, x[fit, :2])) & set(map(tuple, x[held, :2])):
                raise ValueError('Ordered pair crosses fit and assessment folds')
            models, times = fit_batch(x[fit], {k: v[fit] for k, v in y.items()}, truth[fit], STABILITY_MODELS, seed)
            for name, model in models.items():
                begin = perf_counter()
                pred, raw, _, _ = model.predict_details(x[held])
                data = metric_row(name, fold, ids[held], truth[held], y['gap'][held], pred, raw,
                                  (*times[name], perf_counter() - begin))
                rows.append({'scenario': scenario, 'estimator_seed': seed, 'group_seed': group_seed,
                             **data})
        print(f'02 stability: {scenario}, estimator seed={seed}, group seed={group_seed} complete.', flush=True)
    write_table(out / 'stability.csv', rows)
    key = lambda row: (row['scenario'], row['estimator_seed'], row['group_seed'], row['model'])
    summary = []
    for group, iterator in groupby(sorted(rows, key=key), key):
        values = list(iterator)
        scores = {}
        for metric in ('mae', 'low_V_mae', 'low_10pct_mae', 'screening_score',
                       'top_25_overlap_rate', 'top_50_overlap_rate'):
            sample = [record[metric] for record in values]
            scores[f'{metric}_mean'] = mean(sample)
            scores[f'{metric}_sd'] = stdev(sample)
        summary.append(dict(zip(('scenario', 'estimator_seed', 'group_seed', 'model'), group), **scores))
    write_table(out / 'stability_summary.csv', summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=OUTPUT)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        parser.error('Output directory already exists. Use a new path.')
    out.parent.mkdir(parents=True, exist_ok=True)
    train, train_info = official('02', labeled=True)
    validation, validation_info = official('03', labeled=True)
    with threadpool_limits(limits=1), TemporaryDirectory(dir=out.parent, prefix='.q1-v12-') as temporary:
        stage = Path(temporary) / 'run'
        stage.mkdir()
        comparison_panel(stage, train, validation, train_info, validation_info)
        run_stability(stage, train)
        stage.rename(out)
    print(f'Published the V1.2 supplementary evidence to {out}.')


if __name__ == '__main__':
    main()
