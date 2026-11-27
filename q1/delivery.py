"""One held-out validation comparison and versioned final prediction handoff."""

import argparse
import csv
import json
import platform
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from audit.init_check import COMPOSITION, read_csv
from q1.baselines import FEATURES, FOLD_FILE, ROOT, sha256, write_table
from q1.experiments import (CV_DIR, MAE_ALLOWANCE, TIE_BAND, composition, metric_row, official,
                            positive_diagnostic, property_rows, write_json, write_predictions, xy)
from q1.surrogates import SPECS, fit_batch
from q1.violation import PROPERTY_NAMES


OUTPUT = ROOT / 'handoff' / 'v1'
POOL_OUTPUT_NAMES = {
    '04': 'q1_holdout_predictions.csv', '07': 'q2_pool_predictions.csv',
    '08': 'q3_pool_predictions.csv', '11': 'q2_blind_pool_predictions.csv',
    '12': 'q3_blind_pool_predictions.csv',
}
SCORE_FIELDS = (*COMPOSITION, 'V_hat', 'source_pool', 'model_version')


def freeze_model(metrics, freeze):
    best_direct_mae = min(row['mae'] for row in metrics if SPECS[row['model']].direct)
    limit = best_direct_mae * (1 + MAE_ALLOWANCE)
    eligible = [row for row in metrics
                if row['model'] in freeze['cv_eligible'] and row['mae'] <= limit]
    peak = max(row['screening_score'] for row in eligible)
    competitive = [row for row in eligible if peak - row['screening_score'] <= TIE_BAND + 1e-12]
    winner = min(competitive, key=lambda row: (row['low_V_mae'], row['mae'], row['model']))
    return {'selected': winner['model'], 'validation_best_direct_mae': best_direct_mae,
            'validation_mae_limit': limit, 'validation_eligible': [r['model'] for r in eligible],
            'validation_tie_band': TIE_BAND, 'within_screening_tie_band': [r['model'] for r in competitive]}


def validate_candidates(rows, models, timing):
    comp, targets, truth = xy(rows)
    ids = np.array([int(row['id']) for row in rows])
    scores, metrics, components, diagnose = {}, [], [], []
    for name, model in models.items():
        start = perf_counter()
        pred, raw, gap, parts = model.predict_details(comp)
        stats = metric_row(name, '03', ids, truth, targets['gap'], pred, raw,
                           (*timing[name], perf_counter() - start))
        scores[name] = pred
        metrics.append(stats)
        for row_index, sample_id in enumerate(ids):
            if not model.spec.direct:
                result = {'id': sample_id, 'model': name, **{
                    f'true_{key}': values[row_index] for key, values in targets.items()}}
                result.update({f'pred_{key}': parts[key][row_index] if key in parts else None
                               for key in ('e_form', 'vbm', 'cbm', 'positive', 'gap_positive',
                                           'gap_penalty_positive')})
                result['pred_gap'] = gap[row_index] if gap is not None else None
                result['V_hat'] = pred[row_index]
                components.append(result)
        diagnose.extend(property_rows(name, '03', targets, truth, gap, parts))
        if 'positive' in parts and 'gap_positive' in parts:
            diagnose.append({'model': name, **positive_diagnostic('03', targets['gap'], truth, parts)})
    return truth, scores, metrics, components, diagnose


def checked_union(pools):
    unique = {}
    for rows in pools:
        for row in rows:
            identity = tuple(row[key] for key in COMPOSITION)
            key = row['id']
            if key in unique and tuple(unique[key][field] for field in COMPOSITION) != identity:
                raise ValueError(f'Conflicting official rows for id {key}')
            unique[key] = row
    return unique


def scored_rows(source, scores, model_version, pool):
    return [{**{key: row[key] for key in COMPOSITION},
             'V_hat': format(float(scores[row['id']]), '.17g'),
             'source_pool': pool, 'model_version': model_version} for row in source]


def score_pool_group(bundled_model, pools):
    unique = checked_union(pools.values())
    model = bundled_model['model']
    begin = perf_counter()
    scores, raw, _, _ = model.predict_details(composition(list(unique.values())))
    seconds = perf_counter() - begin
    if not np.isfinite(scores).all() or (scores < 0).any():
        raise ValueError('Invalid inference scores')
    by_id = dict(zip(unique, scores))
    raw_by_id = dict(zip(unique, raw))
    outputs, summaries = {}, {}
    for pool, source in pools.items():
        outputs[pool] = scored_rows(source, by_id, bundled_model['version'], pool)
        ordered = sorted(outputs[pool], key=lambda row: (float(row['V_hat']), int(row['id'])))
        values = [float(row['V_hat']) for row in ordered]
        summaries[pool] = {
            'rows': len(source), 'min_score': values[0], 'max_score': values[-1],
            'first_to_second_gap': values[1] - values[0], 'tied_minima': values.count(values[0]),
            'top25_boundary_ties': values.count(values[24]), 'top50_boundary_ties': values.count(values[49]),
            'raw_negative_count': sum(raw_by_id[r['id']] < 0 for r in source),
            'lowest_proxy_candidates': [{k: row[k] for k in ('id', *FEATURES, 'V_hat')} for row in ordered[:5]],
        }
    return outputs, summaries, {'unique_rows': len(unique), 'pool_union_predict_seconds': seconds}


def bundled(name, prefix, model, train_splits, timing):
    return {'version': f'{prefix}_final_v1_{name}', 'name': name, 'model': model,
            'train_splits': train_splits, 'features': FEATURES,
            'encoder_fit_seconds': timing[0], 'head_fit_seconds': timing[1]}


def build(cv_dir, output):
    frozen_file = cv_dir / 'frozen_shortlist.json'
    freeze = json.loads(frozen_file.read_text(encoding='utf-8'))
    assert freeze['configurations'] == {k: asdict(v) for k, v in SPECS.items()}
    assert freeze['fold_sha256'] == sha256(FOLD_FILE)
    assert freeze['validation_mae_slack'] == MAE_ALLOWANCE and freeze['validation_screening_tie_band'] == TIE_BAND
    train, train_info = official('02', labeled=True)
    assert train_info == freeze['train']
    x, props, truth = xy(train)
    candidates, times = fit_batch(x, props, truth, freeze['shortlist'], seed=freeze['seed'])
    validation, validation_info = official('03', labeled=True)
    assert not ({(r['A'], r['B']) for r in train} & {(r['A'], r['B']) for r in validation})
    val_truth, val_scores, val_metrics, val_properties, val_diagnostics = validate_candidates(
        validation, candidates, times)
    decision = freeze_model(val_metrics, freeze)
    selected = decision['selected']
    q1 = bundled(selected, 'q1', candidates[selected], ['02'], times[selected])
    joint, joint_props, joint_v = xy(train + validation)
    downstream, downstream_times = fit_batch(joint, joint_props, joint_v, [selected], seed=freeze['seed'])
    q23 = bundled(selected, 'q23', downstream[selected], ['02', '03'], downstream_times[selected])
    sources = {}
    for pool in POOL_OUTPUT_NAMES:
        sources[pool] = official(pool, labeled=False)
    predictions = {}
    stats = {}
    timing = {}
    for bundle, codes in ((q1, ('04',)), (q23, ('07', '08', '11', '12'))):
        scored, details, cost = score_pool_group(bundle, {code: sources[code][0] for code in codes})
        predictions.update(scored)
        stats.update(details)
        timing[bundle['version']] = cost

    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent, prefix='.delivery-') as temporary:
        stage = Path(temporary) / 'release'
        stage.mkdir()
        model_dir = stage / 'models'
        model_dir.mkdir()
        joblib.dump(q1, model_dir / 'q1_final.joblib', compress=3)
        joblib.dump(q23, model_dir / 'q23_final.joblib', compress=3)
        for pool, filename in POOL_OUTPUT_NAMES.items():
            write_table(stage / filename, predictions[pool])
        combined = [row for code in ('07', '08', '11', '12') for row in predictions[code]]
        write_table(stage / 'candidate_predictions.csv', combined)
        write_predictions(stage / 'validation_predictions.csv', validation, ['03'] * len(validation),
                          val_truth, val_scores)
        write_table(stage / 'validation_metrics.csv', val_metrics)
        if val_properties:
            write_table(stage / 'validation_physics.csv', val_properties)
        write_json(stage / 'validation_property_metrics.json', val_diagnostics)
        metadata = {
            'version': 'v1', 'features': FEATURES, 'seed': freeze['seed'],
            'formula': '2026 APMCM Problem D, five squared hinge penalties, scale 0.5 eV',
            'frozen_shortlist_sha256': sha256(frozen_file), 'shortlist': freeze['shortlist'],
            'selected_spec': asdict(SPECS[selected]), 'selection': decision,
            'inputs': {'02': train_info, '03': validation_info, **{k: v[1] for k, v in sources.items()}},
            'model_training': {b['version']: {k: v for k, v in b.items() if k != 'model'} for b in (q1, q23)},
            'outputs': {k: {'file': f, **stats[k]} for k, f in POOL_OUTPUT_NAMES.items()},
            'inference_timing': timing, 'combined_rows': len(combined),
            'score_columns': SCORE_FIELDS, 'python': platform.python_version(),
            'packages': {name: version(name) for name in ('numpy', 'scipy', 'scikit-learn', 'joblib', 'threadpoolctl')},
            'code_sha256': {str(path.relative_to(ROOT)).replace('\\', '/'): sha256(path)
                            for path in sorted((ROOT / 'q1').glob('*.py'))},
            'artifacts_sha256': {path.relative_to(stage).as_posix(): sha256(path)
                                 for path in sorted(stage.rglob('*')) if path.is_file()},
        }
        write_json(stage / 'manifest.json', metadata)
        stage.rename(output)
    print(f'Frozen model: {selected}. Wrote 04 and four Q2/Q3 pools to {output}.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cv-dir', type=Path, default=CV_DIR)
    parser.add_argument('--out-dir', type=Path, default=OUTPUT)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    if out.exists():
        parser.error('Output directory already exists.')
    with threadpool_limits(limits=1):
        build(args.cv_dir, out)


if __name__ == '__main__':
    main()
