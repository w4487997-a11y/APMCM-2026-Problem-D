# -*- coding: utf-8 -*-
"""阶段三：命中率根因与可行修复。

根因：分区基线用 λ=2、代价 ∈{0,4}，于是
    合法态（代价 4）能量 = 4
    非法态（只选 1 个）能量 = λ = 2
非法态反而更低，退火被困在单选取态，命中率恒为 0。

要点：要让“全部非法态严格差于全部合法态”，需要 λ > 最大代价。
      全池 52 宽一热下 λ=8 会把 |h| 推到 ~152（超 127），
      因此改为每组内按全池排名取前 K 个 A、前 K 个 B，一热宽度 2K。

本脚本：
  1. 复现基线（K=52, λ=2, 代价{0,4}）与命中率；
  2. 扫描 K 与 λ，检查 Ising 整数性、|h|≤127、非法/合法分离；
  3. 对可行配置跑 30 种子 × 10 样本的本地退火，报告命中率；
  4. 输出 SDK 可直接导入的整数 QUBO（NDJSON 证据 + npz）。
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
from stage2_quant_partition import (anneal_ising_batch, build_partition,
                                    ising_matrix, audit_partition)


def shortlist_block(rows, x, k):
    """按全池排名取前 k 个 A 与前 k 个 B（该 X 组内），返回 (left, right, sub_rows)。"""
    block = [r for r in rows if r["X"] == x]
    block = sorted(block, key=lambda r: (float(r["V_hat"]), int(r["id"])))
    a_order, b_order = [], []
    for r in block:
        if r["A"] not in a_order:
            a_order.append(r["A"])
        if r["B"] not in b_order:
            b_order.append(r["B"])
        if len(a_order) >= k and len(b_order) >= k:
            break
    A, B = set(a_order[:k]), set(b_order[:k])
    sub = [r for r in block if r["A"] in A and r["B"] in B]
    return sub


def build_custom(rows, x, k, lam, cap=0.02, cost_scale=4.0):
    """按 K 缩名单构造上三角 QUBO（代价 ∈{0,cost_scale}）。"""
    block = shortlist_block(rows, x, k)
    left = sorted({r["A"] for r in block})
    right = sorted({r["B"] for r in block})
    li = {a: i for i, a in enumerate(left)}
    ri = {b: i + len(left) for i, b in enumerate(right)}
    i = np.array([li[r["A"]] for r in block])
    j = np.array([ri[r["B"]] for r in block])
    raw = np.array([float(r["V_hat"]) for r in block])
    c = np.minimum(raw - raw.min(), cap) / cap
    q = np.eye(len(left) + len(right)) * -lam
    for s, e in [(0, len(left)), (len(left), len(q))]:
        q[s:e, s:e] += np.triu(np.full((e - s, e - s), 2 * lam), 1)
    q[np.ix_(range(len(left)), range(len(left), len(q)))] = 2 * lam
    q[i, j] = cost_scale * np.rint(c)
    return dict(block=block, left=left, right=right, q=q, offset=2 * lam, i=i, j=j)


def full_audit(part):
    q, i, j, off = part["q"], part["i"], part["j"], part["offset"]
    n_left = len(part["left"])
    h, J, K = C.ising(q, off)
    e = C.qubo_energies(q, off, i, j)
    illegal = []
    for a in range(n_left):
        for b in range(a + 1, n_left):
            illegal.append(off + q[a, a] + q[b, b] + q[a, b])
    for a in range(n_left):
        illegal.append(off + q[a, a])
    raw = np.array([float(r["V_hat"]) for r in part["block"]])
    return {
        "n_variables": int(q.shape[0]),
        "n_legal": int(len(e)),
        "h_max_abs": float(np.max(np.abs(h))),
        "J_max_abs": float(np.max(np.abs(J))),
        "integral_ising": bool(np.allclose(h, np.rint(h)) and np.allclose(J, np.rint(J))
                               and abs(K - round(K)) < 1e-9),
        "fits_8bit": bool(np.max(np.abs(h)) <= 127 and np.max(np.abs(J)) <= 127),
        "legal_min": float(e.min()),
        "legal_max": float(e.max()),
        "legal_ties": int(np.sum(e == e.min())),
        "illegal_min": float(min(illegal)),
        "strict_separation": bool(min(illegal) > e.max()),
        "separation_gap": float(min(illegal) - e.max()),
        "argmin_matches_raw": bool(np.argmin(e) == int(np.argmin(raw))),
        "group_raw_min": float(raw.min()),
        "group_material": "|".join(C.key(part["block"][int(np.argmin(raw))])),
        "qubo_sha256": C.sha256_array(q),
        "raw_second_gap": float(np.sort(raw)[1] - raw.min()),
    }


def run_hit(part, seeds=30, size_limit=10, **kw):
    q, off = part["q"], part["offset"]
    i, j = part["i"], part["j"]
    n_left = len(part["left"])
    M = ising_matrix(q, off)
    t0 = time.perf_counter()
    spins = anneal_ising_batch(M, seeds * size_limit, **kw)
    wall = time.perf_counter() - t0
    bits = ((spins[:, :-1] * spins[:, -1:] + 1) // 2).astype(int)
    raw = np.array([float(r["V_hat"]) for r in part["block"]])
    best_raw = float(raw.min())
    feasible = hits = 0
    flags = []
    for rb in bits:
        ones = np.flatnonzero(rb)
        hit = False
        if len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left:
            a, jj = int(ones[0]), int(ones[1])   # j 已是绝对列号
            idx = np.where((i == a) & (j == jj))[0]
            if len(idx):
                feasible += 1
                if abs(raw[idx[0]] - best_raw) < 1e-12:
                    hits += 1
                    hit = True
        flags.append(hit)
    return {"seeds": seeds, "samples": len(bits), "feasible": feasible,
            "feasibility_rate": feasible / len(bits),
            "hits": hits, "hit_rate": hits / len(bits),
            "runs_with_hit": sum(1 for c in range(seeds)
                                 if any(flags[c * size_limit:(c + 1) * size_limit])),
            "wall_s": wall}


def main():
    rows = C.ranked(C.read_csv(C.DATA / "q3_pool_predictions.csv"))
    out = {"diagnosis": {}, "scan": [], "runs": {}, "sdk_matrices": {}}

    # 1) 根因：基线 λ=2 的能级
    base = build_partition(rows, "O3")
    q, off, i, j = base["q"], base["offset"], base["i"], base["j"]
    e = C.qubo_energies(q, off, i, j)
    single = min(off + q[a, a] for a in range(52))
    out["diagnosis"] = {
        "baseline_lambda": 2.0,
        "cost_levels": sorted({float(v) for v in base["c"]}),
        "legal_min": float(e.min()), "legal_max": float(e.max()),
        "illegal_single_min": float(single),
        "illegal_beats_worst_legal": bool(single < e.max()),
        "note": "λ=2 时非法单选取态(2)优于代价 4 的合法态(4)，退火被困",
    }
    print(f"[根因] λ=2：合法 min={e.min():.0f} max={e.max():.0f}，"
          f"非法单选取={single:.0f} → 非法优于最差合法={out['diagnosis']['illegal_beats_worst_legal']}")

    # 2) 扫描 K/λ
    for k in (8, 12, 16, 20, 24, 52):
        for lam in (2.0, 4.0, 8.0):
            part = build_custom(rows, "O3", k, lam)
            a = full_audit(part)
            a.update({"K": k, "lambda": lam})
            out["scan"].append(a)
            print(f"[扫描] K={k:<3} λ={lam:<3} 变量={a['n_variables']:<3} "
                  f"|h|={a['h_max_abs']:>6.1f} |J|={a['J_max_abs']:.1f} "
                  f"整数={a['integral_ising']} 8位={a['fits_8bit']} 严格分离={a['strict_separation']} "
                  f"组内最优保留={a['argmin_matches_raw']}")

    # 3) 选可行配置与基线对比命中率
    candidates = [a for a in out["scan"] if a["fits_8bit"] and a["integral_ising"]
                  and a["strict_separation"] and a["argmin_matches_raw"]]
    candidates.sort(key=lambda a: (-a["K"], a["lambda"]))
    best = candidates[0] if candidates else None
    print(f"[选型] 严格分离且 8 位可行的最大名单 = {best['K'] if best else None}, "
          f"λ={best['lambda'] if best else None}")

    configs = {"baseline_K52_l2": dict(k=52, lam=2.0)}
    if best:
        configs[f"fixed_K{best['K']}_l{int(best['lambda'])}"] = dict(k=best["K"], lam=best["lambda"])
    for name, cfg in configs.items():
        part = build_custom(rows, "O3", cfg["k"], cfg["lam"])
        for label, kw in (("it30_a0.9", dict(iterations_per_t=30, alpha=0.9)),
                          ("it300_a0.99", dict(iterations_per_t=300, alpha=0.99))):
            r = run_hit(part, **kw)
            out["runs"][f"{name}__{label}"] = r
            print(f"[命中] {name:<18} {label:<10} 可行 {r['feasibility_rate']:.1%} "
                  f"命中 {r['hit_rate']:.1%} ({r['hits']}/{r['samples']}) 用时 {r['wall_s']:.1f}s")

    # 4) 导出选定配置的 SDK 矩阵（三组）
    export_cfg = best or {"K": 52, "lambda": 2.0}
    for x in ("O3", "NO2", "FO2"):
        part = build_custom(rows, x, export_cfg["K"], export_cfg["lambda"])
        a = full_audit(part)
        path = C.MATRICES / f"fixed_{x}_K{export_cfg['K']}_l{int(export_cfg['lambda'])}.npz"
        np.savez_compressed(
            path, qubo=part["q"], offset=np.array(part["offset"]),
            var_names=np.array([f"a:{e}" for e in part["left"]] + [f"b:{e}" for e in part["right"]]),
            raw_scores=np.array([float(r["V_hat"]) for r in part["block"]]),
            candidate_id=np.array([int(r["id"]) for r in part["block"]]),
            left_idx=part["i"], right_idx=part["j"],
        )
        out["sdk_matrices"][x] = {"file": path.name, "audit": a,
                                  "sha256": C.sha256_file(path)}
        print(f"[导出 {x}] {path.name} |h|={a['h_max_abs']:.0f} 合法 {a['n_legal']} "
              f"最优 {a['group_material']}")

    C.write_json(C.RESULTS / "stage3_hitrate_fix.json", out)
    print("写出 results/stage3_hitrate_fix.json")


if __name__ == "__main__":
    main()
