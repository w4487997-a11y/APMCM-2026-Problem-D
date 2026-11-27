"""Cross-check the final model and score tables independently of the experiment runner."""

import argparse
import csv
import json
from collections import defaultdict
from hashlib import sha256
from math import isclose, isfinite, sqrt
from pathlib import Path
from statistics import mean

import joblib
import numpy as np
from scipy.stats import spearmanr
from threadpoolctl import threadpool_limits

from audit.baseline_check import exact_violation


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / '2026 APMCM Problem D' / 'date'
CORE = ('id', 'formula', 'A', 'B', 'X', 'a_eq_b')
EXPECTED = {'04': 3703, '07': 2704, '08': 8112, '11': 529, '12': 1587}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames), list(reader)


def check_metrics(raw_labels, archived, reference_table):
    known_ids = [row['id'] for row in raw_labels]
    require([row['id'] for row in archived] == known_ids, 'Misaligned evaluation rows')
    actual = {row['id']: float(row['V_true']) for row in archived}
    require(all(isclose(float(exact_violation(row)), actual[row['id']], abs_tol=1e-12)
                for row in raw_labels), 'Independent V computation differs')
    master = {row['id']: row for row in archived}
    gap = {row['id']: float(row['gap']) for row in raw_labels}
    folds = defaultdict(list)
    for row in archived:
        folds[row['split']].append(row['id'])
    for metric in reference_table:
        keys = folds[metric['split']]
        name = metric['model']
        pred = {k: float(master[k][f'V_hat_{name}']) for k in keys}
        true_rank = sorted(keys, key=lambda k: (actual[k], int(k)))
        predicted_rank = sorted(keys, key=lambda k: (pred[k], int(k)))
        error = {k: abs(actual[k] - pred[k]) for k in keys}
        values = {'mae': mean(error.values()), 'rmse': sqrt(mean(e * e for e in error.values())),
                  'low_V_mae': mean(error[k] for k in keys if actual[k] < 5)}
        if min(pred.values()) != max(pred.values()):
            values['spearman'] = spearmanr([actual[k] for k in keys], [pred[k] for k in keys]).statistic
        else:
            require(metric['spearman'] == '', 'Constant prediction has an invalid rank correlation')
        for count in (10, 25, 50, 100):
            selected = predicted_rank[:count]
            overlap = len(set(selected) & set(true_rank[:count]))
            values[f'top_{count}_overlap_count'] = overlap
            values[f'top_{count}_overlap_rate'] = overlap / count
            values[f'top_{count}_min_true_V'] = min(actual[k] for k in selected)
            values[f'top_{count}_true_zero_gap'] = sum(gap[k] == 0 for k in selected)
        values['screening_score'] = mean((values['top_25_overlap_rate'], values['top_50_overlap_rate']))
        require(all(isclose(value, float(metric[key]), rel_tol=1e-11, abs_tol=1e-11)
                    for key, value in values.items()), f'Metric mismatch for {name}, split {metric["split"]}')


def check_assembly(path):
    if not path.is_file():
        return 0
    _, rows = read(path)
    for row in rows:
        value = lambda key: float(row[key])
        form, vb, cb = (value(key) for key in ('pred_e_form', 'pred_vbm', 'pred_cbm'))
        fixed = 4 * (max(form - 0.21, 0)**2 + max(5.73 - vb, 0)**2 + max(cb - 4.5, 0)**2)
        if row['pred_gap']:
            gap = value('pred_gap')
            band_gap_penalty = 4 * max(1.4 - gap, gap - 3.1, 0)**2
        else:
            probability = value('pred_positive')
            if row['pred_gap_penalty_positive']:
                positive_penalty = max(value('pred_gap_penalty_positive'), 0)
            else:
                gap = max(value('pred_gap_positive'), 0)
                positive_penalty = 4 * max(1.4 - gap, gap - 3.1, 0)**2
            band_gap_penalty = (1 - probability) * 7.84 + probability * positive_penalty
        require(isclose(fixed + band_gap_penalty, value('V_hat'), rel_tol=1e-12, abs_tol=1e-12),
                f'Formula assembly mismatch at validation id {row["id"]}')
    return len(rows)


def check_selection(rows, frozen, metadata):
    direct = {name for name, spec in frozen['configurations'].items() if spec['variant'] in ('direct', 'tail')}
    ceiling = 1.05 * min(float(row['mae']) for row in rows if row['model'] in direct)
    eligible = [row for row in rows if row['model'] in frozen['cv_eligible'] and float(row['mae']) <= ceiling]
    peak = max(float(row['screening_score']) for row in eligible)
    shortlisted = [row for row in eligible if float(row['screening_score']) >= peak - 0.020000000001]
    winner = min(shortlisted, key=lambda row: (float(row['low_V_mae']), float(row['mae']), row['model']))
    require(winner['model'] == metadata['selection']['selected'], 'Independent selection picked a different model')


def audit(release, cv):
    manifest = json.loads((release / 'manifest.json').read_text(encoding='utf-8'))
    require(all(sha256((release / name).read_bytes()).hexdigest() == digest
                for name, digest in manifest['artifacts_sha256'].items()), 'Release SHA-256 mismatch')
    require(all(sha256((ROOT / name).read_bytes()).hexdigest() == digest
                for name, digest in manifest['code_sha256'].items()), 'Build source SHA-256 mismatch')
    freeze_file = cv / 'frozen_shortlist.json'
    require(sha256(freeze_file.read_bytes()).hexdigest() == manifest['frozen_shortlist_sha256'],
            'Frozen shortlist does not match release')
    freeze = json.loads(freeze_file.read_text(encoding='utf-8'))
    originals = {}
    for split, entry in manifest['inputs'].items():
        original = RAW / entry['file']
        require(sha256(original.read_bytes()).hexdigest() == entry['sha256'], f'Changed original {split}')
        fields, originals[split] = read(original)
        if split in EXPECTED:
            require(fields == CORE, 'Inference source contains unexpected fields')
    q1 = joblib.load(release / 'models' / 'q1_final.joblib')
    q23 = joblib.load(release / 'models' / 'q23_final.joblib')
    require(q1['train_splits'] == ['02'] and q23['train_splits'] == ['02', '03'], 'Incorrect training roles')
    for model in (q1, q23):
        require(model['name'] == manifest['selection']['selected'], 'Model name changes across releases')

    train_pairs = {(r['A'], r['B']) for r in originals['02']}
    valid_pairs = {(r['A'], r['B']) for r in originals['03']}
    holdout_pairs = {(r['A'], r['B']) for r in originals['04']}
    require(not (train_pairs & valid_pairs or train_pairs & holdout_pairs or valid_pairs & holdout_pairs),
            'Official pair roles overlap')
    scores, unique, merged = {}, {}, []
    for split, size in EXPECTED.items():
        src = originals[split]
        fields, pred = read(release / manifest['outputs'][split]['file'])
        model = q1 if split == '04' else q23
        require(fields == (*CORE, 'V_hat', 'source_pool', 'model_version'), f'Unexpected score schema {split}')
        require(len(pred) == len(src) == size and len({row['id'] for row in pred}) == size,
                f'Wrong score length or duplicate ID {split}')
        require(all(all(orig[field] == row[field] for field in CORE)
                    and row['source_pool'] == split and row['model_version'] == model['version']
                    for orig, row in zip(src, pred)), f'Source or row order mismatch for {split}')
        actual = [float(row['V_hat']) for row in pred]
        require(all(isfinite(value) and value >= 0 for value in actual), 'Invalid final score')
        comps = np.array([[row['A'], row['B'], row['X']] for row in src])
        reproduce = model['model'].predict(comps)
        require(np.allclose(actual, reproduce, rtol=1e-12, atol=1e-12), f'Saved-model replay failed {split}')
        scores[split] = {row['id']: row['V_hat'] for row in pred}
        if split != '04':
            for key, value in scores[split].items():
                require(unique.setdefault(key, value) == value, 'Cross-pool scores differ')
            merged.extend(pred)
    require(read(release / 'candidate_predictions.csv')[1] == merged, 'Combined pool order changed')
    require(set(scores['11']) == set(scores['07']) & set(scores['04']), 'Q2 blind pool mismatch')
    require(set(scores['12']) == set(scores['08']) & set(scores['04']), 'Q3 blind pool mismatch')

    _, val_predictions = read(release / 'validation_predictions.csv')
    _, val_metrics = read(release / 'validation_metrics.csv')
    _, oof_predictions = read(cv / 'oof_predictions.csv')
    _, folds = read(cv / 'fold_metrics.csv')
    assignment = read(ROOT / 'audit' / 'phase1' / 'folds_02.csv')[1]
    require(all(a['id'] == p['id'] and a['fold'] == p['split']
                for a, p in zip(assignment, oof_predictions)), 'CV assignment no longer matches phase 1')
    check_metrics(originals['02'], oof_predictions, folds)
    check_metrics(originals['03'], val_predictions, val_metrics)
    check_selection(val_metrics, freeze, manifest)
    physical_checks = check_assembly(release / 'validation_physics.csv')
    return {'status': 'PASS', 'validated_pool_sizes': EXPECTED, 'combined_pool_rows': len(merged),
            'validation_rows': len(val_predictions), 'cv_rows': len(oof_predictions),
            'cv_metric_records': len(folds), 'validation_metric_records': len(val_metrics),
            'independent_property_compositions': physical_checks,
            'checks': ['source/result hashes', 'fit-role metadata and group isolation',
                       'official row order and IDs', 'all-row saved-model replay',
                       'cross-pool score equality', 'independent score metrics and selection',
                       'separate formula assembly']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, default=ROOT / 'handoff' / 'v1')
    parser.add_argument('--cv', type=Path, default=ROOT / 'experiments' / 'q1_ablation_v1')
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        print(json.dumps(audit(args.release, args.cv), indent=2))


if __name__ == '__main__':
    main()
