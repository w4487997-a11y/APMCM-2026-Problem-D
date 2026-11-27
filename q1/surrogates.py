"""Train-only composition encoders and fixed direct/physical surrogate variants."""

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OrdinalEncoder

from q1.baselines import composition_encoder, model_templates


SEED = 42
NON_GAP = ('e_form', 'vbm', 'cbm')
ZERO_GAP_PENALTY = 7.84
HIST_PARAMS = dict(learning_rate=0.075, max_iter=180, max_leaf_nodes=31,
                   min_samples_leaf=20, l2_regularization=1.0, early_stopping=False,
                   categorical_features=(True, True, True))


@dataclass(frozen=True)
class Spec:
    family: str
    variant: str
    features: str = 'composition'

    @property
    def heads(self):
        if self.variant in ('direct', 'tail'):
            return ('V_tail',) if self.variant == 'tail' else ('V',)
        if self.variant == 'indirect':
            return (*NON_GAP, 'gap')
        positive_head = 'gap_penalty_positive' if self.variant == 'expected' else 'gap_positive'
        return (*NON_GAP, 'positive', positive_head)

    @property
    def direct(self):
        return self.variant in ('direct', 'tail')


SPECS = {
    'median': Spec('median', 'direct'),
    'ridge': Spec('ridge', 'direct'),
    'random_forest': Spec('random_forest', 'direct'),
    'ridge_interaction': Spec('ridge', 'direct', 'site_X_interactions'),
    'ridge_indirect': Spec('ridge', 'indirect'),
    'hgb_direct': Spec('hgb', 'direct'),
    'hgb_tail': Spec('hgb', 'tail'),
    'hgb_indirect': Spec('hgb', 'indirect'),
    'hgb_gap_hard': Spec('hgb', 'hard'),
    'hgb_gap_soft': Spec('hgb', 'soft'),
    'hgb_gap_mix': Spec('hgb', 'mix'),
    'hgb_gap_expected': Spec('hgb', 'expected'),
}


def design(composition, features):
    composition = np.asarray(composition, dtype=str)
    if features == 'composition':
        return composition
    a, b, x = composition.T
    return np.column_stack((a, b, x, np.char.add(np.char.add(a, '|'), x),
                            np.char.add(np.char.add(b, '|'), x), a == b))


def gap_penalty(gap):
    return (np.maximum(1.4 - gap, 0) / 0.5) ** 2 + (np.maximum(gap - 3.1, 0) / 0.5) ** 2


def combine_prediction(spec, components):
    """Return raw V_hat and any feasible gap-valued prediction."""
    if spec.direct:
        return components[spec.heads[0]], None
    f, vb, cb = (components[k] for k in NON_GAP)
    other = ((np.maximum(f - 0.21, 0) / 0.5) ** 2 + (np.maximum(5.73 - vb, 0) / 0.5) ** 2
             + (np.maximum(cb - 4.50, 0) / 0.5) ** 2)
    if spec.variant == 'indirect':
        gap = np.maximum(components['gap'], 0)
        return other + gap_penalty(gap), gap
    p = components['positive']
    if spec.variant == 'expected':
        conditional_penalty = np.maximum(components['gap_penalty_positive'], 0)
        return other + (1 - p) * ZERO_GAP_PENALTY + p * conditional_penalty, None
    positive_gap = np.maximum(components['gap_positive'], 0)
    if spec.variant == 'mix':
        return other + (1 - p) * ZERO_GAP_PENALTY + p * gap_penalty(positive_gap), None
    gap = p * positive_gap if spec.variant == 'soft' else np.where(p >= 0.5, positive_gap, 0.0)
    return other + gap_penalty(gap), gap


class Surrogate:
    """A fitted composition-only interface shared by CV and final inference."""

    def __init__(self, spec, encoder, estimators):
        self.spec = spec
        self.encoder = encoder
        self.estimators = estimators

    def transform(self, composition):
        return self.encoder.transform(design(composition, self.spec.features))

    def predict_details(self, composition):
        matrix = self.transform(composition)
        parts = {head: predict_head(model, head, matrix) for head, model in self.estimators.items()}
        raw, gap = combine_prediction(self.spec, parts)
        return np.maximum(raw, 0), raw, gap, parts

    def predict(self, composition):
        return self.predict_details(composition)[0]


def predict_head(model, head, matrix):
    return model.predict_proba(matrix)[:, 1] if head == 'positive' else model.predict(matrix)


def fresh_estimator(family, head, seed):
    if family == 'hgb':
        factory = HistGradientBoostingClassifier if head == 'positive' else HistGradientBoostingRegressor
        return factory(random_state=seed, **HIST_PARAMS)
    if head == 'positive':
        return LogisticRegression(max_iter=500, random_state=seed)
    model = model_templates()[family]
    if family == 'random_forest':
        model.set_params(random_state=seed)
    return model


def fit_batch(composition, properties, truth, names, seed=SEED):
    """Reuse identical fitted heads within a fold while keeping individual runtimes."""
    groups = {}
    for name in names:
        spec = SPECS[name]
        groups.setdefault((spec.family, spec.features), []).append(name)

    models, timings = {}, {}
    positive = properties['gap'] > 0
    for (family, features), group in groups.items():
        start = perf_counter()
        encoder = OrdinalEncoder(handle_unknown='error') if family == 'hgb' else composition_encoder()
        matrix = encoder.fit_transform(design(composition, features))
        encode_seconds = perf_counter() - start
        required = dict.fromkeys(head for name in group for head in SPECS[name].heads)
        estimators, elapsed = {}, {}
        for head in required:
            model = fresh_estimator(family, head, seed)
            start = perf_counter()
            if head == 'positive':
                model.fit(matrix, positive)
            elif head in ('gap_positive', 'gap_penalty_positive'):
                y = properties['gap'][positive]
                model.fit(matrix[positive], y if head == 'gap_positive' else gap_penalty(y))
            elif head == 'V_tail':
                model.fit(matrix, truth, sample_weight=1 + 4 * np.exp(-truth / 5))
            else:
                model.fit(matrix, truth if head == 'V' else properties[head])
            elapsed[head] = perf_counter() - start
            estimators[head] = model
        for name in group:
            spec = SPECS[name]
            models[name] = Surrogate(spec, encoder, {head: estimators[head] for head in spec.heads})
            timings[name] = (encode_seconds, sum(elapsed[head] for head in spec.heads))
    return models, timings
