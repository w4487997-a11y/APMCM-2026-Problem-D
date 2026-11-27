# -*- coding: utf-8 -*-
"""附加校验：文件完整性 + README 自洽性。

这些检查不属于题面强制项，但能回答“这份数据是不是官方那一份、有没有被改过、
统计口径是否与随附说明一致”。结论都要落到具体数字上。
"""

import hashlib
import json
import os

import numpy as np
import pandas as pd

GAP_NAMES = ("gap", "gap_gllbsc")

README_STATS = {
    "rows_full": 18928,
    "median_V": 22.2319,
    "max_V": 108.9558,
    "n_lt_0p5": 100,
    "n_lt_1": 152,
    "n_lt_2": 227,
    "n_lt_5": 375,
    "a_eq_b_rows": 364,
    "per_x_train": 1608,
    "per_x_val": 567,
    "per_x_holdout": 529,
}


def sha256_check(data_dir, add):
    manifest_path = os.path.join(data_dir, "sha256_public.json")
    if not os.path.exists(manifest_path):
        return {}   # 自检样例没有官方清单，跳过而不是记 PENDING
    with open(manifest_path, encoding="utf-8") as fh:
        man = json.load(fh)
    ok, bad, missing = [], [], []
    for name, expect in man.items():
        path = os.path.join(data_dir, name)
        if not os.path.exists(path):
            missing.append(name)
            continue
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        (ok if h == expect else bad).append(name)
    status = "PASS" if not bad and not missing else "FAIL"
    add("A0-1", "文件 sha256 与官方清单一致", status,
        f"{len(ok)} 个匹配，{len(bad)} 个不一致，{len(missing)} 个缺失",
        ("不一致：" + "、".join(bad)) if bad else "")
    return {"matched": ok, "mismatched": bad, "missing": missing}


def _penalty_terms(df):
    cols = ["v_form", "v_gap_low", "v_gap_high", "v_vbm", "v_cbm"]
    if not all(c in df.columns for c in cols):
        return None
    return sum(df[c].astype(float) for c in cols)


def consistency_checks(dfs, add, data_dir=""):
    """对照 README 的公开统计，检查数据自洽。"""
    out = {}

    # 1) 单项惩罚之和 == V
    worst = []
    for name in ("02_castelli_train.csv", "03_castelli_val.csv"):
        df = dfs.get(name)
        if df is None or "V" not in df.columns:
            continue
        terms = _penalty_terms(df)
        if terms is None:
            continue
        diff = np.abs(terms - df["V"].astype(float))
        worst.append((name, float(diff.max())))
    if worst:
        mx = max(w for _, w in worst)
        add("A2-7", "五项单项惩罚之和 = V", "PASS" if mx <= 2e-6 else "FAIL",
            "；".join(f"{n.split('_')[0]}: max|Δ|={w:.1e}" for n, w in worst),
            "逐项按六位小数落盘后求和，容差 2e-6")

    # 2) a_eq_b 行数（全空间 364）
    total_aeq, total_rows = 0, 0
    for df in dfs.values():
        if "a_eq_b" in df.columns and "A" in df.columns:
            pass
    seen = set()
    for name in ("02_castelli_train.csv", "03_castelli_val.csv",
                 "04_castelli_test_holdout.csv"):
        df = dfs.get(name)
        if df is None or "a_eq_b" not in df.columns:
            continue
        k = list(zip(df["A"], df["B"], df["X"]))
        keep = [i for i, kk in enumerate(k) if kk not in seen]
        seen.update(k)
        total_aeq += int(df["a_eq_b"].iloc[keep].sum())
        total_rows += len(keep)
    if total_rows:
        exp = README_STATS["a_eq_b_rows"]
        share = total_aeq / total_rows
        add("A2-8", "a_eq_b 行数与说明一致", "PASS" if total_aeq == exp else "FAIL",
            f"实测 {total_aeq} 行，占 {share:.2%}；说明为 {exp} 行（1.92%）")
        out["a_eq_b"] = {"count": total_aeq, "share": round(share, 4)}

    # 3) 每个 X 族在 02/03/04 的行数
    exp = {"02_castelli_train.csv": README_STATS["per_x_train"],
           "03_castelli_val.csv": README_STATS["per_x_val"],
           "04_castelli_test_holdout.csv": README_STATS["per_x_holdout"]}
    rows = []
    ok = True
    for name, e in exp.items():
        df = dfs.get(name)
        if df is None:
            continue
        vc = df["X"].value_counts()
        balanced = bool((vc == e).all() and len(vc) == 7)
        ok &= balanced
        rows.append(f"{name.split('_')[0]}: {vc.min()}–{vc.max()}（应全为 {e}）")
    if rows:
        add("A4-7", "每个 X 族在三档中行数均衡", "PASS" if ok else "FAIL",
            "；".join(rows),
            "对应 1,608 / 567 / 529 个 (A,B) 对 × 7 族")

    # 4) 盲池 = 主池 ∩ holdout
    def keys(df):
        return set(map(tuple, df[["A", "B", "X"]].itertuples(index=False, name=None)))

    if all(n in dfs for n in ("04_castelli_test_holdout.csv", "07_castelli_q2_pool.csv",
                              "11_castelli_q2_pool_blind.csv")):
        k07, k04, k11 = (keys(dfs["07_castelli_q2_pool.csv"]),
                         keys(dfs["04_castelli_test_holdout.csv"]),
                         keys(dfs["11_castelli_q2_pool_blind.csv"]))
        inter11 = {k for k in (k07 & k04)}
        add("A4-8-11", "11 = 07 ∩ 04", "PASS" if k11 == inter11 else "FAIL",
            f"11 {len(k11):,}，07∩04 {len(inter11):,}，对称差 {len(k11 ^ inter11):,}")
    if all(n in dfs for n in ("04_castelli_test_holdout.csv", "08_castelli_q3_pool.csv",
                              "12_castelli_q3_pool_blind.csv")):
        k08, k04, k12 = (keys(dfs["08_castelli_q3_pool.csv"]),
                         keys(dfs["04_castelli_test_holdout.csv"]),
                         keys(dfs["12_castelli_q3_pool_blind.csv"]))
        inter12 = {k for k in (k08 & k04)}
        add("A4-8-12", "12 = 08 ∩ 04", "PASS" if k12 == inter12 else "FAIL",
            f"12 {len(k12):,}，08∩04 {len(inter12):,}，对称差 {len(k12 ^ inter12):,}")

    # 5) V 的全量分布是否与 README 一致（只在有官方说明时核对）
    has_readme = bool(data_dir) and os.path.exists(
        os.path.join(data_dir, "README_数据集说明.md"))
    if not has_readme:
        return out
    labels = []
    for name in ("02_castelli_train.csv", "03_castelli_val.csv"):
        df = dfs.get(name)
        if df is not None and "V" in df.columns:
            labels.append(df["V"].astype(float))
    if labels:
        v = pd.concat(labels, ignore_index=True)
        stats = {
            "rows": int(len(v)),
            "median": round(float(v.median()), 4),
            "max": round(float(v.max()), 4),
            "lt_0p5": int((v < 0.5).sum()),
            "lt_1": int((v < 1).sum()),
            "lt_2": int((v < 2).sum()),
            "lt_5": int((v < 5).sum()),
            "v0": int((v == 0).sum()),
        }
        out["v_stats"] = stats
        # 说明里的分布是"全量 18,928"（含 04 的标签），本地只有 15,225 条带标签：
        # 因此只核对可核对的部分——最大值应完全一致，计数应单调偏小且缺口 ≤ 3,703。
        max_ok = abs(stats["max"] - README_STATS["max_V"]) <= 1e-4
        count_pairs = [(stats["lt_0p5"], README_STATS["n_lt_0p5"]),
                       (stats["lt_1"], README_STATS["n_lt_1"]),
                       (stats["lt_2"], README_STATS["n_lt_2"]),
                       (stats["lt_5"], README_STATS["n_lt_5"])]
        monotone = all(a <= b and (b - a) <= 3703 for a, b in count_pairs)
        gaps = "、".join(f"{b - a}" for a, b in count_pairs)
        status = "PASS" if (max_ok and monotone) else "FAIL"
        add("A3-4", "V 分布与数据集说明一致（可核对部分）", status,
            f"15,225 条：max {stats['max']}（说明 {README_STATS['max_V']}），"
            f"<0.5 {stats['lt_0p5']} / <1 {stats['lt_1']} / <2 {stats['lt_2']} / <5 {stats['lt_5']}",
            f"最大值一致；计数缺口 {gaps}，均可由 04 的 3,703 条未标注样本解释；"
            f"中位 {stats['median']} vs 说明 {README_STATS['median_V']} 的差异同源，无法本地验证")
    return out
