"""Run and freeze the grouped 02 ablations before reading the official 03 labels."""

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from statistics import mean, stdev
from tempfile import TemporaryDirectory
from time import perf_counter

import numpy as np
from sklearn.metrics import average_precision_score, precision_score, recall_score
from threadpoolctl import threadpool_limits

from audit.init_check import COMPOSITION, DATA, LABEL_FIELDS, read_csv
from q1.baselines import FEATURES, MAE_ALLOWANCE, ROOT, SCREENING_PRIMARY, load_inputs, sha256, write_table
from q1.metrics import SCREENING_BUDGETS, evaluate
from q1.surrogates import HIST_PARAMS, SEED, SPECS, fit_batch, fresh_estimator
from q1.violation import PROPERTY_NAMES, violation_degree


ARCHIVE = ROOT / 'experiments' / 'baseline_v1'
CV_DIR = ROOT / 'experiments' / 'q1_ablation_v1'
BASELINES = ('median', 'ridge', 'random_forest')
TIE_BAND = 0.02


def official(split, labeled):
    if labeled != (split in ('02', '03')):
        raise ValueError(f'Invalid data role for split {split}')
    manifest = json.loads((DATA / 'sha256_public.json').read_text(encoding='utf-8'))
    filename, = (name for name in manifest if name.startswith(f'{split}_'))
    path = DATA / filename
    digest = sha256(path)
    if digest != manifest[filename]:
        raise ValueError(f'Invalid checksum for {filename}')
    cols, rows = read_csv(path)
    if cols != COMPOSITION + (LABEL_FIELDS if labeled else ()):
        raise ValueError(f'Invalid field set for {filename}')
    return rows, {'file': filename, 'sha256': digest, 'rows': len(rows)}


def xy(rows):
    x = composition(rows)
    y = {name: np.array([float(row[name]) for row in rows]) for name in PROPERTY_NAMES}
    truth = np.array([violation_degree(*values) for values in zip(*y.values())])
    return x, y, truth


def composition(rows):
    return np.array([[row[k] for k in FEATURES] for row in rows])


def metric_row(name, split, ids, truth, gap, scores, raw, runtime):
    record = evaluate(ids, truth, scores)
    screening = record.pop('screening')
    ordered = np.lexsort((ids, scores))
    extra = {}
    for k in SCREENING_BUDGETS:
        chosen = ordered[:k]
        extra.update({f'top_{k}_{key}': value for key, value in screening[k].items()})
        extra[f'top_{k}_true_zero_gap'] = int((gap[chosen] == 0).sum())
        extra[f'top_{k}_true_low_v'] = int((truth[chosen] < 5).sum())
        extra[f'top_{k}_boundary_ties'] = int((scores == scores[chosen[-1]]).sum())
    lower_tenth = truth <= np.quantile(truth, 0.1)
    return {
        'model': name, 'split': split, **record, **extra,
        'screening_score': mean(screening[k]['overlap_rate'] for k in SCREENING_PRIMARY),
        'low_10pct_count': int(lower_tenth.sum()),
        'low_10pct_mae': float(np.mean(np.abs(scores[lower_tenth] - truth[lower_tenth]))),
        'raw_negative_predictions': int((raw < 0).sum()),
        'encoder_fit_seconds': runtime[0], 'head_fit_seconds': runtime[1], 'predict_seconds': runtime[2],
    }


def property_rows(name, split, targets, truth, gap_prediction, parts):
    rows = []
    for key in PROPERTY_NAMES:
        values = gap_prediction if key == 'gap' else parts.get(key)
        if values is None:
            continue
        error = values - targets[key]
        rows.append({'model': name, 'split': split, 'property': key,
                     'mae_eV': float(np.mean(abs(error))), 'signed_bias_eV': float(np.mean(error)),
                     'low_v_mae_eV': float(np.mean(abs(error[truth < 5])))})
    return rows


def positive_diagnostic(split, gap, truth, parts):
    positive = gap > 0
    p = parts['positive']
    hard = p >= 0.5
    return {
        'split': split, 'positives': int(positive.sum()), 'average_precision': average_precision_score(positive, p),
        'hard_precision': precision_score(positive, hard, zero_division=0),
        'hard_recall': recall_score(positive, hard, zero_division=0),
        'true_low_v_rows': int((truth < 5).sum()), 'true_low_v_hard_misses': int(((truth < 5) & ~hard).sum()),
        'brier': float(np.mean((positive - p) ** 2)),
        'conditional_gap_mae_eV': float(np.mean(abs(parts['gap_positive'][positive] - gap[positive]))),
    }


def compare(fold_records, ceiling):
    records = defaultdict(list)
    for row in fold_records:
        records[row['model']].append(row)
    output = []
    aggregate = ('mae', 'rmse', 'spearman', 'low_V_mae', 'top_true_1pct_mae', 'low_10pct_mae',
                 'screening_score', 'head_fit_seconds', 'predict_seconds',
                 *(f'top_{k}_{metric}' for k in SCREENING_BUDGETS
                   for metric in ('overlap_rate', 'min_true_V', 'true_zero_gap', 'true_low_v')))
    for name, group in records.items():
        summary = {'model': name, **asdict(SPECS[name])}
        for metric in aggregate:
            values = [row[metric] for row in group if row[metric] is not None]
            summary[f'{metric}_mean'] = mean(values) if values else None
            summary[f'{metric}_sd'] = stdev(values) if len(values) > 1 else None
        summary['passes_mae_limit'] = summary['mae_mean'] <= ceiling
        output.append(summary)
    return sorted(output, key=lambda r: (-r['screening_score_mean'], r['low_V_mae_mean'], r['mae_mean']))


def frozen_candidates(summary):
    eligible = [row for row in summary if row['passes_mae_limit']]
    direct = [row['model'] for row in eligible if SPECS[row['model']].direct][:2]
    physical = [row['model'] for row in eligible if not SPECS[row['model']].direct][:2]
    if not physical:
        physical = [row['model'] for row in summary if not SPECS[row['model']].direct][:1]
    return direct + physical


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, allow_nan=False,
                               default=lambda value: value.item()) + '\n', encoding='utf-8')


def write_predictions(path, rows, groups, truth, raw_scores):
    names = tuple(raw_scores)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(('id', *FEATURES, 'split', 'V_true', *(f'V_hat_{name}' for name in names)))
        writer.writerows((row['id'], *(row[k] for k in FEATURES), groups[i], truth[i],
                          *(raw_scores[name][i] for name in names)) for i, row in enumerate(rows))


def train_cv(output):
    train, train_manifest = official('02', labeled=True)
    ids, _, archived_truth, folds, hashes = load_inputs()
    comp, targets, truth = xy(train)
    assert np.array_equal(archived_truth, truth)
    archive_config = json.loads((ARCHIVE / 'results.json').read_text(encoding='utf-8'))
    assert archive_config['input_sha256'] == hashes
    _, old_scores = read_csv(ARCHIVE / 'oof_predictions.csv')
    assert [(int(r['id']), int(r['fold']), float(r['V_true'])) for r in old_scores] == list(zip(ids, folds, truth))
    _, old_metrics = read_csv(ARCHIVE / 'fold_metrics.csv')
    old_times = {(r['model'], int(r['fold'])): tuple(float(r[k]) for k in
                ('encoding_fit_seconds', 'model_fit_seconds', 'model_predict_seconds')) for r in old_metrics}
    extended = tuple(name for name in SPECS if name not in BASELINES)
    predictions = {name: np.empty(len(train)) for name in SPECS}
    gap_oof = np.empty(len(train))
    fold_records, properties, gap_diagnostics, gap_scores = [], [], [], []
    for fold in sorted(set(folds)):
        held = folds == fold
        fit = ~held
        part = {key: values[held] for key, values in targets.items()}
        for name in BASELINES:
            column = np.array([float(row[f'V_hat_{name}']) for row in old_scores])[held]
            predictions[name][held] = column
            fold_records.append(metric_row(name, fold, ids[held], truth[held], part['gap'],
                                           column, column, old_times[name, fold]))
        models, timing = fit_batch(comp[fit], {k: v[fit] for k, v in targets.items()}, truth[fit], extended)
        for name, model in models.items():
            start = perf_counter()
            scores, raw, predicted_gap, heads = model.predict_details(comp[held])
            runtime = (*timing[name], perf_counter() - start)
            predictions[name][held] = scores
            fold_records.append(metric_row(name, fold, ids[held], truth[held], part['gap'], scores, raw, runtime))
            properties.extend(property_rows(name, fold, part, truth[held], predicted_gap, heads))
            if name == 'hgb_gap_hard':
                gap_diagnostics.append(positive_diagnostic(fold, part['gap'], truth[held], heads))
                gap_oof[held] = heads['positive']
        print(f'Fold {fold}: {len(SPECS)} model scores complete.', flush=True)
    gap_scores = [{'id': i, 'fold': f, 'true_gap': g, 'p_positive': p}
                  for i, f, g, p in zip(ids, folds, targets['gap'], gap_oof)]
    ceiling = archive_config['selection_diagnostics']['tentative_mae_limit']
    summary = compare(fold_records, ceiling)
    shortlist = frozen_candidates(summary)
    freeze = {'train': train_manifest, 'fold_sha256': hashes['fold_csv'], 'seed': SEED,
              'baseline_oof_sha256': sha256(ARCHIVE / 'oof_predictions.csv'),
              'configurations': {name: asdict(spec) for name, spec in SPECS.items()},
              'estimator_parameters': {family: fresh_estimator(family, 'V', SEED).get_params()
                                       for family in ('ridge', 'random_forest', 'hgb', 'median')},
              'hist_params': HIST_PARAMS, 'cv_mae_limit': ceiling,
              'validation_mae_slack': MAE_ALLOWANCE, 'validation_screening_tie_band': TIE_BAND,
              'shortlist': shortlist, 'cv_eligible': [r['model'] for r in summary if r['passes_mae_limit']],
              'rank': 'Top-25/50 mean, then low-V MAE, then global MAE',
              'tail_weights': '1 + 4 * exp(-V / 5)', 'hard_gap_threshold': 0.5,
              'x_feature_ablation': 'Replace basic Ridge inputs by A,B,X,A:X,B:X,A=B',
              'score_clip_min': 0.0}
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent, prefix='.ablation-') as temp:
        stage = Path(temp) / 'run'
        stage.mkdir()
        write_table(stage / 'fold_metrics.csv', fold_records)
        write_table(stage / 'model_comparison.csv', summary)
        write_table(stage / 'physical_errors.csv', properties)
        write_table(stage / 'gap_diagnostics.csv', gap_diagnostics)
        write_table(stage / 'gap_probabilities.csv', gap_scores)
        write_predictions(stage / 'oof_predictions.csv', train, folds, truth, predictions)
        write_json(stage / 'frozen_shortlist.json', freeze)
        stage.rename(output)
    print(f'Frozen four-or-fewer models for 03: {shortlist}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=CV_DIR)
    args = parser.parse_args()
    target = args.out_dir.resolve()
    if target.exists():
        parser.error('Output directory already exists.')
    with threadpool_limits(limits=1):
        train_cv(target)


if __name__ == '__main__':
    main()
