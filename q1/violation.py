"""Official Problem D violation degree and strict feasibility predicates."""

from math import isfinite


PENALTY_NAMES = ('v_form', 'v_gap_low', 'v_gap_high', 'v_vbm', 'v_cbm')
PROPERTY_NAMES = ('e_form', 'gap', 'vbm', 'cbm')


def deviations(e_form, gap, vbm, cbm):
    """Return signed deviations from the five limits, in electronvolts."""
    if not all(map(isfinite, (e_form, gap, vbm, cbm))):
        raise ValueError('Physical properties must be finite')
    return e_form - 0.21, 1.4 - gap, gap - 3.1, 5.73 - vbm, cbm - 4.50


def squared_penalty(deviation):
    return (max(0.0, deviation) / 0.5) ** 2


def penalty_terms(e_form, gap, vbm, cbm):
    """Return the five ordered, dimensionless penalties in PENALTY_NAMES."""
    return tuple(map(squared_penalty, deviations(e_form, gap, vbm, cbm)))


def violation_degree(e_form, gap, vbm, cbm):
    return sum(penalty_terms(e_form, gap, vbm, cbm))


def strictly_feasible(e_form, gap, vbm, cbm):
    return all(deviation < 0 for deviation in deviations(e_form, gap, vbm, cbm))
