# -*- coding: utf-8 -*-
"""O-11 图表：并档结构、排序保持、Top-K 落档。用 venv-mirna 的 matplotlib 运行。"""

import csv
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "O11"
for name in ("msyh.ttc", "simhei.ttf"):
    p = Path(r"C:\Windows\Fonts") / name
    if p.exists():
        font_manager.fontManager.addfont(str(p))
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["savefig.dpi"] = 300

NAVY, ACCENT, GREY = "#1F3864", "#C00000", "#8C8C8C"


def read_csv(name):
    with open(OUT / name, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def fig_ties():
    rows = read_csv("schemes.csv")
    rows = [r for r in rows if r["scheme"] != "float"]
    labels = [f"{r['problem']} {r['scheme']}" for r in rows]
    vals = [int(r["min_tier_ties"]) for r in rows]
    colors = [ACCENT if v > 1 else "#2E7D32" for v in vals]
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.barh(labels[::-1], vals[::-1], color=colors[::-1])
    for y, v in enumerate(vals[::-1]):
        ax.text(v + 0.3, y, str(v), va="center", fontsize=8)
    ax.set_xlabel("最低能量档并列候选数")
    ax.set_title("O-11：各精度方案的最低档并列数（红=无法唯一确定最优）", fontsize=11)
    ax.set_xlim(0, max(vals) * 1.2)
    ax.grid(axis="x", alpha=0.25, ls="--")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "o11_ties.png", bbox_inches="tight")
    plt.close(fig)


def fig_retention():
    rows = read_csv("sorting_retention.csv")
    labels = [f"{r['problem']} {r['scheme']}" for r in rows]
    keep = [float(r["pairwise_keep_distinct"]) for r in rows]
    loss = [float(r["best_V_loss"]) for r in rows]
    pres = [1.0 if r["argmin_preserved"] == "True" else 0.0 for r in rows]
    x = np.arange(len(rows))
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.3))
    axes[0].bar(x, keep, color=NAVY)
    axes[0].set_ylim(0, 1.08)
    axes[0].set_ylabel("可区分配对保序率")
    axes[0].set_title("(a) 整数能量能区分的配对上，顺序是否保持", fontsize=10)
    axes[1].bar(x, loss, color=[ACCENT if l > 1e-9 else "#2E7D32" for l in loss])
    axes[1].set_ylabel("整数最优相对浮点最优的 V_hat 损失")
    axes[1].set_title("(b) 最优候选是否被保住（0=保住）", fontsize=10)
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=75, ha="right", fontsize=6.5)
        ax.grid(axis="y", alpha=0.25, ls="--")
        ax.set_axisbelow(True)
    fig.suptitle("O-11：量化后排序保持与最优保留（不同方案）", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "o11_retention.png", bbox_inches="tight")
    plt.close(fig)


def fig_levels():
    d = json.loads((OUT / "o11_metrics.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    picks = [("q2", "qubo_x127/4"), ("q3", "qubo_x127/4"),
             ("q2", "partition_NO2"), ("q3", "partition_O3")]
    names, stats = [], []
    for prob, scheme in picks:
        row = next(r for r in d["ties"] if r["problem"] == prob and r["scheme"] == scheme)
        names.append(f"{prob}\n{scheme}")
        stats.append((int(row["n_levels"]), float(row["mean_tier"]), int(row["max_tier"])))
    idx = np.arange(len(names))
    ax.bar(idx, [s[1] for s in stats], color=NAVY, label="平均档大小")
    ax.bar(idx, [s[2] for s in stats], color=ACCENT, alpha=0.45, label="最大档大小")
    for i, s in enumerate(stats):
        ax.text(i, s[2] + 20, f"档数 {s[0]}", ha="center", fontsize=8)
    ax.set_xticks(idx)
    ax.set_xticklabels(names, fontsize=8)
    ax.set_yscale("log")
    ax.set_ylabel("每档候选数（对数轴）")
    ax.set_title("O-11：整数能量档位结构（并档越严重，唯一性越差）", fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25, ls="--")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "o11_levels.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_ties()
    fig_retention()
    fig_levels()
    for f in ("o11_ties.png", "o11_retention.png", "o11_levels.png"):
        print(f, (OUT / f).stat().st_size, "bytes")
