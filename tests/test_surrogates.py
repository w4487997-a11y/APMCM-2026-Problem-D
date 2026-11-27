import unittest

import numpy as np

from q1.surrogates import SPECS, combine_prediction


class GapPenaltyTests(unittest.TestCase):
    def test_zero_and_positive_branches(self):
        parts = {'e_form': np.array([0.1] * 3), 'vbm': np.array([6.0] * 3), 'cbm': np.array([4.0] * 3),
                 'positive': np.array([0.0, 0.5, 1.0]), 'gap_positive': np.array([2.0] * 3),
                 'gap_penalty_positive': np.array([0.0, 0.4, 0.0])}
        mixed, _ = combine_prediction(SPECS['hgb_gap_mix'], parts)
        soft, gap = combine_prediction(SPECS['hgb_gap_soft'], parts)
        hard, _ = combine_prediction(SPECS['hgb_gap_hard'], parts)
        expected, _ = combine_prediction(SPECS['hgb_gap_expected'], parts)
        np.testing.assert_allclose(mixed, [7.84, 3.92, 0])
        np.testing.assert_allclose(soft, [7.84, 0.64, 0])
        np.testing.assert_allclose(gap, [0, 1, 2])
        np.testing.assert_allclose(hard, [7.84, 0, 0])
        np.testing.assert_allclose(expected, [7.84, 4.12, 0])

    def test_negative_point_gap_is_clipped(self):
        parts = {'e_form': np.array([0.71]), 'vbm': np.array([5.23]), 'cbm': np.array([5.00]),
                 'gap': np.array([-0.1])}
        prediction, gap = combine_prediction(SPECS['hgb_indirect'], parts)
        np.testing.assert_allclose(prediction, [10.84])
        np.testing.assert_allclose(gap, [0])
