"""Run the three fixed composition-only baselines on the public 02 grouped folds."""

import argparse
import csv
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
from statistics import mean, stdev
from tempfile import TemporaryDirectory
from time import perf_counter

import numpy as np
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits

from audit.init_check import DATA, read_csv
from q1.metrics import LOW_V_CUTOFF, SCREENING_BUDGETS, evaluate
from q1.violation import PROPERTY_NAMES, violation_degree


ROOT = Path(__file__).resolve().parents[1]
TRAIN_FILE = DATA / '02_castelli_train.csv'
FOLD_FILE = ROOT / 'audit' / 'phase1' / 'folds_02.csv'
OUTPUT = ROOT / 'experiments' / 'baseline_v1'
FEATURES = ('A', 'B', 'X')
SEED = 42
SCREENING_PRIMARY = (25, 50)
MAE_ALLOWANCE = 0.05


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs():
    official_checksums = json.loads((DATA / 'sha256_public.json').read_text(encoding='utf-8'))
    train_hash = sha256(TRAIN_FILE)
    if train_hash != official_checksums[TRAIN_FILE.name]:
        raise ValueError('Training CSV does not match the official SHA-256')

    _, rows = read_csv(TRAIN_FILE)
    fold_fields, assignment = read_csv(FOLD_FILE)
    identity = ('id', *FEATURES)
    if fold_fields != (*identity, 'fold') or len(assignment) != len(rows):
        raise ValueError('Fold assignment does not match the official training schema or row count')

    groups = {}
    folds = []
    for row, fold_row in zip(rows, assignment):
        if any(row[k] != fold_row[k] for k in identity):
            raise ValueError(f'Fold assignment misaligned at official id {row["id"]}')
        group = row['A'], row['B']
        fold = int(fold_row['fold'])
        if groups.setdefault(group, fold) != fold:
            raise ValueError(f'Ordered pair {group} appears in multiple folds')
        folds.append(fold)
    if set(folds) != {1, 2, 3, 4, 5}:
        raise ValueError('Expected five nonempty folds')
    ids = np.array([int(row['id']) for row in rows])
    if len(np.unique(ids)) != len(ids):
        raise ValueError('Duplicate training sample IDs')
    features = np.array([[row[name] for name in FEATURES] for row in rows])
    truth = np.array([violation_degree(*(float(row[k]) for k in PROPERTY_NAMES)) for row in rows])
    return ids, features, truth, np.array(folds), {'train_csv': train_hash, 'fold_csv': sha256(FOLD_FILE)}


def model_templates():
    return {
        'median': DummyRegressor(strategy='median'),
        'ridge': Ridge(alpha=1.0, solver='cholesky'),
        'random_forest': RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                                               random_state=SEED, n_jobs=1),
    }


def composition_encoder():
    return OneHotEncoder(sparse_output=False, handle_unknown='error')


def run_folds(ids, features, truth, assignment, templates):
    out_of_fold = {name: np.full(len(ids), np.nan) for name in templates}
    fold_results = []
    for fold in sorted(set(assignment)):
        validation = assignment == fold
        training = ~validation
        encoder = composition_encoder()
        start = perf_counter()
        fit_features = encoder.fit_transform(features[training])
        encoding_fit_time = perf_counter() - start
        start = perf_counter()
        validation_features = encoder.transform(features[validation])
        encoding_predict_time = perf_counter() - start
        counts = {'training_rows': int(sum(training)),
                  'validation_rows': int(sum(validation)),
                  'training_pairs': len(set(map(tuple, features[training, :2]))),
                  'validation_pairs': len(set(map(tuple, features[validation, :2]))),
                  'feature_columns': fit_features.shape[1]}

        for name, template in templates.items():
            model = clone(template)
            start = perf_counter()
            model.fit(fit_features, truth[training])
            fit_time = perf_counter() - start
            start = perf_counter()
            scores = model.predict(validation_features)
            predict_time = perf_counter() - start
            out_of_fold[name][validation] = scores
            report = evaluate(ids[validation], truth[validation], scores)
            top = report.pop('screening')
            flat_top = {f'top_{k}_{metric}': value for k, metrics in top.items()
                        for metric, value in metrics.items()}
            primary = mean(top[k]['overlap_rate'] for k in SCREENING_PRIMARY)
            fold_results.append({
                'model': name, 'fold': int(fold), **counts, **report, **flat_top,
                'screening_score': primary, 'negative_predictions': int(sum(scores < 0)),
                'encoding_fit_seconds': encoding_fit_time, 'encoding_predict_seconds': encoding_predict_time,
                'model_fit_seconds': fit_time, 'model_predict_seconds': predict_time,
            })
        print(f'Fold {fold}: {counts["validation_rows"]:,} validation rows, three baselines complete.', flush=True)

    if not all(np.isfinite(scores).all() for scores in out_of_fold.values()):
        raise ValueError('Out-of-fold predictions have missing or nonfinite scores')
    return out_of_fold, fold_results


def summarize(fold_results, names):
    summaries = {}
    for name in names:
        records = [entry for entry in fold_results if entry['model'] == name]
        metrics = (
            'mae', 'rmse', 'spearman', 'low_V_mae', 'top_true_1pct_mae', 'screening_score',
            *(f'top_{k}_{metric}' for k in SCREENING_BUDGETS for metric in ('overlap_rate', 'min_true_V')),
            'encoding_fit_seconds', 'encoding_predict_seconds', 'model_fit_seconds', 'model_predict_seconds',
        )
        stats = {}
        for metric in metrics:
            values = [entry[metric] for entry in records if entry[metric] is not None]
            stats[metric] = {
                'mean': mean(values) if values else None,
                'sd': stdev(values) if len(values) > 1 else None,
                'valid_folds': len(values),
            }
        summaries[name] = {'metrics': stats, 'negative_predictions': sum(r['negative_predictions'] for r in records)}

    reference = min(summaries, key=lambda name: summaries[name]['metrics']['mae']['mean'])
    best_mae = summaries[reference]['metrics']['mae']['mean']
    ceiling = best_mae * (1 + MAE_ALLOWANCE)
    comparison = []
    for name, entry in summaries.items():
        row = {f'{metric}_{key}': stats[key] for metric, stats in entry['metrics'].items()
               for key in ('mean', 'sd')}
        comparison.append({'model': name, 'within_tentative_mae_limit': row['mae_mean'] <= ceiling,
                           'relative_mae_vs_best': row['mae_mean'] / best_mae - 1,
                           'negative_predictions': entry['negative_predictions'], **row})
    rule = {'primary_screening_budgets': SCREENING_PRIMARY, 'tentative_mae_allowance': MAE_ALLOWANCE,
            'best_mae_reference': reference, 'best_mae': best_mae, 'tentative_mae_limit': ceiling}
    return summaries, comparison, rule


def write_table(path, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', default=OUTPUT, type=Path)
    out = parser.parse_args().out_dir.resolve()
    if out.exists():
        parser.error('Output directory already exists. Choose a new --out-dir.')
    ids, features, truth, assignment, hashes = load_inputs()
    templates = model_templates()
    start = perf_counter()
    with threadpool_limits(limits=1):
        scores, fold_results = run_folds(ids, features, truth, assignment, templates)
    total_seconds = perf_counter() - start
    summaries, comparison, rule = summarize(fold_results, templates)
    encoder_config = composition_encoder().get_params()
    encoder_config['dtype'] = np.dtype(encoder_config['dtype']).name

    provenance = {
        'run': 'baseline_v1', 'split': '02 five-group-fold cross-validation', 'features': FEATURES,
        'target': 'official V recomputed from public 02 physical labels', 'input_sha256': hashes,
        'estimator_seed': SEED, 'fold_manifest_seed': 42, 'low_V_cutoff_exclusive': LOW_V_CUTOFF,
        'screening_budgets': SCREENING_BUDGETS, 'prediction_postprocessing': 'none',
        'fit_threads': 1,
        'encoder': encoder_config,
        'estimator_configurations': {name: model.get_params() for name, model in templates.items()},
        'python': platform.python_version(), 'system': platform.platform(),
        'packages': {name: version(name) for name in ('numpy', 'scipy', 'scikit-learn', 'joblib', 'threadpoolctl')},
        'fit_and_evaluate_seconds': total_seconds, 'selection_diagnostics': rule,
        'count': {'predictions_per_model': len(ids), 'model_fits': len(fold_results)},
        'models': summaries,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=out.parent, prefix='.baseline-working-') as temporary:
        staged = Path(temporary) / 'run'
        staged.mkdir()
        (staged / 'results.json').write_text(json.dumps(provenance, indent=2, allow_nan=False) + '\n',
                                             encoding='utf-8')
        write_table(staged / 'fold_metrics.csv', fold_results)
        write_table(staged / 'summary.csv', comparison)
        with (staged / 'oof_predictions.csv').open('w', encoding='utf-8', newline='') as handle:
            writer = csv.writer(handle, lineterminator='\n')
            writer.writerow(('id', *FEATURES, 'fold', 'V_true', *(f'V_hat_{name}' for name in scores)))
            writer.writerows(zip(ids, *features.T, assignment, truth, *scores.values()))
        staged.rename(out)
    print(f'Wrote {len(fold_results)} fold/model evaluations to {out}.')


if __name__ == '__main__':
    main()
