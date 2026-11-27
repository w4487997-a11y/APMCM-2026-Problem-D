"""Independently check the V1.2 supplements without altering the frozen v1 release."""

import argparse
import json
import subprocess
from collections import Counter
from hashlib import sha256
from math import isclose, isfinite
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from audit.baseline_check import exact_violation
from audit.final_check import CORE, EXPECTED, RAW, ROOT, audit, check_assembly, check_metrics, read, require


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def check_contract(release):
    manifest = json.loads((release / 'manifest.json').read_text(encoding='utf-8'))
    frozen = ROOT / 'handoff' / 'v1'
    require((release / 'manifest.json').read_bytes() == (ROOT / 'handoff' / 'manifest.json').read_bytes(),
            'Canonical and versioned handoff manifest differ')
    require(manifest['frozen_manifest_sha256'] == digest(frozen / 'manifest.json'), 'Frozen manifest changed')
    require(manifest['planning_sha256'] == digest(ROOT / manifest['planning_file']), 'V1.2 plan hash mismatch')
    require(manifest['primary_pools'] == {'Q2': '07', 'Q3': '08'}, 'Unexpected full-pool defaults')
    combined, by_id = [], {}
    for pool, count in EXPECTED.items():
        entry = manifest['outputs'][pool]
        path = release / entry['file']
        columns, exported = read(path)
        _, old_rows = read(frozen / entry['frozen_file'])
        _, official_rows = read(RAW / manifest['inputs'][pool]['file'])
        require(columns == (*CORE, 'V_hat', 'pool', 'model_version', 'source_pool'), f'Wrong schema for {pool}')
        require(len(exported) == len(old_rows) == len(official_rows) == count, f'Wrong length for {pool}')
        require(entry['sha256'] == digest(path), f'Invalid exported table hash for {pool}')
        for row, previous, original in zip(exported, old_rows, official_rows):
            require({k: row[k] for k in previous} == previous and row['pool'] == row['source_pool'] == pool,
                    f'Frozen prediction or pool changed at ID {row["id"]}')
            require(all(row[k] == original[k] for k in CORE), 'Original columns or row order changed')
            if pool != '04':
                require(by_id.setdefault(row['id'], row['V_hat']) == row['V_hat'], 'Cross-pool score inconsistency')
        if pool != '04':
            combined.extend(exported)
    combined_file = release / manifest['combined_output']['file']
    require(read(combined_file)[1] == combined and digest(combined_file) == manifest['combined_output']['sha256'],
            'Combined candidate file hash or order differs')
    require(all(digest(frozen / path) == expected for path, expected in manifest['models'].items()),
            'Frozen model hash changed')

    source = manifest['source_snapshot']
    bundle = release / source['file']
    require(digest(bundle) == source['bundle_sha256'], 'Local source bundle hash mismatch')
    heads = subprocess.check_output(['git', 'bundle', 'list-heads', str(bundle)], text=True).strip()
    require(heads == f'{source["commit"]} refs/heads/{source["branch"]}', 'Wrong commit in source snapshot')
    require(all(digest(ROOT / path) == expected for path, expected in source['files'].items()),
            'Current code does not match source snapshot')
    return {'pool_sizes': EXPECTED, 'prediction_values_unchanged': True, 'combined_rows': len(combined),
            'source_commit': source['commit']}


def check_labels():
    report = json.loads((ROOT / 'audit' / 'q1_label_audit.json').read_text(encoding='utf-8'))
    require(all(digest(RAW / name) == expected for name, expected in report['verified_public_sha256'].items()),
            'Official file hash mismatch')
    _, computed = read(ROOT / 'audit' / 'label_checks.csv')
    for key, split in (('02', 'train'), ('03', 'val')):
        _, source = read(RAW / f'{key}_castelli_{split}.csv')
        checks = [r for r in computed if r['split'] == key]
        require(len(source) == len(checks), f'Label audit length changed for {key}')
        counts = Counter()
        for a, b in zip(source, checks):
            require(a['id'] == b['id'] and isclose(float(exact_violation(a)), float(b['V_calc']), abs_tol=1e-12),
                    'Raw label and row-wise audit differ')
            f, g, vb, cb = (float(a[k]) for k in ('e_form', 'gap', 'vbm', 'cbm'))
            for k, value in zip(('e_form', 'gap', 'vbm', 'cbm'), (f < 0.21, 1.4 < g < 3.1, vb > 5.73, cb < 4.50)):
                require(int(b[f'strict_{k}']) == int(value), f'Wrong strict label for {k}')
                counts[f'strict_{k}'] += value
        require(all(report['observed_labeled_splits'][key][name] == value for name, value in counts.items()),
                f'Single-property totals do not agree for {key}')
    return len(computed)


def check_evidence(supplement):
    _, raw = read(RAW / '03_castelli_val.csv')
    _, all_preds = read(supplement / 'validation_predictions_03.csv')
    _, scores = read(supplement / 'model_comparison.csv')
    require(len(scores) == 12, 'Supplement must cover 12 models')
    check_metrics(raw, all_preds, scores)
    _, prior = read(ROOT / 'handoff' / 'v1' / 'validation_predictions.csv')
    require(all(all(p[k] == row[k] for k in p) for p, row in zip(prior, all_preds)),
            'Score text of previously frozen finalists changed')
    _, gap = read(supplement / 'gap_ablation.csv')
    require({r['model'] for r in gap} == {'hgb_indirect', 'hgb_gap_hard', 'hgb_gap_soft', 'hgb_gap_mix',
                                          'hgb_gap_expected'}, 'The 03 gap panel is incomplete')
    terms = check_assembly(supplement / 'val_physics_predictions.csv')
    require(terms == len(raw) * 6, 'Missing per-row property predictions')

    _, base_preds = read(supplement / 'val_predictions_baseline.csv')
    require([r['id'] for r in base_preds] == [r['id'] for r in raw], 'Baseline output ID/row mismatch')
    comp = np.array([[r['A'], r['B'], r['X']] for r in raw])
    for name in ('median', 'ridge', 'random_forest', 'hgb_direct'):
        artifact = joblib.load(supplement / 'models' / 'baseline' / f'{name}.joblib')
        v = [float(r[f'V_hat_{name}']) for r in base_preds]
        require(artifact['train_splits'] == ['02'] and np.allclose(artifact['model'].predict(comp), v, atol=1e-12),
                '03 baseline artifact does not reproduce its saved predictions')
    _, physical = read(supplement / 'val_physics_predictions.csv')
    ordinary = [r for r in physical if r['model'] == 'hgb_indirect']
    for field in ('e_form', 'gap', 'vbm', 'cbm'):
        artifact = joblib.load(supplement / 'models' / 'four_properties' / f'{field}.joblib')
        predicted = artifact['estimator'].predict(artifact['encoder'].transform(comp))
        column = 'pred_gap_raw' if field == 'gap' else f'pred_{field}'
        require(artifact['train_splits'] == ['02']
                and np.allclose(predicted, [float(r[column]) for r in ordinary], atol=1e-12),
                f'Four-property head mismatch for {field}')
    temporary = supplement / 'baseline_v0'
    ridge = joblib.load(temporary / 'baseline_v0.joblib')
    require(ridge['train_splits'] == ['02', '03'], 'Wrong temporary baseline training roles')
    for filename, known in (('q2_pool_predictions.csv', 2704), ('q3_pool_predictions.csv', 8112)):
        _, rows = read(temporary / filename)
        require(len(rows) == known and all(r['model_version'] == 'baseline_v0'
                                           and isfinite(float(r['V_hat'])) for r in rows),
                'Unlabeled or incomplete temporary baseline')
        comp = np.array([[r['A'], r['B'], r['X']] for r in rows])
        require(np.allclose(ridge['model'].predict(comp), [float(r['V_hat']) for r in rows], atol=1e-12),
                'Temporary baseline rescore disagrees')
    _, stability = read(supplement / 'stability.csv')
    seed_tests = [r for r in stability if r['scenario'] == 'estimator_seed']
    group_tests = [r for r in stability if r['scenario'] == 'group_assignment']
    required = {'42', '1729', '31415'}
    require(len(seed_tests) == 30 and {r['estimator_seed'] for r in seed_tests} == required
            and len(group_tests) == 20 and {r['group_seed'] for r in group_tests} == required - {'42'},
            'Incomplete stability pass')
    return {'validation_rows': len(raw), 'validation_model_count': len(scores), 'property_rows': terms,
            'stability_fold_records': len(stability), 'prior_finalist_scores_equal': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'audit' / 'v12_acceptance.json')
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        frozen = audit(ROOT / 'handoff' / 'v1', ROOT / 'experiments' / 'q1_ablation_v1')
        final = {'status': 'PASS', 'frozen_release': frozen, 'label_rows': check_labels(),
                 'supplement': check_evidence(ROOT / 'experiments' / 'q1_v12'),
                 'contract': check_contract(ROOT / 'handoff' / 'v1_2'),
                 'pending': ['Independent human team review and acceptance',
                             'Logged-in official portal: dedicated 04 format or upload field']}
    args.out.write_text(json.dumps(final, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(final, indent=2))


if __name__ == '__main__':
    main()
