"""Generate English paper figures and paired ablation statistics from frozen outputs."""

import csv
import json
from pathlib import Path
from statistics import mean, stdev

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, PercentFormatter
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CV = ROOT / 'experiments' / 'q1_ablation_v1'
RELEASE = ROOT / 'handoff' / 'v1'
OUTPUT = CV / 'figures'
COLORS = {'direct': '#175d84', 'indirect': '#c86a30', 'mix': '#14735c', 'soft': '#88629c'}
LABEL = {'hgb_direct': 'Direct boosting', 'hgb_tail': 'Tail-weighted boosting',
         'hgb_indirect': 'Property model', 'hgb_gap_mix': 'Penalty mixture',
         'hgb_gap_soft': 'Mean-gap fusion', 'hgb_gap_hard': 'Hard gate'}
PAIRS = (
    ('ridge_indirect', 'ridge'), ('hgb_indirect', 'hgb_direct'),
    ('hgb_gap_hard', 'hgb_indirect'), ('hgb_gap_soft', 'hgb_indirect'),
    ('hgb_gap_mix', 'hgb_indirect'), ('hgb_gap_mix', 'hgb_gap_soft'),
    ('hgb_gap_expected', 'hgb_gap_mix'), ('ridge_interaction', 'ridge'),
    ('hgb_tail', 'hgb_direct'),
)


def load(path):
    with path.open(encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def save(fig, name):
    fig.savefig(OUTPUT / f'{name}.png', dpi=300)
    fig.savefig(OUTPUT / f'{name}.svg', metadata={'Date': None})
    plt.close(fig)


def fold_comparison(summary, lookup):
    fig, (left, right) = plt.subplots(1, 2, figsize=(10.6, 4.35), layout='constrained')
    fig.suptitle('Grouped cross-validation of the composition surrogates', fontsize=15)
    for kind, color, names in (
        ('Direct scores', COLORS['direct'], [r['model'] for r in summary if r['variant'] in ('direct', 'tail')]),
        ('Property-based scores', COLORS['indirect'], [r['model'] for r in summary
                                                       if r['variant'] not in ('direct', 'tail', 'mix')]),
        ('Selected mixture', COLORS['mix'], ['hgb_gap_mix']),
    ):
        subset = [r for r in summary if r['model'] in names]
        left.scatter([float(r['mae_mean']) for r in subset], [float(r['screening_score_mean']) for r in subset],
                     s=55, color=color, label=kind, zorder=3)
    left.axvline(4.49802919392422, linestyle='--', color='#687b8a', lw=1.25, label='Internal MAE limit')
    left.set(title='Global error and screening quality', xlabel='Mean absolute error of V',
             ylabel='Mean Top-25/50 overlap', xlim=(2.3, 8.05), ylim=(0, 0.5))
    left.legend(loc='upper right', fontsize=8)
    for name, color in [('hgb_direct', COLORS['direct']), ('hgb_indirect', COLORS['indirect']),
                        ('hgb_gap_mix', COLORS['mix'])]:
        scores = [float(lookup[name, str(fold)]['screening_score']) for fold in range(1, 6)]
        right.plot(range(1, 6), scores, marker='o', lw=1.8, color=color, label=LABEL[name])
    right.set(title='Screening scores on matched folds', xlabel='Held-out ordered-pair fold',
              ylabel='Top-25/50 overlap', xticks=range(1, 6), ylim=(0, 0.57))
    right.legend(loc='lower right', fontsize=8)
    for ax in (left, right):
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.yaxis.set_major_locator(MultipleLocator(0.1))
        ax.yaxis.grid(True, color='#dde5ea')
    save(fig, 'grouped_ablation')


def precision_recall(gap, score):
    positives = gap > 0
    order = np.argsort(-score, kind='stable')
    boundaries = np.r_[np.flatnonzero(np.diff(score[order]) != 0), len(score) - 1]
    cumulative = positives[order].cumsum()[boundaries]
    recall = cumulative / positives.sum()
    precision = cumulative / (boundaries + 1)
    ap = np.sum(np.diff(np.r_[0, recall]) * precision)
    return np.r_[0, recall], np.r_[1, precision], ap


def gap_plot(gap_rows, validation, selected):
    fig, ax = plt.subplots(figsize=(6.2, 4.0), layout='constrained')
    for name, rows, gap, score, color in (
        ('02 grouped out-of-fold', gap_rows, 'true_gap', 'p_positive', COLORS['direct']),
        ('03 official validation', [r for r in validation if r['model'] == selected],
         'true_gap', 'pred_positive', COLORS['mix']),
    ):
        y = np.array([float(row[gap]) for row in rows])
        p = np.array([float(row[score]) for row in rows])
        recall, precision, ap = precision_recall(y, p)
        ax.step(recall, precision, where='pre', lw=1.7, color=color, label=f'{name} (AP {ap:.3f})')
        ax.axhline(np.mean(y > 0), color=color, alpha=0.4, lw=1, linestyle='--')
    ax.set(title='Precision and recall for detecting positive band gaps',
           xlabel='Recall', ylabel='Precision', xlim=(0, 1), ylim=(0, 1.02))
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, color='#dde5ea')
    save(fig, 'positive_gap_precision_recall')


def property_plot(rows):
    fig, axes = plt.subplots(2, 2, figsize=(8.3, 6.4), layout='constrained')
    fig.suptitle('Validation of the four physical-property predictions', fontsize=15)
    for ax, key, label in zip(axes.flat, ('e_form', 'gap', 'vbm', 'cbm'),
                              ('Formation energy', 'Positive band gap', 'Valence-band maximum', 'Conduction-band minimum')):
        plot_rows = rows if key != 'gap' else [row for row in rows if float(row['true_gap']) > 0]
        target = np.array([float(row[f'true_{key}']) for row in plot_rows])
        predicted = np.array([float(row['pred_gap_positive' if key == 'gap' else f'pred_{key}'])
                              for row in plot_rows])
        lo, hi = min(target.min(), predicted.min()), max(target.max(), predicted.max())
        ax.scatter(target, predicted, s=7, alpha=0.38, color=COLORS['direct'], linewidth=0)
        ax.plot([lo, hi], [lo, hi], ls='--', lw=1, color='#728491')
        ax.set(title=f'{label} (n={len(target):,})', xlabel='Observed (eV)', ylabel='Predicted (eV)')
    save(fig, 'validation_properties')


def write_paired(lookup):
    rows = []
    for model, reference in PAIRS:
        for metric in ('mae', 'low_V_mae', 'screening_score', 'top_50_true_zero_gap'):
            values = [float(lookup[model, str(fold)][metric]) - float(lookup[reference, str(fold)][metric])
                      for fold in range(1, 6)]
            rows.append([model, reference, metric, *values, mean(values), stdev(values)])
    with (CV / 'paired_ablation.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(('model', 'reference', 'metric', 'fold1', 'fold2', 'fold3', 'fold4', 'fold5', 'mean', 'sd'))
        writer.writerows(rows)


def main():
    OUTPUT.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.axisbelow': True, 'legend.frameon': False,
                         'svg.fonttype': 'none', 'svg.hashsalt': 'q1-final-v1'})
    lookup = {(r['model'], r['split']): r for r in load(CV / 'fold_metrics.csv')}
    validation = load(RELEASE / 'validation_physics.csv')
    selected = json.loads((RELEASE / 'manifest.json').read_text(encoding='utf-8'))['selection']['selected']
    write_paired(lookup)
    fold_comparison(load(CV / 'model_comparison.csv'), lookup)
    gap_plot(load(CV / 'gap_probabilities.csv'), validation, selected)
    property_plot([r for r in validation if r['model'] == selected])
    print(f'Exported three PNG/SVG figures to {OUTPUT}.')


if __name__ == '__main__':
    main()
