"""Read-only cross-check of official CSVs and archived Q1 predictions."""

import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal
from itertools import combinations, product
from math import isfinite, sqrt
from pathlib import Path
from statistics import mean, median, quantiles


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / '2026 APMCM Problem D' / 'date'
ARCHIVE = ROOT / 'deliverable'
COMPOSITION = ('id', 'formula', 'A', 'B', 'X', 'a_eq_b')
PENALTIES = ('v_form', 'v_gap_low', 'v_gap_high', 'v_vbm', 'v_cbm')
LABEL_FIELDS = ('a_lat', 'volume', 'e_form', 'gap', 'gap_is_direct', 'vbm',
                'cbm', 'mu_b', 'fermi_level', 'fermi_width', *PENALTIES, 'V')
SIZE = {'02': 11256, '03': 3969, '04': 3703, '06': 15225,
        '07': 2704, '08': 8112, '11': 529, '12': 1587}
X_GROUPS = {'O3', 'NO2', 'FO2', 'N2O', 'N3', 'O2S', 'FNO'}
MICRO = 1_000_000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        return tuple(reader.fieldnames or ()), list(reader)


def verified_hashes(root, manifest):
    for name, expected in manifest.items():
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        require(actual == expected, f'SHA-256 mismatch: {name}')
    return len(manifest)


def micro(value):
    return int(Decimal(value) * MICRO)


def violation_numerators(formation, gap, vbm, cbm):
    # Compute squared distances to the closed admissible intervals in integer micro-eV.
    distances = (max(formation, 210_000) - 210_000,
                 1_400_000 - min(gap, 1_400_000),
                 max(gap, 3_100_000) - 3_100_000,
                 5_730_000 - min(vbm, 5_730_000),
                 max(cbm, 4_500_000) - 4_500_000)
    return tuple(distance**2 for distance in distances)


def label_check(rows):
    numerators, gaps, v_values, errors = [], [], [], []
    strict_count = 0
    max_term_error = 0
    max_stored_sum_error = 0
    denominator = 500_000**2
    for row in rows:
        values = [Decimal(row[name]) for name in LABEL_FIELDS]
        require(all(value.is_finite() for value in values), 'Nonfinite labeled field')
        formation, gap, vbm, cbm = (micro(row[k]) for k in ('e_form', 'gap', 'vbm', 'cbm'))
        terms = violation_numerators(formation, gap, vbm, cbm)
        strict_count += (formation < 210_000 and 1_400_000 < gap < 3_100_000
                         and vbm > 5_730_000 and cbm < 4_500_000)
        gaps.append(gap / MICRO)
        numerators.append(sum(terms))
        v_values.append(micro(row['V']) / MICRO)
        # Scale both sides to a common integer denominator before comparison.
        stored_terms = [micro(row[name]) for name in PENALTIES]
        errors.append(abs(sum(terms) - micro(row['V']) * (denominator // MICRO)) / denominator)
        max_term_error = max(max_term_error, *(abs(term - stored * (denominator // MICRO))
                             / denominator for term, stored in zip(terms, stored_terms)))
        max_stored_sum_error = max(max_stored_sum_error, abs(sum(stored_terms) - micro(row['V'])))

    positive_gaps = [gap for gap in gaps if gap > 0]
    require(min(gaps) >= 0 and min(v_values) >= 0, 'Negative gap or V')
    require(max(errors) <= 5e-5 and max_term_error <= 5e-5, 'Formula mismatch')
    require(max_stored_sum_error <= 2, 'Stored penalty sum mismatch')
    require(numerators.count(0) == v_values.count(0) == strict_count == 0,
            'Encountered a zero-violation or strictly feasible labeled row')
    return {'V_zero_stored': v_values.count(0), 'V_zero_recomputed': numerators.count(0),
            'strict': strict_count, 'V_min': min(v_values), 'V_median': median(v_values),
            'V_below': {str(t): sum(v < t for v in v_values) for t in (0.5, 1, 2, 5, 7.84)},
            'gap_zero': gaps.count(0), 'gap_positive': len(positive_gaps),
            'gap_positive_min_median_max': [min(positive_gaps), median(positive_gaps), max(positive_gaps)],
            'gap_in_closed_window': sum(1.4 <= gap <= 3.1 for gap in gaps),
            'gap_positive_by_X': dict(Counter(row['X'] for row, gap in zip(rows, gaps) if gap > 0)),
            'max_formula_error': max(errors), 'mean_formula_error': mean(errors),
            'max_formula_term_error': max_term_error,
            'max_stored_sum_error': max_stored_sum_error / MICRO}


def archived_metrics(validation):
    _, predictions = read_csv(ARCHIVE / 'results' / 'baseline_val_predictions.csv')
    expected = json.loads((ARCHIVE / 'results' / 'baseline_metrics.json').read_text(encoding='utf-8'))
    actual_keys = [(row['id'], Decimal(row['V_true'])) for row in predictions]
    source_keys = [(row['id'], Decimal(row['V'])) for row in validation]
    require(actual_keys == source_keys, 'Archived predictions do not align with official validation rows')
    ids = [int(row['id']) for row in predictions]
    truth = [float(row['V']) for row in validation]
    cutoff = quantiles(truth, n=10, method='inclusive')[0]
    low_indices = [i for i, value in enumerate(truth) if value <= cutoff]
    true_order = sorted(range(len(ids)), key=lambda i: (truth[i], ids[i]))
    result = {}
    for field, model in [('pred_median', 'baseline0_median'), ('pred_ridge', 'baseline1_ridge'),
                         ('pred_rf', 'baseline2_rf')]:
        scores = [float(row[field]) for row in predictions]
        require(all(map(isfinite, scores)), f'Nonfinite prediction: {model}')
        errors = [abs(y - score) for y, score in zip(truth, scores)]
        pred_order = sorted(range(len(ids)), key=lambda i: (scores[i], ids[i]))
        top = {}
        for k in (10, 25, 50, 100):
            selected = pred_order[:k]
            top[k] = {'overlap': len(set(selected) & set(true_order[:k])) / k,
                      'min_true_V': min(truth[i] for i in selected)}
        values = {'MAE': mean(errors), 'RMSE': sqrt(mean(e**2 for e in errors)),
                  'Low10_MAE': mean(errors[i] for i in low_indices), 'Top25_overlap': top[25]['overlap']}
        for metric, value in values.items():
            require(abs(value - expected['models'][model][metric]) <= 6e-7,
                    f'Archived metric mismatch: {model} {metric}')
        result[model] = {**values, 'top_k': top, 'negative_predictions': sum(v < 0 for v in scores)}
    return {'low_10_percent_threshold': cutoff, 'low_10_percent_rows': len(low_indices), 'models': result}


def main():
    public_manifest = json.loads((DATA / 'sha256_public.json').read_text(encoding='utf-8'))
    archive_manifest = json.loads((ARCHIVE / 'MANIFEST.json').read_text(encoding='utf-8'))['files']
    result = {'official_hashes_matched': verified_hashes(DATA, public_manifest),
              'archive_hashes_matched': verified_hashes(ARCHIVE, archive_manifest), 'files': {}}
    files, identities = {}, {}
    for name in (name for name in public_manifest if name.endswith('.csv')):
        code = name[:2]
        labeled = code in ('02', '03')
        fields, rows = read_csv(DATA / name)
        require(fields == COMPOSITION + (LABEL_FIELDS if labeled else ()), f'Unexpected schema: {name}')
        require(len(rows) == SIZE[code], f'Unexpected row count: {name}')
        require(all(None not in row and all(value and value.strip() for value in row.values())
                    for row in rows), f'Blank cell or malformed row: {name}')
        require(all(row['a_eq_b'] == str(int(row['A'] == row['B'])) for row in rows), f'Bad a_eq_b: {name}')
        key_map = {tuple(row[k] for k in ('A', 'B', 'X')): tuple(row[k] for k in COMPOSITION)
                   for row in rows}
        require(len(key_map) == len({row['id'] for row in rows}) == len(rows), f'Duplicate key: {name}')
        files[code], identities[code] = rows, key_map
        result['files'][code] = {'rows': len(rows), 'columns': len(fields),
                                 'A_eq_B': sum(row['a_eq_b'] == '1' for row in rows)}
        if labeled:
            result['files'][code].update(label_check(rows))

    groups = {code: {(a, b) for a, b, _ in identities[code]} for code in ('02', '03', '04')}
    require(all(not (groups[p] & groups[q]) for p, q in combinations(groups, 2)), 'Ordered pair leakage')
    full = identities['02'] | identities['03'] | identities['04']
    elements_a = {a for a, _, _ in full}
    elements_b = {b for _, b, _ in full}
    require(elements_a == elements_b and len(elements_a) == 52, 'Unexpected element domain')
    require(set(full) == set(product(elements_a, elements_b, X_GROUPS)), 'Incomplete full grid')
    require({int(row[0]) for row in full.values()} == set(range(len(full))), 'Invalid full-grid IDs')
    for code, n_groups in zip(groups, (1608, 567, 529)):
        require(len(groups[code]) == n_groups, f'Unexpected ordered pair count: {code}')
        require(set(identities[code]) == {(a, b, x) for a, b in groups[code] for x in X_GROUPS},
                f'Missing ordered pair/X cell: {code}')
    require({a for a, _ in groups['02']} == {b for _, b in groups['02']} == elements_a,
            'A or B elements absent in 02')
    require(identities['06'] == identities['02'] | identities['03'], '06 composition mismatch')
    for main_pool, blind_pool, classes in [('07', '11', {'NO2'}), ('08', '12', {'O3', 'NO2', 'FO2'})]:
        require(identities[main_pool] == {k: v for k, v in full.items() if k[2] in classes},
                f'Full-pool composition mismatch: {main_pool}')
        require(identities[blind_pool] == {k: v for k, v in identities['04'].items() if k[2] in classes},
                f'Blind-pool composition mismatch: {blind_pool}')
        pool_number = 2 if main_pool == '07' else 3
        _, old_pool = read_csv(ARCHIVE / 'results' / f'q{pool_number}_pool_predictions.csv')
        require([tuple(row[k] for k in COMPOSITION) for row in old_pool]
                == [tuple(row[k] for k in COMPOSITION) for row in files[main_pool]],
                f'Archived pool row alignment mismatch: {main_pool}')
    result['ordered_pairs'] = {code: len(pairs) for code, pairs in groups.items()}
    result['04_reverse_pair_in_02'] = sum(a != b and (b, a) in groups['02'] for a, b in groups['04'])
    result['archived_metrics'] = archived_metrics(files['03'])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
