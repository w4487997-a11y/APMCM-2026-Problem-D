"""Regression and low-violation screening scores for labeled evaluation rows."""

from itertools import groupby
from math import ceil, isfinite, sqrt
from statistics import correlation, mean


SCREENING_BUDGETS = (10, 25, 50, 100)
LOW_V_CUTOFF = 5.0


def average_ranks(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(order)
    first_rank = 1
    for _, group in groupby(order, key=values.__getitem__):
        tied = list(group)
        rank = first_rank + (len(tied) - 1) / 2
        for index in tied:
            ranks[index] = rank
        first_rank += len(tied)
    return ranks


def evaluate(ids, truth, scores, budgets=SCREENING_BUDGETS, low_cutoff=LOW_V_CUTOFF):
    """Return scores for aligned rows with unique numeric official IDs."""
    ids, truth, scores = list(ids), list(truth), list(scores)
    n = len(ids)
    if not n or len(truth) != n or len(scores) != n or len(set(ids)) != n:
        raise ValueError('Evaluation requires aligned, nonempty rows with unique IDs')
    if not all(map(isfinite, truth)) or not all(map(isfinite, scores)):
        raise ValueError('Evaluation requires finite scores and labels')

    actual = sorted(range(n), key=lambda i: (truth[i], ids[i]))
    predicted = sorted(range(n), key=lambda i: (scores[i], ids[i]))
    errors = [abs(y - score) for y, score in zip(truth, scores)]
    low = [i for i in actual if truth[i] < low_cutoff]
    low_one_percent = actual[:ceil(n / 100)]
    spearman = None
    if min(truth) < max(truth) and min(scores) < max(scores):
        spearman = correlation(average_ranks(truth), average_ranks(scores))

    screening = {}
    for budget in budgets:
        if budget <= 0:
            raise ValueError('Screening budgets must be positive')
        k = min(budget, n)
        selected = predicted[:k]
        overlap = len(set(selected).intersection(actual[:k]))
        screening[budget] = {
            'k_effective': k,
            'overlap_count': overlap,
            'overlap_rate': overlap / k,
            'min_true_V': min(truth[i] for i in selected),
        }

    return {
        'rows': n,
        'mae': mean(errors),
        'rmse': sqrt(mean(e**2 for e in errors)),
        'spearman': spearman,
        'low_V_count': len(low),
        'low_V_mae': mean(errors[i] for i in low) if low else None,
        'top_true_1pct_count': len(low_one_percent),
        'top_true_1pct_mae': mean(errors[i] for i in low_one_percent),
        'screening': screening,
    }
