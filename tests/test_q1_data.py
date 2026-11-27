import unittest
from math import inf, nan

from q1.metrics import evaluate
from q1.violation import penalty_terms, strictly_feasible, violation_degree


class OfficialFormulaTests(unittest.TestCase):
    def test_thresholds_on_both_sides(self):
        base = [0.10, 2.0, 6.0, 4.0]
        for field, boundary, outward, term in [
            (0, 0.21, 1, 0), (1, 1.4, -1, 1), (1, 3.1, 1, 2),
            (2, 5.73, -1, 3), (3, 4.50, 1, 4),
        ]:
            for position in (-1, 0, 1):
                with self.subTest(field=field, boundary=boundary, position=position):
                    properties = base.copy()
                    properties[field] = boundary + position * outward * 1e-6
                    terms = penalty_terms(*properties)
                    self.assertAlmostEqual(terms[term], 4e-12 if position == 1 else 0.0, places=20)
                    self.assertTrue(all(value == 0 for i, value in enumerate(terms) if i != term))
                    self.assertEqual(strictly_feasible(*properties), position == -1)

    def test_additive_distinct_terms(self):
        observed = penalty_terms(0.71, 3.6, 4.73, 6.0)
        for value, expected in zip(observed, (1.0, 0.0, 1.0, 4.0, 9.0)):
            self.assertAlmostEqual(value, expected)
        self.assertAlmostEqual(violation_degree(0.71, 3.6, 4.73, 6.0), 15.0)

    def test_zero_band_gap(self):
        self.assertAlmostEqual(violation_degree(0.10, 0.0, 6.0, 4.0), 7.84)

    def test_nonfinite_input(self):
        for value in (inf, -inf, nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                violation_degree(0.10, value, 6.0, 4.0)


class ScreeningScoreTests(unittest.TestCase):
    def test_ties_and_screening_budget(self):
        report = evaluate([20, 2, 3, 4], [0.1, 0.1, 2, 5], [0, 3, 0, 4], (1, 2, 10))
        self.assertEqual(report['screening'][1]['overlap_count'], 0)
        self.assertEqual(report['screening'][1]['min_true_V'], 2)
        self.assertEqual(report['screening'][2]['overlap_rate'], 0.5)
        self.assertEqual(report['screening'][10]['k_effective'], 4)
        self.assertEqual(report['screening'][10]['overlap_rate'], 1)
        self.assertAlmostEqual(report['mae'], 1.5)
        self.assertAlmostEqual(report['rmse'], (13.42 / 4) ** 0.5)
        self.assertAlmostEqual(report['spearman'], 0.5)
        self.assertEqual(report['low_V_count'], 3)
        self.assertEqual(report['top_true_1pct_count'], 1)
        self.assertAlmostEqual(report['top_true_1pct_mae'], 2.9)

    def test_undefined_spearman_and_empty_low_tail(self):
        report = evaluate([1, 2], [5, 5], [3, 4], (1,))
        self.assertIsNone(report['spearman'])
        self.assertIsNone(report['low_V_mae'])

    def test_unaligned_duplicate_or_nonfinite(self):
        for ids, truth, scores in [
            ([], [], []), ([1], [1], [1, 2]), ([1, 1], [1, 2], [1, 2]), ([1], [inf], [1]),
        ]:
            with self.subTest(ids=ids, truth=truth, scores=scores), self.assertRaises(ValueError):
                evaluate(ids, truth, scores)
