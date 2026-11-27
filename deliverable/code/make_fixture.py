# -*- coding: utf-8 -*-
"""生成 Task A 自检样例（synthetic fixture）。

用途：在没有官方附件的情况下，验证审计脚本本身能跑通、能报错。
⚠ 生成的数据不是官方附件，任何基于它的数字都不得写进竞赛结论。
官方附件到位后，把 --data-dir 指向真实目录即可，脚本无需修改。

结构严格对照题面：
  52 元素 × 52 元素 × 7 基团 = 18,928
  04 取 23×23×7 = 3,703 的完整区块
  02 + 03 = 15,225，按 (A,B) 元素对整组划分：1,608 对 + 567 对
  07 = 52×52（X = NO2）、11 = 23×23（X = NO2）
  08 = 3×52×52、12 = 3×23×23
  06 = 02 ∪ 03 的组成列
  02/03 不含 V = 0 样本（与官方一致）
"""

import argparse
import os

import numpy as np
import pandas as pd

ELEMENTS = [
    "Li", "Be", "Na", "Mg", "Al", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe",
    "Co", "Ni", "Cu", "Zn", "Ga", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru",
    "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Sm",
    "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Hf", "Ta", "W", "Re", "Os",
]
X_GROUPS = ["O3", "NO2", "FO2", "N2O", "N3", "O2S", "FNO"]
X_Q3 = ["O3", "NO2", "FO2"]

EPS = 0.5


def violation(e_form, gap, vbm, cbm):
    parts = [
        np.maximum(0.0, (e_form - 0.21) / EPS) ** 2,
        np.maximum(0.0, (1.4 - gap) / EPS) ** 2,
        np.maximum(0.0, (gap - 3.1) / EPS) ** 2,
        np.maximum(0.0, (5.73 - vbm) / EPS) ** 2,
        np.maximum(0.0, (cbm - 4.50) / EPS) ** 2,
    ]
    return sum(parts)


def strict_target(e_form, gap, vbm, cbm):
    return ((e_form < 0.21) & (1.4 < gap) & (gap < 3.1)
            & (vbm > 5.73) & (cbm < 4.50))


def build_grid():
    rows = []
    for a in ELEMENTS:
        for b in ELEMENTS:
            for x in X_GROUPS:
                rows.append((a, b, x))
    df = pd.DataFrame(rows, columns=["A", "B", "X"])
    df.insert(0, "id", ["P%06d" % (i + 1) for i in range(len(df))])
    df["formula"] = df["A"] + df["B"] + df["X"]
    df["a_eq_b"] = (df["A"] == df["B"]).astype(int)
    return df


def main(out_dir, seed=20261126):
    rng = np.random.default_rng(seed)
    os.makedirs(out_dir, exist_ok=True)

    grid = build_grid()
    n = len(grid)
    assert n == 18928, n

    # ---- 物理量 ----
    gap = rng.uniform(0.2, 4.5, n)
    zero_idx = rng.choice(n, size=18193, replace=False)
    gap[zero_idx] = 0.0
    e_form = rng.normal(0.05, 0.30, n).clip(-1.2, 1.6)
    vbm = rng.normal(5.55, 0.55, n)
    cbm = rng.normal(4.20, 0.55, n)
    mu_b = np.abs(rng.normal(0.0, 2.0, n))
    a_lat = rng.normal(4.20, 0.25, n)
    volume = rng.normal(65.0, 9.0, n)
    is_direct = rng.integers(0, 2, n)

    grid["gap"] = np.round(gap, 3)
    grid["e_form"] = np.round(e_form, 3)
    grid["vbm"] = np.round(vbm, 3)
    grid["cbm"] = np.round(cbm, 3)
    grid["mu_b"] = np.round(mu_b, 3)
    grid["a_lat"] = np.round(a_lat, 3)
    grid["volume"] = np.round(volume, 2)
    grid["gap_is_direct"] = is_direct
    # 与官方一致：五项单独落盘到 6 位小数，V = 五项之和
    e, g, vb, cb = grid["e_form"], grid["gap"], grid["vbm"], grid["cbm"]
    grid["v_form"] = np.round(np.maximum(0, (e - 0.21) / EPS) ** 2, 6)
    grid["v_gap_low"] = np.round(np.maximum(0, (1.4 - g) / EPS) ** 2, 6)
    grid["v_gap_high"] = np.round(np.maximum(0, (g - 3.1) / EPS) ** 2, 6)
    grid["v_vbm"] = np.round(np.maximum(0, (5.73 - vb) / EPS) ** 2, 6)
    grid["v_cbm"] = np.round(np.maximum(0, (cb - 4.50) / EPS) ** 2, 6)
    grid["V"] = np.round(grid[["v_form", "v_gap_low", "v_gap_high",
                                "v_vbm", "v_cbm"]].sum(axis=1), 6)

    # ---- 元素分组：04 用 23 元素区块，其余 29 元素进入 02/03 ----
    s23 = ELEMENTS[::2][:23]
    s29 = [e for e in ELEMENTS if e not in s23]
    assert len(s23) == 23 and len(s29) == 29

    in23 = lambda s: s.isin(s23)
    m04 = in23(grid["A"]) & in23(grid["B"])
    assert m04.sum() == 3703, m04.sum()

    rest = grid[~m04].copy()
    assert len(rest) == 15225

    # 按 (A,B) 元素对整组分配：29×29 全给 02，再补 767 个交叉对
    rest["pair"] = rest["A"] + "|" + rest["B"]
    pairs = rest.drop_duplicates("pair")["pair"].tolist()
    assert len(pairs) == 2175, len(pairs)

    both29 = {f"{a}|{b}" for a in s29 for b in s29}
    p02 = [p for p in pairs if p in both29]
    assert len(p02) == 841
    cross = [p for p in pairs if p not in both29]
    rng.shuffle(cross)
    p02 += cross[:767]
    p03 = [p for p in pairs if p not in set(p02)]
    assert len(p02) == 1608 and len(p03) == 567

    df02 = rest[rest["pair"].isin(p02)].drop(columns=["pair"]).copy()
    df03 = rest[rest["pair"].isin(p03)].drop(columns=["pair"]).copy()
    df04 = grid[m04].copy()
    assert len(df02) == 11256 and len(df03) == 3969

    # 02/03 不得含 V = 0（与官方划分一致），若有则扰动到明显违反带隙
    for d in (df02, df03):
        bad = d["V"] <= 0
        if bad.any():
            d.loc[bad, "e_form"] = 1.20
            d.loc[bad, "gap"] = 0.10
            d["v_form"] = np.round(np.maximum(0, (d["e_form"] - 0.21) / EPS) ** 2, 6)
            d["v_gap_low"] = np.round(np.maximum(0, (1.4 - d["gap"]) / EPS) ** 2, 6)
            d["v_gap_high"] = np.round(np.maximum(0, (d["gap"] - 3.1) / EPS) ** 2, 6)
            d["V"] = np.round(d[["v_form", "v_gap_low", "v_gap_high",
                                  "v_vbm", "v_cbm"]].sum(axis=1), 6)

    # ---- 候选池 ----
    comp_cols = ["id", "formula", "A", "B", "X", "a_eq_b"]
    pool_q2 = grid[grid["X"] == "NO2"][comp_cols].copy()
    pool_q2_b = grid[(grid["X"] == "NO2") & in23(grid["A"]) & in23(grid["B"])][comp_cols].copy()
    pool_q3 = grid[grid["X"].isin(X_Q3)][comp_cols].copy()
    pool_q3_b = grid[grid["X"].isin(X_Q3) & in23(grid["A"]) & in23(grid["B"])][comp_cols].copy()

    assert len(pool_q2) == 2704 and len(pool_q2_b) == 529
    assert len(pool_q3) == 8112 and len(pool_q3_b) == 1587

    # ---- 落盘 ----
    lab_cols = ["id", "formula", "A", "B", "X", "a_eq_b", "a_lat", "volume",
                "e_form", "gap", "gap_is_direct", "vbm", "cbm", "mu_b",
                "v_form", "v_gap_low", "v_gap_high", "v_vbm", "v_cbm", "V"]
    df02[lab_cols].to_csv(os.path.join(out_dir, "02_castelli_train.csv"), index=False)
    df03[lab_cols].to_csv(os.path.join(out_dir, "03_castelli_val.csv"), index=False)
    df04[comp_cols].to_csv(os.path.join(out_dir, "04_castelli_test_holdout.csv"), index=False)
    pd.concat([df02, df03])[comp_cols].to_csv(
        os.path.join(out_dir, "06_castelli_no_physics.csv"), index=False)
    pool_q2.to_csv(os.path.join(out_dir, "07_castelli_q2_pool.csv"), index=False)
    pool_q3.to_csv(os.path.join(out_dir, "08_castelli_q3_pool.csv"), index=False)
    pool_q2_b.to_csv(os.path.join(out_dir, "11_castelli_q2_pool_blind.csv"), index=False)
    pool_q3_b.to_csv(os.path.join(out_dir, "12_castelli_q3_pool_blind.csv"), index=False)

    meta = pd.DataFrame({
        "file": ["02", "03", "04", "06", "07", "08", "11", "12"],
        "rows": [len(df02), len(df03), len(df04), len(df02) + len(df03),
                 len(pool_q2), len(pool_q3), len(pool_q2_b), len(pool_q3_b)],
    })
    meta.to_csv(os.path.join(out_dir, "_fixture_meta.csv"), index=False)

    print("fixture written to", out_dir)
    print("02/03 V==0 counts:", int((df02["V"] == 0).sum()), int((df03["V"] == 0).sum()))
    print("strict counts:", int(strict_target(df02.e_form, df02.gap, df02.vbm, df02.cbm).sum()),
          int(strict_target(df03.e_form, df03.gap, df03.vbm, df03.cbm).sum()))
    print(meta.to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="task_a/data_fixture")
    ap.add_argument("--seed", type=int, default=20261126)
    args = ap.parse_args()
    main(args.out, args.seed)
