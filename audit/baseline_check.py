"""Independently check baseline inputs, fold predictions, screening, and summary scores."""

import argparse
import csv
import json
from decimal import Decimal
from hashlib import sha256
from math import isclose, isfinite, sqrt
from pathlib import Path
from statistics import mean, median, stdev

import numpy as np
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / '2026 APMCM Problem D' / 'date' / '02_castelli_train.csv'
FOLDS = ROOT / 'audit' / 'phase1' / 'folds_02.csv'
DEFAULT_RUN = ROOT / 'experiments' / 'baseline_v1'
MODELS = ('median', 'ridge', 'random_forest')
KEY = ('id', 'A', 'B', 'X')
BUDGETS = (10, 25, 50, 100)


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def exact_violation(row):
    d = Decimal
    form, gap, vbm, cbm = (d(row[name]) for name in ('e_form', 'gap', 'vbm', 'cbm'))
    return 4 * (max(form - d('.21'), 0)**2 + max(d('1.4') - gap, gap - d('3.1'), 0)**2
                + max(d('5.73') - vbm, 0)**2 + max(cbm - d('4.50'), 0)**2)


def check_close(actual, reported):
    if not isclose(actual, float(reported), rel_tol=1e-11, abs_tol=1e-11):
        raise ValueError(f'Metric mismatch: {actual} versus {reported}')


def check_fold_scores(rows, published, model):
    y = np.array([float(row['V_true']) for row in rows])
    p = np.array([float(row[f'V_hat_{model}']) for row in rows])
    ids = np.array([int(row['id']) for row in rows])
    expected_order = np.lexsort((ids, y))
    predicted_order = np.lexsort((ids, p))
    err = abs(y - p)
    low = y < 5
    one_percent = expected_order[:(len(rows) + 99) // 100]
    assert int(published['low_V_count']) == int(sum(low))
    check_close(float(np.mean(err)), published['mae'])
    check_close(sqrt(float(np.mean(err**2))), published['rmse'])
    check_close(float(np.mean(err[low])), published['low_V_mae'])
    check_close(float(np.mean(err[one_percent])), published['top_true_1pct_mae'])
    if np.ptp(p) == 0:
        assert published['spearman'] == ''
    else:
        check_close(float(spearmanr(y, p).statistic), published['spearman'])
    top = {}
    for k in BUDGETS:
        chosen = predicted_order[:k]
        hits = len(np.intersect1d(expected_order[:k], chosen))
        top[k] = hits / k
        assert int(published[f'top_{k}_overlap_count']) == hits
        check_close(top[k], published[f'top_{k}_overlap_rate'])
        check_close(float(min(y[chosen])), published[f'top_{k}_min_true_V'])
    check_close(mean([top[25], top[50]]), published['screening_score'])


def verify_ridge(train, validation):
    train_x = np.array([[row[k] for k in KEY[1:]] for row in train])
    valid_x = np.array([[row[k] for k in KEY[1:]] for row in validation])
    domains = [sorted(set(column)) for column in train_x.T]
    encoded_train = np.hstack([train_x[:, i, None] == levels for i, levels in enumerate(domains)])
    encoded_valid = np.hstack([valid_x[:, i, None] == levels for i, levels in enumerate(domains)])
    target = np.array([float(row['V_true']) for row in train])
    centers = encoded_train.mean(axis=0)
    centered = encoded_train - centers
    y_mean = mean(target)
    coefs = np.linalg.solve(centered.T @ centered + np.eye(centered.shape[1]), centered.T @ (target - y_mean))
    independent = y_mean + (encoded_valid - centers) @ coefs
    exported = [float(row['V_hat_ridge']) for row in validation]
    if not np.allclose(independent, exported, rtol=1e-11, atol=1e-10):
        raise ValueError('Closed-form Ridge disagrees with archived predictions')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', default=DEFAULT_RUN, type=Path)
    parser.add_argument('--replay-dir', type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir
    metadata = json.loads((run_dir / 'results.json').read_text(encoding='utf-8'))
    assert metadata['features'] == list(KEY[1:])
    for label, source in [('train_csv', TRAIN), ('fold_csv', FOLDS)]:
        assert metadata['input_sha256'][label] == sha256(source.read_bytes()).hexdigest()

    predictions = read_rows(run_dir / 'oof_predictions.csv')
    official_rows = read_rows(TRAIN)
    assign = read_rows(FOLDS)
    assert len(predictions) == len(official_rows) == len(assign) == 11256
    groups = {}
    actual_gap = {}
    for raw, membership, row in zip(official_rows, assign, predictions):
        assert all(raw[k] == row[k] == membership[k] for k in KEY)
        assert row['fold'] == membership['fold'] == groups.setdefault((row['A'], row['B']), row['fold'])
        check_close(float(exact_violation(raw)), row['V_true'])
        assert all(isfinite(float(row[f'V_hat_{name}'])) for name in MODELS)
        actual_gap[row['id']] = Decimal(raw['gap'])
    assert len(groups) == 1608

    fold_table = read_rows(run_dir / 'fold_metrics.csv')
    paired = {(row['fold'], row['model']): row for row in fold_table}
    assert len(fold_table) == len(paired) == 15
    zero_gap_top_50 = {name: [] for name in ('ridge', 'random_forest')}
    for fold in ('1', '2', '3', '4', '5'):
        train = [row for row in predictions if row['fold'] != fold]
        held = [row for row in predictions if row['fold'] == fold]
        expected_median = median(float(row['V_true']) for row in train)
        assert float(held[0]['V_hat_median']) == expected_median
        assert len({row['V_hat_median'] for row in held}) == 1
        verify_ridge(train, held)
        for name in MODELS:
            published = paired[fold, name]
            assert int(published['training_rows']) == len(train)
            assert int(published['validation_rows']) == len(held)
            assert int(published['feature_columns']) == 111
            check_fold_scores(held, published, name)
        for name, counts in zero_gap_top_50.items():
            selected = sorted(held, key=lambda row: (float(row[f'V_hat_{name}']), int(row['id'])))[:50]
            counts.append(sum(actual_gap[row['id']] == 0 for row in selected))

    for name in MODELS:
        for metric in ('mae', 'screening_score', 'low_V_mae'):
            values = [float(row[metric]) for row in fold_table if row['model'] == name]
            record = metadata['models'][name]['metrics'][metric]
            check_close(mean(values), record['mean'])
            check_close(stdev(values), record['sd'])

    if args.replay_dir:
        assert ((args.replay_dir / 'oof_predictions.csv').read_bytes()
                == (run_dir / 'oof_predictions.csv').read_bytes()), 'OOF replay changed'
    print('Baseline audit passed: 02 only, 1,608 isolated groups, 11,256 OOF rows, 15 score records.')
    print('Independent Decimal labels, closed-form Ridge, median and screening metrics agree.')
    for name, counts in zero_gap_top_50.items():
        print(f'{name}: actual zero-gap samples in predicted Top-50, by fold: {counts}')
    if args.replay_dir:
        print('Replay OOF predictions match byte for byte, including the random forest.')


if __name__ == '__main__':
    main()
