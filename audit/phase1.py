"""Audit public Q1 labels and prepare a train-only grouped fold manifest."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from itertools import combinations
from math import isfinite
from pathlib import Path
from statistics import mean, median, quantiles

from audit.init_check import DATA, LABEL_FIELDS, read_csv, require, verified_hashes
from audit.init_check import micro, violation_numerators
from q1.metrics import LOW_V_CUTOFF
from q1.violation import PENALTY_NAMES, PROPERTY_NAMES, deviations, penalty_terms
from q1.violation import squared_penalty, strictly_feasible


OUTPUT = Path(__file__).resolve().parent / 'phase1'
LABELED_SPLITS = ('02', '03')
SPLIT_COUNTS = {'02': 1608, '03': 567, '04': 529}
TAIL_LIMITS = (0.5, 1.0, 2.0, LOW_V_CUTOFF, 7.84)
ROUNDING = 0.5e-6
COMPARISON_EPS = 1e-12
FOLD_SEED = 42
FOLD_COUNT = 5


def ab_pair(row):
    return row['A'], row['B']


def distribution(values):
    ordered = sorted(values)
    cutoffs = quantiles(ordered, n=100, method='inclusive')
    return dict(min=ordered[0], p01=cutoffs[0], median=median(ordered),
                p99=cutoffs[98], max=ordered[-1])


def group_summary(rows):
    return {'rows': len(rows),
            'gap_zero': sum(row['gap'] == 0 for row in rows),
            'gap_positive': sum(row['gap'] > 0 for row in rows),
            'gap_in_closed_window': sum(1.4 <= row['gap'] <= 3.1 for row in rows),
            'V_lt_5': sum(row['V'] < LOW_V_CUTOFF for row in rows)}


def formula_audit(raw_rows):
    """Verify every archived penalty against six-decimal input and output intervals."""
    terms_error = {name: 0.0 for name in PENALTY_NAMES}
    bounds = {'V': 0.0, **terms_error}
    exceed = Counter({name: 0 for name in (*PENALTY_NAMES, 'V', 'stored_sum')})
    absolute_errors = []
    stored_zero = computed_zero = strict_count = 0
    sum_error = exact_error = 0.0
    for row in raw_rows:
        properties = tuple(float(row[name]) for name in PROPERTY_NAMES)
        terms = penalty_terms(*properties)
        exact_terms = violation_numerators(*(micro(row[name]) for name in PROPERTY_NAMES))
        exact_error = max(exact_error, *(abs(t - e / 500_000**2) for t, e in zip(terms, exact_terms)))
        signed = deviations(*properties)
        lo = [squared_penalty(d - ROUNDING) for d in signed]
        hi = [squared_penalty(d + ROUNDING) for d in signed]

        stored = [float(row[name]) for name in PENALTY_NAMES]
        truth = float(row['V'])
        for name, observed, value, lower, upper in zip(
            (*PENALTY_NAMES, 'V'), [*stored, truth], [*terms, sum(terms)],
            [*lo, sum(lo)], [*hi, sum(hi)],
        ):
            distance = abs(observed - value)
            bounds[name] = max(bounds[name], value - lower + ROUNDING, upper + ROUNDING - value)
            exceed[name] += not (lower - ROUNDING - COMPARISON_EPS
                                 <= observed <= upper + ROUNDING + COMPARISON_EPS)
            if name == 'V':
                absolute_errors.append(distance)
            else:
                terms_error[name] = max(terms_error[name], distance)

        stored_sum_difference = abs(truth - sum(stored))
        sum_error = max(sum_error, stored_sum_difference)
        exceed['stored_sum'] += stored_sum_difference > 6 * ROUNDING + COMPARISON_EPS
        stored_zero += truth == 0
        computed_zero += sum(terms) == 0
        strict_count += strictly_feasible(*properties)
    require(exact_error <= COMPARISON_EPS, 'Independent integer penalty implementation disagrees')
    require(not any(exceed.values()), f'Label outside theoretical rounding interval: {dict(exceed)}')
    return {'stored_zero': stored_zero, 'recomputed_zero': computed_zero, 'strict': strict_count,
            'max_abs_V_error': max(absolute_errors), 'mean_abs_V_error': mean(absolute_errors),
            'max_abs_term_errors': terms_error, 'max_rounding_bounds': bounds,
            'outside_rounding_interval': dict(exceed), 'max_abs_stored_sum_error': sum_error,
            'max_abs_error_vs_independent_integer_terms': exact_error}


def split_diagnostics(raw_rows, rows):
    require(all(isfinite(row[name]) for name in LABEL_FIELDS for row in rows), 'Nonfinite label')
    gap_positive = [r for r in rows if r['gap'] > 0]
    gap_zero = [r for r in rows if r['gap'] == 0]
    tail_rows = [r for r in rows if r['V'] < LOW_V_CUTOFF]
    x_groups = sorted({r['X'] for r in rows})
    by_x = {x: group_summary([r for r in rows if r['X'] == x]) for x in x_groups}
    require(all(row['gap_is_direct'] in (0, 1) for row in rows), 'Nonbinary direct-gap flag')
    require(all(row['a_lat'] > 0 and row['volume'] > 0 and row['gap'] >= 0 and row['V'] >= 0
                and row['fermi_width'] >= 0 for row in rows), 'Unexpected negative physical magnitude')
    require(all(row[p] >= 0 for p in PENALTY_NAMES for row in rows), 'Negative penalty')
    gap_residual = [row['vbm'] - row['cbm'] - row['gap'] for row in gap_positive]
    volume_residual = [abs(row['volume'] - row['a_lat'] ** 3) for row in rows]
    volume_outside = 0
    for row in rows:
        lower = (row['a_lat'] - ROUNDING) ** 3 - ROUNDING
        upper = (row['a_lat'] + ROUNDING) ** 3 + ROUNDING
        volume_outside += not lower - COMPARISON_EPS <= row['volume'] <= upper + COMPARISON_EPS

    return {
        **group_summary(rows),
        'formula': formula_audit(raw_rows),
        'ranges': {name: distribution([row[name] for row in rows]) for name in LABEL_FIELDS},
        'V_below': {str(cutoff): sum(row['V'] < cutoff for row in rows) for cutoff in TAIL_LIMITS},
        'summary_by_X': by_x,
        'positive_gap_eV': distribution([row['gap'] for row in gap_positive]),
        'positive_gap_on_0p1_eV_grid': sum(abs(row['gap'] * 10 - round(row['gap'] * 10)) < 1e-10
                                           for row in gap_positive),
        'gap_zero_equal_edges': sum(row['vbm'] == row['cbm'] for row in gap_zero),
        'gap_zero_with_direct_flag': sum(row['gap_is_direct'] == 1 for row in gap_zero),
        'gap_positive_with_direct_flag': sum(row['gap_is_direct'] == 1 for row in gap_positive),
        'positive_gap_vbm_minus_cbm_minus_gap_eV': {
            **distribution(gap_residual), 'abs_gt_2e_minus_6': sum(abs(e) > 2e-6 for e in gap_residual)},
        'vbm_lt_cbm': sum(row['vbm'] < row['cbm'] for row in rows),
        'cell_volume': {'max_abs_residual_A3': max(volume_residual), 'outside_rounding_interval': volume_outside},
        'duplicate_formula_strings': len(rows) - len({row['formula'] for row in rows}),
        'V_lt_5_penalties': {
            name: {'nonzero': sum(row[name] > 0 for row in tail_rows),
                   'sum': sum(row[name] for row in tail_rows)}
            for name in PENALTY_NAMES},
    }


def train_folds(train):
    pairs = {ab_pair(row) for row in train}
    ordered = sorted(pairs, key=lambda pair: hashlib.sha256(
        f'{FOLD_SEED}|{pair[0]}|{pair[1]}'.encode()).digest())
    assignment = {pair: index % FOLD_COUNT + 1 for index, pair in enumerate(ordered)}
    fold_rows = {fold: [] for fold in range(1, FOLD_COUNT + 1)}
    for row in train:
        fold_rows[assignment[ab_pair(row)]].append(row)
    all_x = sorted({row['X'] for row in train})
    summaries = {}
    for fold, rows in fold_rows.items():
        valid_pairs = {ab_pair(row) for row in rows}
        fit = [row for row in train if assignment[ab_pair(row)] != fold]
        require(len(rows) == len(valid_pairs) * len(all_x), f'Missing pair/X cell in fold {fold}')
        require(not valid_pairs & {ab_pair(row) for row in fit}, f'Pair overlap in fold {fold}')
        require(all({row[site] for row in rows} <= {row[site] for row in fit} for site in ('A', 'B')),
                f'Unseen element in fold {fold}')
        summaries[fold] = {
            **group_summary(rows), 'pairs': len(valid_pairs),
            'training_rows': len(fit), 'training_pairs': len(pairs) - len(valid_pairs),
            'positive_gap_by_X': {x: sum(row['X'] == x and row['gap'] > 0 for row in rows) for x in all_x},
        }
    require(sum(len(rows) for rows in fold_rows.values()) == len(train), 'Fold coverage mismatch')
    return assignment, summaries


def write_csv(path, columns, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(columns)
        writer.writerows(rows)


def load_public_inputs():
    manifest = json.loads((DATA / 'sha256_public.json').read_text(encoding='utf-8'))
    checked = verified_hashes(DATA, manifest)
    names = {name[:2]: name for name in manifest if name.endswith('.csv')}
    raw = {split: read_csv(DATA / names[split])[1] for split in SPLIT_COUNTS}
    numeric = {split: [{**row, **{name: float(row[name]) for name in LABEL_FIELDS}} for row in raw[split]]
               for split in LABELED_SPLITS}
    return raw, numeric, manifest, checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', default=OUTPUT, type=Path)
    out = parser.parse_args().out_dir
    raw, numeric, manifest, checked = load_public_inputs()
    pairs = {split: {ab_pair(r) for r in rows} for split, rows in raw.items()}
    require({split: len(p) for split, p in pairs.items()} == SPLIT_COUNTS, 'Unexpected official pair counts')
    require(all(not pairs[l] & pairs[r] for l, r in combinations(pairs, 2)), 'Official pair overlap')
    assignment, folds = train_folds(numeric['02'])
    splits = {split: split_diagnostics(raw[split], numeric[split]) for split in LABELED_SPLITS}
    results = {'official_sha256_checks': checked, 'input_sha256': manifest,
               'split_pair_counts': SPLIT_COUNTS, 'fold_seed': FOLD_SEED, 'folds_02': folds,
               'stats': splits}
    out.mkdir(parents=True, exist_ok=True)
    (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    write_csv(out / 'folds_02.csv', ('id', 'A', 'B', 'X', 'fold'),
              ((row['id'], *ab_pair(row), row['X'], assignment[ab_pair(row)]) for row in raw['02']))
    group_fields = ('rows', 'gap_zero', 'gap_positive', 'gap_in_closed_window', 'V_lt_5')
    write_csv(out / 'stats_by_x.csv', ('split', 'X', *group_fields),
              ((split, x, *(values[name] for name in group_fields)) for split, stats in splits.items()
               for x, values in stats['summary_by_X'].items()))
    print(f'Verified {checked} official hashes, {sum(len(rows) for rows in numeric.values())} label rows, '
          f'and {FOLD_COUNT} disjoint validation folds in 02. Results saved to {out}.')


if __name__ == '__main__':
    main()
