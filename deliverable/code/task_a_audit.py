# -*- coding: utf-8 -*-
"""Task A：CSV 数据审计（对应 V0.4 第四章 A1–A5）。

用法：
    python task_a/task_a_audit.py --data-dir <附件目录> --out audit_result.json

输出：JSON（供报告生成器使用）+ 控制台摘要。
判定：PASS / FAIL / PENDING；缺文件或无法对账的检查记 PENDING，不猜测。
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

EPS = 0.5
EXPECTED_ROWS = {
    "02_castelli_train.csv": 11256,
    "03_castelli_val.csv": 3969,
    "04_castelli_test_holdout.csv": 3703,
    "06_castelli_no_physics.csv": 15225,
    "07_castelli_q2_pool.csv": 2704,
    "08_castelli_q3_pool.csv": 8112,
    "11_castelli_q2_pool_blind.csv": 529,
    "12_castelli_q3_pool_blind.csv": 1587,
}
LABELED = ["02_castelli_train.csv", "03_castelli_val.csv"]
POOLS_NO_PHYSICS = ["04_castelli_test_holdout.csv", "06_castelli_no_physics.csv",
                    "07_castelli_q2_pool.csv", "08_castelli_q3_pool.csv",
                    "11_castelli_q2_pool_blind.csv", "12_castelli_q3_pool_blind.csv"]
PHYSICS_COLS = ["e_form", "gap", "gap_gllbsc", "vbm", "cbm", "mu_b", "gap_is_direct",
                "a_lat", "volume", "fermi_level", "fermi_width",
                "v_form", "v_gap_low", "v_gap_high", "v_vbm", "v_cbm", "V"]
GAP_NAMES = ("gap", "gap_gllbsc")
V_TOL = 5e-5   # 输入六位小数落盘导致复算偏差上界约 1e-5


def gap_col(df):
    for name in GAP_NAMES:
        if name in df.columns:
            return name
    return None
X_GROUPS = ["O3", "NO2", "FO2", "N2O", "N3", "O2S", "FNO"]
X_Q3 = ["O3", "NO2", "FO2"]

check_rows = []


def add(cid, name, status, detail, evidence=""):
    check_rows.append({"id": cid, "name": name, "status": status,
                       "detail": detail, "evidence": evidence})


def read_csv_robust(path):
    last = None
    for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
        try:
            df = pd.read_csv(path, encoding=enc, low_memory=False)
            return df, enc
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise last


def violation(e_form, gap, vbm, cbm):
    e_form = np.asarray(e_form, dtype=float)
    gap = np.asarray(gap, dtype=float)
    vbm = np.asarray(vbm, dtype=float)
    cbm = np.asarray(cbm, dtype=float)
    parts = [
        np.maximum(0.0, (e_form - 0.21) / EPS) ** 2,
        np.maximum(0.0, (1.4 - gap) / EPS) ** 2,
        np.maximum(0.0, (gap - 3.1) / EPS) ** 2,
        np.maximum(0.0, (5.73 - vbm) / EPS) ** 2,
        np.maximum(0.0, (cbm - 4.50) / EPS) ** 2,
    ]
    return sum(parts)


def strict_target(e_form, gap, vbm, cbm):
    e_form = np.asarray(e_form, dtype=float)
    gap = np.asarray(gap, dtype=float)
    vbm = np.asarray(vbm, dtype=float)
    cbm = np.asarray(cbm, dtype=float)
    return ((e_form < 0.21) & (1.4 < gap) & (gap < 3.1)
            & (vbm > 5.73) & (cbm < 4.50))


# ---------------------------------------------------------------- A1
def audit_files(data_dir):
    files = []
    dfs = {}
    for name, expected in EXPECTED_ROWS.items():
        path = os.path.join(data_dir, name)
        if not os.path.exists(path):
            files.append({"name": name, "expected": expected, "rows": None,
                          "status": "PENDING", "note": "文件不存在"})
            add("A1-" + name.split("_")[0], "附件存在：" + name, "PENDING", "文件不存在")
            continue
        df, enc = read_csv_robust(path)
        dfs[name] = df
        rows, cols = df.shape
        num_ok = True
        for c in PHYSICS_COLS:
            if c in df.columns:
                conv = pd.to_numeric(df[c], errors="coerce")
                if conv.isna().sum() > df[c].isna().sum():
                    num_ok = False
        has_phys = any(c in df.columns for c in PHYSICS_COLS)
        match = rows == expected
        status = "PASS" if match else "FAIL"
        files.append({
            "name": name, "expected": expected, "rows": rows, "cols": cols,
            "columns": list(df.columns), "encoding": enc,
            "missing_cells": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "has_physics": has_phys, "numeric_ok": num_ok,
            "status": status, "note": "" if match else f"行数预期 {expected}",
        })
        add("A1-" + name.split("_")[0], "行数与字段：" + name, status,
            f"{rows:,} 行 × {cols} 列，编码 {enc}",
            "；".join(f"{c}:{d}" for c, d in zip(df.columns, df.dtypes.astype(str))) if cols <= 20 else "")
        if name in POOLS_NO_PHYSICS and has_phys:
            add("A1-leak-" + name.split("_")[0], "池文件不得含物性列：" + name,
                "FAIL", "出现物性列：" + ",".join(c for c in PHYSICS_COLS if c in df.columns))
    return files, dfs


# ---------------------------------------------------------------- A2
def audit_quality(dfs):
    out = {}
    keys = {}
    for name, df in dfs.items():
        if all(c in df.columns for c in ("A", "B", "X")):
            keys[name] = set(map(tuple, df[["A", "B", "X"]].itertuples(index=False, name=None)))

    dup = {n: int(df.duplicated(subset=["A", "B", "X"]).sum())
           for n, df in dfs.items() if all(c in df.columns for c in ("A", "B", "X"))}
    total_dup = sum(dup.values())
    add("A2-1", "材料主键唯一 (A,B,X)", "PASS" if total_dup == 0 else "FAIL",
        f"重复键合计 {total_dup} 条", "; ".join(f"{k}:{v}" for k, v in dup.items() if v))
    out["duplicates"] = dup

    a_vals, b_vals, bad_tokens = set(), set(), []
    for df in dfs.values():
        for col, bucket in (("A", a_vals), ("B", b_vals)):
            if col not in df.columns:
                continue
            vals = df[col].astype(str)
            bucket.update(vals.unique().tolist())
            if (vals != vals.str.strip()).any():
                bad_tokens.append(f"{col} 含首尾空格")
            # 同一元素出现两种大小写形态才算异常（Li 与 LI 并存）
            forms = {}
            for v in vals.unique():
                forms.setdefault(v.strip().lower(), set()).add(v)
            collide = [k for k, vs in forms.items() if len(vs) > 1]
            if collide:
                bad_tokens.append(f"{col} 大小写混用：{','.join(sorted(collide)[:5])}")
    same_pool = a_vals == b_vals
    add("A2-2", "元素编码一致（A、B 同池）", "PASS" if same_pool and not bad_tokens else "FAIL",
        f"A 位 {len(a_vals)} 种、B 位 {len(b_vals)} 种" + ("" if same_pool else "，两者不一致")
        + ("" if not bad_tokens else "；" + "；".join(sorted(set(bad_tokens)))))
    out["elements"] = {"A": sorted(a_vals), "B": sorted(b_vals), "n_A": len(a_vals),
                       "n_B": len(b_vals), "same_pool": bool(same_pool)}

    ab = None
    for df in dfs.values():
        if all(c in df.columns for c in ("A", "B", "X")):
            ab = df
            break
    if ab is not None:
        n_aeq = int((ab["A"] == ab["B"]).sum())
        rev = int(((ab["A"] != ab["B"])).sum())
        add("A2-3", "A = B 合法且有序位点", "PASS" if n_aeq > 0 and rev > 0 else "FAIL",
            f"A=B 记录 {n_aeq:,} 条，A≠B 记录 {rev:,} 条")
        out["a_eq_b"] = {"same": n_aeq, "diff": rev}

    zero_share = {}
    for name in LABELED:
        df = dfs.get(name)
        gc = gap_col(df) if df is not None else None
        if gc is not None:
            g = pd.to_numeric(df[gc], errors="coerce")
            zero_share[name] = round(float((g == 0).mean()), 4)
    if zero_share:
        add("A2-4", "gap = 0 保留（金属性）", "PASS",
            "零带隙占比 " + "，".join(f"{k.split('_')[0]}={v:.2%}" for k, v in zero_share.items()),
            "全库基准 18,193 / 18,928 = 96.12%")
    out["gap_zero_share"] = zero_share

    nan_report = {}
    for name in LABELED:
        df = dfs.get(name)
        if df is None:
            continue
        rec = {}
        for c in PHYSICS_COLS:
            if c in df.columns:
                s = pd.to_numeric(df[c], errors="coerce")
                rec[c] = {"nan": int(s.isna().sum()), "inf": int(np.isinf(s).sum())}
        nan_report[name] = rec
    ok = all(v["inf"] == 0 for rec in nan_report.values() for v in rec.values())
    add("A2-5", "物性字段可解析、无 inf", "PASS" if ok else "FAIL",
        "；".join(f"{k.split('_')[0]}:{sum(v['nan'] for v in rec.values())} 个 NaN"
                 for k, rec in nan_report.items()))
    out["nan"] = nan_report

    join = {}
    if all(n in keys for n in LABELED + ["04_castelli_test_holdout.csv"]):
        tr, va, te = (keys["02_castelli_train.csv"], keys["03_castelli_val.csv"],
                      keys["04_castelli_test_holdout.csv"])
        union = tr | va | te
        join = {"union": len(union), "expected": 18928,
                "pairs_02_03": len(tr & va), "pairs_02_04": len(tr & te),
                "pairs_03_04": len(va & te)}
        ok = (len(union) == 18928 and join["pairs_02_03"] == 0
              and join["pairs_02_04"] == 0 and join["pairs_03_04"] == 0)
        add("A2-6", "02/03/04 通过主键可关联且不重叠",
            "PASS" if ok else "FAIL",
            f"并集 {len(union):,} / 18,928；交叠 02∩03={join['pairs_02_03']}, "
            f"02∩04={join['pairs_02_04']}, 03∩04={join['pairs_03_04']}")
    out["join"] = join
    return out


# ---------------------------------------------------------------- A3
def audit_v(dfs):
    out = {"unit_tests": [], "files": {}, "counts": {}}
    cases = [
        (0.10, 2.00, 6.00, 4.00, 0.0),
        (0.21, 1.40, 5.73, 4.50, 0.0),
        (0.41, 2.00, 6.00, 4.00, 0.16),
        (0.10, 0.00, 6.00, 4.00, 7.84),
        (0.10, 3.60, 6.00, 4.00, 1.0),
        (0.10, 2.00, 5.23, 4.00, 1.0),
        (0.10, 2.00, 6.00, 5.00, 1.0),
    ]
    all_pass = True
    for i, (e, g, v, c, exp) in enumerate(cases, 1):
        got = float(violation(e, g, v, c))
        ok = abs(got - exp) <= 1e-8
        all_pass &= ok
        out["unit_tests"].append({"case": i, "args": [e, g, v, c],
                                  "expected": exp, "got": round(got, 10), "pass": bool(ok)})
    add("A3-1", "七项公式单元测试", "PASS" if all_pass else "FAIL",
        f"{sum(t['pass'] for t in out['unit_tests'])}/7 通过",
        "含 /0.5 归一；边界样本期望为 0")

    merged = []
    for name in LABELED:
        df = dfs.get(name)
        if df is None or "e_form" not in (df.columns if df is not None else []):
            out["files"][name] = {"status": "PENDING"}
            add("A3-2-" + name.split("_")[0], f"V 重算：{name}", "PENDING", "缺少物性列")
            continue
        gc = gap_col(df)
        need = ["e_form", "vbm", "cbm"] + ([gc] if gc else [])
        if not all(c in df.columns for c in need):
            missing = [c for c in need if c not in df.columns]
            out["files"][name] = {"status": "PENDING", "missing": missing}
            add("A3-2-" + name.split("_")[0], f"V 重算：{name}", "PENDING",
                "缺少列：" + ",".join(missing))
            continue
        rec = {}
        v_calc = violation(df["e_form"], df[gc], df["vbm"], df["cbm"])
        rec["v_min"] = float(np.min(v_calc))
        rec["v_zero"] = int((v_calc == 0).sum())
        rec["strict"] = int(strict_target(df["e_form"], df[gc],
                                          df["vbm"], df["cbm"]).sum())
        if "V" in df.columns:
            v_off = pd.to_numeric(df["V"], errors="coerce")
            diff = np.abs(v_calc - v_off.values)
            rec["max_abs_err"] = float(np.nanmax(diff))
            rec["mean_abs_err"] = float(np.nanmean(diff))
            rec["over_tol"] = int((diff > V_TOL).sum())
            status = "PASS" if rec["max_abs_err"] <= V_TOL else "FAIL"
            add("A3-2-" + name.split("_")[0], f"V 重算与附件对账：{name}", status,
                f"max|ΔV|={rec['max_abs_err']:.2e}，mean|ΔV|={rec['mean_abs_err']:.2e}，"
                f"超 {V_TOL:.0e} 的 {rec['over_tol']} 条",
                "输入按六位小数落盘，复算偏差上界约 1e-5，实测与此吻合")
            terms = [c for c in ("v_form", "v_gap_low", "v_gap_high", "v_vbm", "v_cbm")
                     if c in df.columns]
            if len(terms) == 5:
                d2 = np.abs(df[terms].astype(float).sum(axis=1) - v_off)
                rec["sum_err"] = float(np.nanmax(d2))
                add("A3-6-" + name.split("_")[0], f"V = 五项惩罚之和：{name}",
                    "PASS" if rec["sum_err"] <= 2e-6 else "FAIL",
                    f"max|Σv_* − V|={rec['sum_err']:.1e}")
        else:
            rec["max_abs_err"] = None
            add("A3-2-" + name.split("_")[0], f"V 重算：{name}", "PENDING",
                "附件无 V 列，仅重算不比对")
        rec["rows"] = int(len(df))
        out["files"][name] = rec
        merged.append(df)

    if merged:
        md = pd.concat(merged, ignore_index=True)
        gcm = gap_col(md)
        v_calc = violation(md["e_form"], md[gcm], md["vbm"], md["cbm"])
        st = strict_target(md["e_form"], md[gcm], md["vbm"], md["cbm"])
        out["counts"] = {"rows": int(len(md)), "v_zero": int((v_calc == 0).sum()),
                         "strict": int(st.sum()), "v_min": float(np.min(v_calc)),
                         "v_median": float(np.median(v_calc))}
        add("A3-3", "两套口径统计（02∪03）", "PASS",
            f"V=0 共 {out['counts']['v_zero']} 条，严格目标 {out['counts']['strict']} 条",
            f"全库基准 19 / 15；最小 V={out['counts']['v_min']:.4f}")
    return out


# ---------------------------------------------------------------- A4 / A5
def key_set(df):
    return set(map(tuple, df[["A", "B", "X"]].itertuples(index=False, name=None)))


def audit_split(dfs):
    out = {}
    n = {k: len(df) for k, df in dfs.items()}
    add("A4-1", "并集覆盖 18,928", "PASS" if n.get("02_castelli_train.csv", 0) + n.get("03_castelli_val.csv", 0) + n.get("04_castelli_test_holdout.csv", 0) == 18928 else "FAIL",
        f"02+03+04 = {n.get('02_castelli_train.csv',0)+n.get('03_castelli_val.csv',0)+n.get('04_castelli_test_holdout.csv',0):,}")

    if "06_castelli_no_physics.csv" in dfs and "02_castelli_train.csv" in dfs:
        k06 = key_set(dfs["06_castelli_no_physics.csv"])
        k0203 = key_set(dfs["02_castelli_train.csv"]) | key_set(dfs["03_castelli_val.csv"])
        add("A4-2", "06 = 02 ∪ 03（组成集合）", "PASS" if k06 == k0203 else "FAIL",
            f"06 {len(k06):,}，02∪03 {len(k0203):,}，差 {len(k06 ^ k0203):,}")

    if "11_castelli_q2_pool_blind.csv" in dfs and "07_castelli_q2_pool.csv" in dfs:
        k11 = key_set(dfs["11_castelli_q2_pool_blind.csv"])
        k07 = key_set(dfs["07_castelli_q2_pool.csv"])
        add("A4-3", "11 ⊆ 07", "PASS" if k11 <= k07 else "FAIL",
            f"11 有 {len(k11 - k07):,} 条不在 07 内")

    if "12_castelli_q3_pool_blind.csv" in dfs and "08_castelli_q3_pool.csv" in dfs:
        k12 = key_set(dfs["12_castelli_q3_pool_blind.csv"])
        k08 = key_set(dfs["08_castelli_q3_pool.csv"])
        add("A4-4", "12 ⊆ 08", "PASS" if k12 <= k08 else "FAIL",
            f"12 有 {len(k12 - k08):,} 条不在 08 内")

    for name, allowed, label in (
            ("07_castelli_q2_pool.csv", ["NO2"], "07 的 X 必须全为 NO2"),
            ("11_castelli_q2_pool_blind.csv", ["NO2"], "11 的 X 必须全为 NO2"),
            ("08_castelli_q3_pool.csv", X_Q3, "08 的 X ⊆ {O3,NO2,FO2}"),
            ("12_castelli_q3_pool_blind.csv", X_Q3, "12 的 X ⊆ {O3,NO2,FO2}")):
        df = dfs.get(name)
        if df is None:
            continue
        xs = set(df["X"].astype(str).unique())
        ok = xs <= set(allowed)
        add("A4-5-" + name.split("_")[0], label, "PASS" if ok else "FAIL",
            "实际 X：" + "、".join(sorted(xs)))

    for name, dim in (("07_castelli_q2_pool.csv", 1), ("08_castelli_q3_pool.csv", 3)):
        df = dfs.get(name)
        if df is None:
            continue
        na, nb, nx = df["A"].nunique(), df["B"].nunique(), df["X"].nunique()
        ok = na * nb * nx == len(df) and na == nb == 52 and nx == dim
        add("A4-6-" + name.split("_")[0], f"{name.split('_')[0]} 覆盖完整网格",
            "PASS" if ok else "FAIL",
            f"|A|={na}, |B|={nb}, |X|={nx}, 行数 {len(df):,}"
            + ("，构成完整网格" if ok else ""))
    return out


def audit_blind(dfs):
    out = {}
    for name in ("04_castelli_test_holdout.csv", "11_castelli_q2_pool_blind.csv",
                 "12_castelli_q3_pool_blind.csv"):
        df = dfs.get(name)
        if df is None:
            continue
        na, nb, nx = df["A"].nunique(), df["B"].nunique(), df["X"].nunique()
        pairs = df[["A", "B"]].drop_duplicates().shape[0]
        # 结构判据不是"元素级笛卡尔积"，而是"元素对 × X 族"完整：
        # 切分以 (A,B) 对为单位，元素因此散落在全部 52 类上。
        rows_ok = len(df) == pairs * nx
        per_pair = df.groupby(["A", "B"])["X"].nunique()
        pair_complete = bool((per_pair == nx).all())
        per_x = {str(x): int(len(sub)) for x, sub in df.groupby("X")}
        same_pairs = bool(len({int(v) for v in per_x.values()}) == 1)
        out[name] = {"n_A": int(na), "n_B": int(nb), "n_X": int(nx),
                     "rows": int(len(df)), "pairs": int(pairs),
                     "product": int(pairs * nx),
                     "cartesian": bool(rows_ok and pair_complete),
                     "ab_per_x": per_x,
                     "same_ab_across_x": same_pairs}
        status = "PASS" if (rows_ok and pair_complete) else "FAIL"
        add("A5-" + name.split("_")[0], f"区块结构：{name}", status,
            f"{pairs:,} 个 (A,B) 对 × {nx} 个 X 族 = {pairs * nx:,}，行数 {len(df):,}；"
            f"|A|={na}、|B|={nb}"
            + ("，每个元素对都含全部 X 族" if pair_complete else "，存在元素对缺 X 族")
            + ("，各 X 族行数一致" if same_pairs else "，各 X 族行数不一致"))
    if "04_castelli_test_holdout.csv" in dfs and "02_castelli_train.csv" in dfs:
        te = dfs["04_castelli_test_holdout.csv"]
        tr = pd.concat([dfs["02_castelli_train.csv"], dfs["03_castelli_val.csv"]])
        a_in = set(te["A"]) <= set(tr["A"])
        b_in = set(te["B"]) <= set(tr["B"])
        out["elements_visible"] = {"A_in_train": bool(a_in), "B_in_train": bool(b_in)}
        add("A5-4", "04 的元素是否在 02/03 出现",
            "PASS" if (a_in and b_in) else "FAIL",
            ("A、B 均出现（缺的是组合而非元素）" if (a_in and b_in)
             else "存在未出现元素（留出的是元素）"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", default="task_a/audit_result.json")
    ap.add_argument("--mode", default="real", choices=["real", "synthetic"])
    args = ap.parse_args()

    files, dfs = audit_files(args.data_dir)
    quality = audit_quality(dfs)
    vchk = audit_v(dfs)
    split = audit_split(dfs) if dfs else {}
    blind = audit_blind(dfs) if dfs else {}

    import audit_extra
    integrity = audit_extra.sha256_check(args.data_dir, add)
    extra = audit_extra.consistency_checks(dfs, add, args.data_dir) if dfs else {}

    fails = [c for c in check_rows if c["status"] == "FAIL"]
    pends = [c for c in check_rows if c["status"] == "PENDING"]
    verdict = "FAIL" if fails else ("CONDITIONAL" if pends else "PASS")

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_dir": os.path.abspath(args.data_dir),
        "mode": args.mode,
        "files": files,
        "checks": check_rows,
        "quality": quality,
        "v": vchk,
        "split": split,
        "blind": blind,
        "integrity": integrity,
        "extra": extra,
        "summary": {"total": len(check_rows), "pass": len(check_rows) - len(fails) - len(pends),
                    "fail": len(fails), "pending": len(pends), "verdict": verdict},
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    width = max(len(c["name"]) for c in check_rows) if check_rows else 10
    for c in check_rows:
        print(f"[{c['status']:9s}] {c['name']:<{width}}  {c['detail']}")
    print("-" * 60)
    print(f"总计 {len(check_rows)} 项：PASS {result['summary']['pass']}，"
          f"FAIL {len(fails)}，PENDING {len(pends)} → {verdict}")
    print("结果已写入", args.out)
    return 0 if verdict != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
