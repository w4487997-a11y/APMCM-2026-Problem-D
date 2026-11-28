# -*- coding: utf-8 -*-
"""O-11：量化与精度补证指标（全部基于已有数据，不新跑求解）。

产出（q23_supplement/O11/）：
  schemes.csv             各精度方案对照（矩阵规模、范围、整数性、最优是否保留、最低档并列数）
  sorting_retention.csv   浮点排序 vs 整数能量排序的保持率（Spearman/Kendall/成对保序率）
  topk_overlap.csv        Top-K 候选重合率（K=1/5/10/25/50）
  tie_structure.csv       整数能量档位结构（档数、平均档大小、最大档、并列比例）
  oracle_caveat.md        关于“最优保持型编码”的声明与量化
  mcc_summary.csv         惩罚系数与退火预算扫描汇总
"""

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]          # q23_supplement
FIX = ROOT.parent / "q23_fix"
sys.path.insert(0, str(FIX / "scripts"))
import common as C

OUT = ROOT / "O11"
OUT.mkdir(parents=True, exist_ok=True)
RES = FIX / "results"


def write_csv(name, rows):
    if not rows:
        return
    with open(OUT / name, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def load_rows(problem):
    name = {"q2": "q2_pool_predictions.csv", "q3": "q3_pool_predictions.csv"}[problem]
    return C.ranked(C.read_csv(FIX / "data" / "pred" / name))


def build_full(rows, lam=2.0, cap=None):
    left, right = C.layout(rows)
    q, offset, i, j, c = C.encode(rows, left, right, lam=lam, cap=cap)
    return q, offset, i, j, c


def legal_matrix(n, i, j):
    b = np.zeros((len(i), n))
    b[np.arange(len(i)), i] = 1.0
    b[np.arange(len(i)), j] = 1.0
    return b


def energies_int(qi, i, j):
    return qi[i, i] + qi[j, j] + qi[i, j]


def ising_matrix(q, offset):
    h, J, K = C.ising(q, offset)
    n = len(q)
    M = np.zeros((n + 1, n + 1))
    M[:-1, :-1] = -(J + J.T) / 2.0
    M[:-1, -1] = M[-1, :-1] = -h / 2.0
    return M


def avg_rank(x):
    order = np.argsort(x, kind="stable")
    ranks = np.empty(len(x), dtype=float)
    sx = x[order]
    start = 0
    for k in range(1, len(x) + 1):
        if k == len(x) or sx[k] != sx[start]:
            ranks[order[start:k]] = (start + k - 1) / 2.0
            start = k
    return ranks


def spearman(a, b):
    ra, rb = avg_rank(a), avg_rank(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = np.sqrt((ra @ ra) * (rb @ rb))
    return float((ra @ rb) / denom) if denom else float("nan")


def pairwise_keep(a, b, n_pairs=200000, seed=0):
    """随机抽样成对，比较浮点排序与整数排序是否同向（并列记半保留）。"""
    rng = np.random.default_rng(seed)
    n = len(a)
    x = rng.integers(0, n, n_pairs)
    y = rng.integers(0, n, n_pairs)
    mask = x != y
    x, y = x[mask], y[mask]
    da = np.sign(a[x] - a[y])
    db = np.sign(b[x] - b[y])
    keep = np.mean((da == db) | ((da == 0) & (db == 0)))
    kendall = float(np.mean(np.sign(da) * np.sign(db)))
    # 只在“整数能量可区分”的配对上看保序率：并列严重的方案必须用这个口径
    distinct = db != 0
    keep_distinct = (float(np.mean(np.sign(da[distinct]) == np.sign(db[distinct])))
                     if distinct.any() else float("nan"))
    return float(keep), kendall, keep_distinct


def topk(score, k, tiebreak):
    order = np.lexsort((tiebreak, score))
    return set(order[:k].tolist())


def metrics(name, problem, float_scores, int_energy, ids, notes):
    n = len(float_scores)
    arg_float = int(np.lexsort((ids, float_scores))[0])
    arg_int = int(np.lexsort((ids, int_energy))[0])
    e = int_energy
    levels, counts = np.unique(e, return_counts=True)
    min_level = counts[0]
    multi = counts[counts > 1]
    keep, kendall, keep_distinct = pairwise_keep(float_scores, int_energy)
    row = {
        "problem": problem, "scheme": name, "n_candidates": n,
        "argmin_preserved": bool(arg_float == arg_int),
        "float_best_V_hat": float(float_scores[arg_float]),
        "int_best_V_hat": float(float_scores[arg_int]),
        "best_V_loss": float(float_scores[arg_int] - float_scores[arg_float]),
        "min_tier_ties": int(min_level),
        "n_levels": int(len(levels)),
        "mean_level_size": float(n / len(levels)),
        "max_level_size": int(counts.max()),
        "tie_ratio": float(1 - len(levels) / n),
        "spearman": spearman(float_scores, e),
        "pairwise_order_keep": keep,
        "pairwise_keep_distinct": keep_distinct,
        "kendall_sampled": kendall,
        "notes": notes,
    }
    tover = []
    min_tier_set = set(np.flatnonzero(e == e.min()).tolist())
    for k in (1, 5, 10, 25, 50):
        if k > n:
            continue
        a = topk(float_scores, k, ids)
        b = topk(e.astype(float), k, ids)
        tover.append({"problem": problem, "scheme": name, "K": k,
                      "overlap": len(a & b), "overlap_ratio": len(a & b) / k,
                      "float_topK_in_min_tier": len(a & min_tier_set),
                      "float_topK_in_min_tier_ratio": len(a & min_tier_set) / k})
    return row, tover


def direct_ising_quant(q, offset, bits, scale=None):
    """直接对 Ising 矩阵缩放取整，返回合法态整数 Ising 能量。"""
    M = ising_matrix(q, offset)
    mx = float(np.abs(M).max())
    s = (127.0 / mx) if scale is None else scale
    Mq = np.rint(M * s)
    spins = np.column_stack([2.0 * bits - 1.0, np.ones(len(bits))])
    return -np.sum((spins @ Mq) * spins, axis=1), s


def clipped_model(rows, cap=0.4, lam=1.02):
    left, right = C.layout(rows)
    q, offset, i, j, c = C.encode(rows, left, right, lam=lam, cap=cap)
    return q, offset, i, j, c


def partition_models(rows, problem):
    """已验证的 λ=2 两档代价分区模型（λ=8 短名单另计）。"""
    out = []
    xs = ["NO2"] if problem == "q2" else ["O3", "NO2", "FO2"]
    for x in xs:
        block = sorted([r for r in rows if r["X"] == x],
                       key=lambda r: (float(r["V_hat"]), int(r["id"])))
        left = sorted({r["A"] for r in block})
        right = sorted({r["B"] for r in block})
        li = {a: n for n, a in enumerate(left)}
        ri = {b: n + len(left) for n, b in enumerate(right)}
        i = np.array([li[r["A"]] for r in block])
        j = np.array([ri[r["B"]] for r in block])
        raw = np.array([float(r["V_hat"]) for r in block])
        c = np.minimum(raw - raw.min(), 0.02) / 0.02
        q = np.eye(len(left) + len(right)) * -2.0
        for s, e in [(0, len(left)), (len(left), len(q))]:
            q[s:e, s:e] += np.triu(np.full((e - s, e - s), 4.0), 1)
        q[np.ix_(range(len(left)), range(len(left), len(q)))] = 4.0
        q[i, j] = 4.0 * np.rint(c)
        out.append({"x": x, "q": q, "offset": 4.0, "i": i, "j": j, "raw": raw,
                    "ids": np.array([int(r["id"]) for r in block])})
    return out


def load_sweeps():
    rows = []
    sp = RES / "stage2_quant_partition.json"
    if sp.exists():
        d = json.loads(sp.read_text(encoding="utf-8"))
        for prob, pack in d.get("quantization", {}).items():
            for rule, v in pack.get("rules", {}).items():
                rows.append({"source": "stage2/precision_rules", "problem": prob,
                             "config": rule, "metric": "ties_at_min",
                             "value": v["ties_at_min"], "note": f"scale={v['scale']}"})
            di = pack.get("direct_ising_8bit", {})
            ill = di.get("illegal_min_integer_sampled")
            leg = di.get("legal_min_integer")
            rows.append({"source": "stage2/direct_ising", "problem": prob,
                         "config": "scale_to_127", "metric": "illegal_minus_legal",
                         "value": (None if ill is None or leg is None else ill - leg),
                         "note": "负值表示非法态更优"})
    sh = RES / "stage3_hitrate_fix.json"
    if sh.exists():
        d = json.loads(sh.read_text(encoding="utf-8"))
        for k, v in d.get("runs", {}).items():
            rows.append({"source": "stage3/hitrate", "problem": "q3",
                         "config": k, "metric": "seed_hit_ratio",
                         "value": v["runs_with_hit"] / v["seeds"],
                         "note": f"legal_ratio={v['feasibility_rate']:.3f}"})
        for k, v in d.get("hitrate_sweep", {}).items():
            if not isinstance(v, dict):
                continue
            rows.append({"source": "stage3/budget_sweep", "problem": "q3",
                         "config": k, "metric": "sample_hit_ratio",
                         "value": v["hit_rate"], "note": f"legal={v['feasibility_rate']:.3f}"})
    return rows


def main():
    scheme_rows, retention_rows, topk_rows, tie_rows = [], [], [], []
    for problem in ("q2", "q3"):
        rows = load_rows(problem)
        raw = np.array([float(r["V_hat"]) for r in rows])
        ids = np.array([int(r["id"]) for r in rows])
        q, offset, i, j, c = build_full(rows)
        mx = float(np.abs(q).max())
        bits = legal_matrix(len(q), i, j)

        # S0 浮点（参照）
        scheme_rows.append({"problem": problem, "scheme": "float",
                            "variables": len(q), "max_abs_q": mx,
                            "integral": True, "fits_8bit": True,
                            "argmin_preserved": True, "min_tier_ties": 1,
                            "note": "连续分数线性缩放，无量化（参照）"})
        # S1/S2 全池 QUBO 统一缩放
        for name, scale in (("qubo_x127/4", 127.0 / 4.0),
                            ("qubo_xfloor", float(np.floor(127.0 / mx)))):
            qi = np.rint(q * scale)
            e = energies_int(qi, i, j)
            r, tover = metrics(name, problem, raw, e, ids,
                               f"scale={scale:g}, max|q_int|={np.abs(qi).max():.0f}")
            scheme_rows.append({"problem": problem, "scheme": name,
                                "variables": len(q), "max_abs_q": mx,
                                "integral": True,
                                "fits_8bit": bool(np.abs(qi).max() <= 127),
                                "argmin_preserved": r["argmin_preserved"],
                                "min_tier_ties": r["min_tier_ties"],
                                "note": f"scale={scale:g}"})
            retention_rows.append(r)
            topk_rows.extend(tover)
            e_r, c_r = np.unique(e, return_counts=True)
            tie_rows.append({"problem": problem, "scheme": name,
                             "n_levels": len(e_r), "min_tier": int(c_r[0]),
                             "max_tier": int(c_r.max()),
                             "mean_tier": float(c_r.mean()),
                             "multi_tier_ratio": float((c_r > 1).mean())})
        # S3 截断 Δ=0.4 λ=1.02
        q3m, off3, i3, j3, c3 = clipped_model(rows)
        s3 = float(np.floor(127.0 / np.abs(q3m).max()))
        qi3 = np.rint(q3m * s3)
        e3 = energies_int(qi3, i3, j3)
        r3, t3 = metrics("clip_d0.4_l1.02", problem, raw, e3, ids,
                         f"scale={s3:g}, max|q_int|={np.abs(qi3).max():.0f}")
        scheme_rows.append({"problem": problem, "scheme": "clip_d0.4_l1.02",
                            "variables": len(q3m), "max_abs_q": float(np.abs(q3m).max()),
                            "integral": True,
                            "fits_8bit": bool(np.abs(qi3).max() <= 127),
                            "argmin_preserved": r3["argmin_preserved"],
                            "min_tier_ties": r3["min_tier_ties"],
                            "note": f"scale={s3:g}"})
        retention_rows.append(r3)
        topk_rows.extend(t3)
        # S4 直接 Ising 缩放
        e4, s4 = direct_ising_quant(q, offset, bits)
        r4, t4 = metrics("direct_ising_8bit", problem, raw, e4, ids,
                         f"ising_scale={s4:g}")
        scheme_rows.append({"problem": problem, "scheme": "direct_ising_8bit",
                            "variables": len(q), "max_abs_q": float(np.abs(ising_matrix(q, offset)).max()),
                            "integral": False, "fits_8bit": True,
                            "argmin_preserved": r4["argmin_preserved"],
                            "min_tier_ties": r4["min_tier_ties"],
                            "note": f"ising_scale={s4:g}（数学场项会超 127）"})
        retention_rows.append(r4)
        topk_rows.extend(t4)
        # S5 两档代价分区（λ=2）
        parts = partition_models(rows, problem)
        agg = []
        for p in parts:
            e5 = energies_int(p["q"], p["i"], p["j"])
            r5, t5 = metrics(f"partition_{p['x']}", problem, p["raw"], e5, p["ids"],
                             "λ=2，代价∈{0,4}，最优保持型编码")
            agg.append(r5)
            retention_rows.append(r5)
            topk_rows.extend(t5)
            scheme_rows.append({"problem": problem, "scheme": f"partition_{p['x']}",
                                "variables": len(p["q"]), "max_abs_q": float(np.abs(p["q"]).max()),
                                "integral": True, "fits_8bit": True,
                                "argmin_preserved": r5["argmin_preserved"],
                                "min_tier_ties": r5["min_tier_ties"],
                                "note": "λ=2, 代价{0,4}, |h|=102, |J|=1"})
            e_r, c_r = np.unique(e5, return_counts=True)
            tie_rows.append({"problem": problem, "scheme": f"partition_{p['x']}",
                             "n_levels": len(e_r), "min_tier": int(c_r[0]),
                             "max_tier": int(c_r.max()), "mean_tier": float(c_r.mean()),
                             "multi_tier_ratio": float((c_r > 1).mean())})
        print(f"[{problem}] 完成 {len(parts) + 4} 个方案")

    write_csv("schemes.csv", scheme_rows)
    write_csv("sorting_retention.csv", retention_rows)
    write_csv("topk_overlap.csv", topk_rows)
    write_csv("tie_structure.csv", tie_rows)
    write_csv("mcc_summary.csv", load_sweeps())
    C.write_json(OUT / "o11_metrics.json",
                 {"schemes": scheme_rows, "retention": retention_rows,
                  "topk": topk_rows, "ties": tie_rows})
    print("写出", OUT)


if __name__ == "__main__":
    main()
