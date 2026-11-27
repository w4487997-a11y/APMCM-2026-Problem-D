"""Render compact, publication-ready figures from public Q1 audit inputs."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator, PercentFormatter
import numpy as np

from audit.phase1 import OUTPUT, ab_pair, group_summary, load_public_inputs


COLORS = {'02': '#175d84', '03': '#c86a30', '04': '#8797ad'}
LABELS = {'02': '02 Train', '03': '03 Validation', '04': '04 Holdout'}
INK = '#172d42'
MUTED = '#55687b'


def write_figure(fig, out, name):
    fig.savefig(out / f'{name}.svg', metadata={'Date': None})
    fig.savefig(out / f'{name}.png', dpi=300)
    plt.close(fig)


def plot_low_tail(out, labeled):
    fig, ax = plt.subplots(figsize=(7.8, 4.4), layout='constrained')
    upper = 14
    for split, rows in labeled.items():
        values, counts = np.unique([row['V'] for row in rows], return_counts=True)
        keep = values <= upper
        cumulative = np.cumsum(counts)[keep] / len(rows)
        ax.step(np.r_[0, values[keep], upper], np.r_[0, cumulative, cumulative[-1]],
                where='post', color=COLORS[split], linewidth=2, label=f'{LABELS[split]} (n={len(rows):,})')
    for x, label, y in [(5, 'V = 5', 0.833), (7.84, 'Zero-gap lower bound', 0.675)]:
        ax.axvline(x, linestyle='--', linewidth=1.15, color=MUTED, alpha=0.7)
        ax.text(x + 0.16, y, label, transform=ax.get_xaxis_transform(), fontsize=9, color=MUTED)
    ax.set(title='Empirical cumulative distribution of low violation scores',
           xlim=(0, upper), xlabel='True violation degree V', ylabel='Share of all labeled rows')
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.grid(True, color='#e2e8ef', linewidth=0.8)
    ax.legend(loc='upper left')
    write_figure(fig, out, 'low_violation_ecdf')


def plot_gap(out, labeled):
    families = ['O3', 'NO2', 'FO2', 'N2O', 'N3', 'O2S', 'FNO']
    fig, (ax_family, ax_gap) = plt.subplots(1, 2, figsize=(11.2, 4.55),
                                         gridspec_kw={'width_ratios': [1, 1.2]}, layout='constrained')
    fig.suptitle('Band-gap prevalence and positive-gap distribution', fontsize=17, color=INK)
    centers = np.arange(len(families))
    ax_gap.axvspan(1.4, 3.1, color='#dceadf', alpha=0.85, zorder=0, label='Target window')
    bins = np.arange(0, 7.51, 0.5)
    for split, offset in [('02', -0.18), ('03', 0.18)]:
        rows = labeled[split]
        family_stats = [group_summary([row for row in rows if row['X'] == x]) for x in families]
        widths = [stats['gap_positive'] / stats['rows'] for stats in family_stats]
        bars = ax_family.barh(centers + offset, widths, height=0.31, color=COLORS[split],
                             label=f'{LABELS[split]} ({family_stats[0]["rows"]:,} per family)')
        ax_family.bar_label(bars, labels=[str(stats['gap_positive']) for stats in family_stats],
                            fontsize=8, padding=4, color=INK)
        positive = [row['gap'] for row in rows if row['gap'] > 0]
        ax_gap.hist(positive, bins=bins, weights=np.repeat(1 / len(positive), len(positive)),
                    histtype='step', linewidth=2, color=COLORS[split],
                    label=f'{LABELS[split]} (n={len(positive):,})')
    ax_family.set(title='Positive gaps by anion family', xlabel='Share with gap > 0',
                  xlim=(0, 0.086), yticks=centers, yticklabels=families)
    ax_family.invert_yaxis()
    ax_family.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax_family.xaxis.grid(True, color='#e2e8ef', linewidth=0.8)
    ax_family.legend(loc='lower right', fontsize=8)
    ax_gap.set(title='Distribution conditional on gap > 0', xlabel='Band gap (eV)',
               ylabel='Share of positive gaps per 0.5 eV bin', xlim=(0, 7.25))
    ax_gap.yaxis.set_major_locator(MultipleLocator(0.05))
    ax_gap.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax_gap.yaxis.grid(True, color='#e2e8ef', linewidth=0.8)
    ax_gap.legend(loc='upper right', fontsize=8)
    write_figure(fig, out, 'band_gap_distribution')


def plot_split(out, raw):
    elements = sorted({row['A'] for rows in raw.values() for row in rows})
    positions = {element: index for index, element in enumerate(elements)}
    matrix = np.full((len(elements), len(elements)), -1)
    keys = tuple(LABELS)
    handles = []
    for color_index, split in enumerate(keys):
        pairs = {ab_pair(row) for row in raw[split]}
        for a, b in pairs:
            matrix[positions[a], positions[b]] = color_index
        handles.append(Patch(facecolor=COLORS[split], label=f'{LABELS[split]} ({len(pairs):,} pairs)'))
    fig, ax = plt.subplots(figsize=(8.6, 8.0), layout='constrained')
    ax.imshow(matrix, cmap=ListedColormap([COLORS[k] for k in keys]), interpolation='nearest', vmin=0, vmax=2)
    ax.set(title='Official split of the 2,704 ordered A–B pairs', xlabel='B-site element', ylabel='A-site element',
           xticks=range(len(elements)), yticks=range(len(elements)))
    ax.set_xticklabels(elements, fontsize=6.8, rotation=90)
    ax.set_yticklabels(elements, fontsize=6.8)
    ax.tick_params(axis='both', length=0, pad=2)
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.085), ncols=3, fontsize=9)
    write_figure(fig, out, 'ordered_pair_split')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', default=OUTPUT / 'figures', type=Path)
    out = parser.parse_args().out_dir
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK,
        'axes.labelcolor': INK, 'axes.titlecolor': INK, 'axes.titlesize': 13,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.axisbelow': True, 'axes.edgecolor': '#9aabbc',
        'xtick.color': MUTED, 'ytick.color': MUTED, 'legend.frameon': False,
        'svg.fonttype': 'none', 'svg.hashsalt': 'apmcm-q1-audit-phase1',
    })
    raw, labeled, _, _ = load_public_inputs()
    plot_low_tail(out, labeled)
    plot_gap(out, labeled)
    plot_split(out, raw)
    print(f'Wrote 3 figures in PNG and SVG to {out}.')


if __name__ == '__main__':
    main()
