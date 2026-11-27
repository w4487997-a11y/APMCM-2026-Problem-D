"""Produce the V1.2 penalty decomposition, property scatter, and gap PR figures."""

import json
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from audit.plot_final import load, precision_recall


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'experiments' / 'q1_v12'
OUTPUT = DATA / 'figures'
BLUE, GREEN, ORANGE, GRID = '#185b82', '#0b7960', '#be653c', '#dce5eb'


def save(fig, name):
    fig.savefig(OUTPUT / f'{name}.svg', metadata={'Date': None})
    fig.savefig(OUTPUT / f'{name}.png', dpi=300)
    plt.close(fig)


def penalty_chart():
    rows = load(DATA / 'penalty_decomposition.csv')
    records = {(row['model'], row['scope'], row['term']): row for row in rows}
    terms = ('v_form', 'v_gap_low', 'v_gap_high', 'v_vbm', 'v_cbm')
    names = ('Formation\nenergy', 'Band gap\nlower limit', 'Band gap\nupper limit', 'VBM', 'CBM')
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.35), layout='constrained')
    fig.suptitle('Decomposition of the five violation penalties on file 03', fontsize=15)
    positions = np.arange(len(terms))
    for ax, scope, label in zip(axes, ('all', 'V_lt_5'), ('All validation rows', 'Observed V < 5')):
        mixtures = [records['hgb_gap_mix', scope, term] for term in terms]
        observed = [float(row['true_penalty_mean']) for row in mixtures]
        ordinary = [float(records['hgb_indirect', scope, term]['pred_penalty_mean']) for term in terms]
        predicted = [float(row['pred_penalty_mean']) for row in mixtures]
        for offset, values, color, text in (
            (-0.25, observed, BLUE, 'Observed'), (0, ordinary, ORANGE, 'Ordinary gap'),
            (0.25, predicted, GREEN, 'Penalty mixture'),
        ):
            ax.bar(positions + offset, values, width=0.22, label=text, color=color)
        ax.set(title=f'{label} (n={int(mixtures[0]["rows"]):,})', ylabel='Mean penalty',
               xticks=positions, xticklabels=names)
        ax.yaxis.grid(True, color=GRID)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='outside lower center', ncols=3, fontsize=9)
    save(fig, 'five_penalty_decomposition')


def scatter_chart():
    records = [r for r in load(DATA / 'val_physics_predictions.csv') if r['model'] == 'hgb_indirect']
    fig, axes = plt.subplots(2, 2, figsize=(8.3, 6.25), layout='constrained')
    fig.suptitle('Ordinary four-property surrogate on file 03', fontsize=15)
    labels = ('Formation energy', 'Band gap', 'Valence-band maximum', 'Conduction-band minimum')
    for ax, key, label in zip(axes.flat, ('e_form', 'gap', 'vbm', 'cbm'), labels):
        observed = np.array([float(row[f'true_{key}']) for row in records])
        predicted = np.array([float(row[f'pred_{key}']) for row in records])
        lower, upper = min(observed.min(), predicted.min()), max(observed.max(), predicted.max())
        ax.scatter(observed, predicted, color=BLUE, s=6, alpha=0.30, linewidth=0)
        ax.plot([lower, upper], [lower, upper], '--', lw=1, color='#69798b')
        ax.set(title=label, xlabel='Observed (eV)', ylabel='Predicted (eV)')
    save(fig, 'ordinary_four_properties')


def classifier_chart():
    rows = load(DATA / 'gap_probabilities_03.csv')
    gap = np.array([float(r['true_gap']) for r in rows])
    scores = np.array([float(r['p_positive']) for r in rows])
    recall, precision, ap = precision_recall(gap, scores)
    metrics = json.loads((DATA / 'gap_classifier_metrics.json').read_text(encoding='utf-8'))
    fig, ax = plt.subplots(figsize=(6.35, 4.2), layout='constrained')
    ax.step(recall, precision, where='pre', color=GREEN, lw=1.8,
            label=f'AP {ap:.3f} · trapezoidal AUC {metrics["pr_auc_trapezoidal"]:.3f}')
    ax.axhline(np.mean(gap > 0), color=BLUE, linestyle='--', linewidth=1.0, label='Positive-gap prevalence')
    ax.scatter([metrics['hard_recall']], [metrics['hard_precision']], color=ORANGE, zorder=3,
               s=37, label='Hard gate at 0.5')
    ax.set(title='Positive-gap classification on file 03', xlabel='Recall', ylabel='Precision',
           xlim=(0, 1), ylim=(0, 1.015))
    ax.grid(True, color=GRID)
    ax.legend(loc='upper right', fontsize=9)
    save(fig, 'gap_pr_03')


def main():
    OUTPUT.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.axisbelow': True, 'legend.frameon': False,
                         'svg.fonttype': 'none', 'svg.hashsalt': 'q1-v12'})
    penalty_chart()
    scatter_chart()
    classifier_chart()
    print(f'Wrote three V1.2 figures in PNG and SVG to {OUTPUT}.')


if __name__ == '__main__':
    main()
