"""Export V1.2 label checks and feature provenance for public files 02 and 03."""

import json

from audit.baseline_check import exact_violation
from audit.init_check import DATA, COMPOSITION, LABEL_FIELDS, X_GROUPS, verified_hashes
from q1.baselines import FEATURES, ROOT, sha256, write_table
from q1.experiments import official, write_json
from q1.violation import PENALTY_NAMES, PROPERTY_NAMES, penalty_terms


OUTPUT = ROOT / 'audit'


def checks(split, rows):
    records = []
    for row in rows:
        e, g, vb, cb = (float(row[k]) for k in PROPERTY_NAMES)
        values = penalty_terms(e, g, vb, cb)
        total = sum(values)
        if abs(total - float(exact_violation(row))) > 1e-12:
            raise ValueError(f'Independent V formula mismatch at id {row["id"]}')
        strict = (e < 0.21, 1.4 < g < 3.1, vb > 5.73, cb < 4.50)
        inclusive = (e <= 0.21, 1.4 <= g <= 3.1, vb >= 5.73, cb <= 4.50)
        readme = strict[0], inclusive[1], strict[2], strict[3]
        record = {'split': split, **{k: row[k] for k in ('id', *FEATURES, *PROPERTY_NAMES)},
                  'V_stored': row['V'], 'V_calc': total, 'V_abs_error': abs(total - float(row['V'])),
                  'gap_zero': int(g == 0)}
        for name, predicted in zip(PENALTY_NAMES, values):
            record[f'{name}_stored'] = row[name]
            record[f'{name}_calc'] = predicted
            record[f'{name}_abs_error'] = abs(predicted - float(row[name]))
        for scope, flags in (('strict', strict), ('inclusive', inclusive), ('readme_mixed', readme)):
            record.update({f'{scope}_{k}': int(flag) for k, flag in zip(PROPERTY_NAMES, flags)})
            record[f'{scope}_all'] = int(all(flags))
        records.append(record)
    fields = [f'{scope}_{name}' for scope in ('strict', 'inclusive', 'readme_mixed')
              for name in (*PROPERTY_NAMES, 'all')]
    summary = {field: sum(row[field] for row in records) for field in fields}
    summary.update(rows=len(rows), zero_gap=sum(r['gap_zero'] for r in records),
                   zero_v_stored=sum(float(r['V_stored']) == 0 for r in records),
                   zero_v_calc=sum(r['V_calc'] == 0 for r in records),
                   max_abs_v_difference=max(r['V_abs_error'] for r in records))
    assert summary['inclusive_all'] == summary['zero_v_calc']
    return records, summary


def main():
    official_hashes = json.loads((DATA / 'sha256_public.json').read_text(encoding='utf-8'))
    verified_hashes(DATA, official_hashes)
    recorded = json.loads((OUTPUT / 'init_results.json').read_text(encoding='utf-8'))
    roundoff = json.loads((OUTPUT / 'phase1' / 'results.json').read_text(encoding='utf-8'))
    split_checks, records, sources = {}, [], {}
    for split in ('02', '03'):
        raw, sources[split] = official(split, labeled=True)
        detail, split_checks[split] = checks(split, raw)
        records.extend(detail)
        split_checks[split]['rounding_audit'] = roundoff['stats'][split]['formula']

    paper = DATA.parent / '2026 APMCM Problem D.pdf'
    readme = 'README_数据集说明.md'
    source_docs = {'official_pdf': {'file': paper.relative_to(ROOT).as_posix(), 'sha256': sha256(paper),
                                    'sections': 'pp. 2–5'},
                   'official_readme': {'file': (DATA / readme).relative_to(ROOT).as_posix(),
                                       'sha256': official_hashes[readme], 'sections': [2, 4, 5, 7]}}
    shared = {
        'source_docs': source_docs,
        'verified_public_sha256': official_hashes,
        'observed_labeled_splits': split_checks,
        'scope': 'Only public labels 02 and 03. No reconstruction of protected holdout labels.',
        'organizer_aggregate_only': {
            'zero_v_full': 19, 'strict_target_full': 15, 'zero_v_pairs_locked_to_04': 19,
            'zero_v_by_X': {'O3': 6, 'NO2': 6, 'FO2': 6, 'N2O': 1, 'N3': 0, 'O2S': 0, 'FNO': 0},
            'zero_v_pool_counts_derived_from_public_aggregates': {'07': 6, '08': 18, '11': 6, '12': 18},
            'rounding_decimals': 6, 'documented_max_V_rounding_error': 1.02e-5,
            'split_hash_documented': {'holdout_supplement': '2026|<A>|<B>', 'validation_train': '2027|<A>|<B>'},
        },
    }

    write_table(OUTPUT / 'label_checks.csv', records)
    write_json(OUTPUT / 'q1_label_audit.json', {**shared, 'labeled_files': sources})
    write_json(OUTPUT / 'data_audit.json', {**shared, 'independent_initial_checks': recorded})
    write_json(OUTPUT / 'features_schema.json', {
        'labeled_columns': [*COMPOSITION, *LABEL_FIELDS],
        'composition_csv_columns': COMPOSITION, 'composition_only_sources': ['04', '06', '07', '08', '11', '12'],
        'final_model_input_order': FEATURES, 'sites_are_ordered': True, 'retain_equal_sites': True,
        'anion_labels': sorted(X_GROUPS), 'forbidden_predictors': [
            'id', 'formula', 'pool', 'source_pool', 'file membership', 'row number', 'split hash', *LABEL_FIELDS],
        'allowed_derived_ablation_only': ['A:X', 'B:X', 'A=B'], 'direct_use_of_a_eq_b': False,
        'preprocessing': 'Fit categorical encoder within each fit partition. All final models consume A/B/X.',
        'external_descriptors_used': False,
    })
    print(f'Wrote {len(records):,} public label checks and matched {len(official_hashes)} hashes.')


if __name__ == '__main__':
    main()
