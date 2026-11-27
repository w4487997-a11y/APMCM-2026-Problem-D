import unittest

import numpy as np

from q1.experiments import official
from q1.v12_handoff import NEW_FIELDS, remap_pool
from q1.v12_supplement import group_assignment


class DataContractTests(unittest.TestCase):
    def test_04_rejects_label_role(self):
        with self.assertRaisesRegex(ValueError, 'Invalid data role'):
            official('04', labeled=True)

    def test_v12_pool_alias_preserves_precision_and_id(self):
        row = {'id': '47', 'formula': 'AAX', 'A': 'Li', 'B': 'Li', 'X': 'O3', 'a_eq_b': '1',
               'V_hat': '0.12345678901234567', 'model_version': 'q23_final', 'source_pool': '08'}
        mapped = remap_pool(row, '08')
        self.assertEqual(tuple(mapped), NEW_FIELDS)
        self.assertEqual(mapped, {**row, 'pool': '08'})
        with self.assertRaisesRegex(ValueError, 'Expected 07'):
            remap_pool(row, '07')

    def test_alternate_folds_keep_ordered_pairs_together(self):
        rows = np.array([['Li', 'Ti', 'O3'], ['Li', 'Ti', 'NO2'], ['Ti', 'Li', 'O3'], ['B', 'B', 'FNO']])
        groups = group_assignment(rows, 1729)
        self.assertEqual(groups[0], groups[1])
        self.assertNotEqual(groups[0], groups[2])
        np.testing.assert_array_equal(groups, group_assignment(rows, 1729))
