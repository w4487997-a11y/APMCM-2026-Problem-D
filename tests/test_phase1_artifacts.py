"""Cross-check saved results against public CSVs without importing the audit builder."""

import csv
import json
import unittest
from collections import Counter
from decimal import Decimal as D
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '2026 APMCM Problem D' / 'date'
OUTPUT = ROOT / 'audit' / 'phase1'


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


class SavedAuditTests(unittest.TestCase):
    def test_formula_summary_against_decimal_oracle(self):
        stats = json.loads((OUTPUT / 'results.json').read_text(encoding='utf-8'))['stats']
        for split, name in [('02', '02_castelli_train.csv'), ('03', '03_castelli_val.csv')]:
            worst_difference, strict_count, zero_count = D(0), 0, 0
            for record in rows(SOURCE / name):
                e, g, vb, cb = [D(record[k]) for k in ('e_form', 'gap', 'vbm', 'cbm')]
                total = (
                    4 * max(e - D('.21'), 0) ** 2
                    + 4 * max(D('1.4') - g, g - D('3.1'), 0) ** 2
                    + 4 * max(D('5.73') - vb, 0) ** 2
                    + 4 * max(cb - D('4.5'), 0) ** 2
                )
                worst_difference = max(worst_difference, abs(D(record['V']) - total))
                zero_count += total == 0
                strict_count += e < D('.21') and D('1.4') < g < D('3.1') and vb > D('5.73') and cb < D('4.50')
            self.assertAlmostEqual(float(worst_difference), stats[split]['formula']['max_abs_V_error'], places=12)
            self.assertEqual(zero_count, stats[split]['formula']['recomputed_zero'])
            self.assertEqual(strict_count, stats[split]['formula']['strict'])

    def test_group_manifest_aligns_with_train_rows_only(self):
        train = rows(SOURCE / '02_castelli_train.csv')
        manifest = rows(OUTPUT / 'folds_02.csv')
        columns = ('id', 'A', 'B', 'X')
        row_key = lambda row: tuple(row[k] for k in columns)
        self.assertEqual(list(manifest[0]), [*columns, 'fold'])
        self.assertEqual(list(map(row_key, train)), list(map(row_key, manifest)))
        self.assertEqual(Counter(row['fold'] for row in manifest),
                         {'1': 2254, '2': 2254, '3': 2254, '4': 2247, '5': 2247})
        fold_by_pair = {}
        for row in manifest:
            key = row['A'], row['B']
            self.assertEqual(row['fold'], fold_by_pair.setdefault(key, row['fold']))
        self.assertEqual(len(fold_by_pair), 1608)
