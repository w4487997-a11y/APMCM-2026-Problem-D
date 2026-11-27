# -*- coding: utf-8 -*-
"""阶段二：Q3 8 位量化的合法性分析 + 三组 104 位分区模型 + 命中率实验。

A. 全池 QUBO 按两种取整规则量化后的最低档并列数（期望 21 / 24）；
B. 全池直接缩放 Ising 到 8 位后非法态反超合法态的反例；
C. 三组 104 位整数分区模型：Ising 系数全整数、|h|≤127，组内唯一最优保留；
D. 本地 SA（复刻 SDK 参数）批量并行，30 种子 × 10 样本的命中率与参数扫描。

注意：D 是本地复现实现，不是 SDK 运行；SDK 求解需要 license。
"""

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C


# ---------- A. QUBO 量化规则 ----------
def qubo_quant_ties(q, i, j, scale):
    qi = np.rint(q * scale)
    e = qi[i, i] + qi[j, j] + qi[i, j]
    m = e.min()
    return int(np.sum(e - m < 1e-9)), float(m), qi


def scale_rules(q):
    mx = float(np.abs(q).max())
    return {"exact_127_over_4": 127.0 / 4.0, "floor_127_over_4": float(np.floor(127.0 / mx))}


# ---------- B. 直接 Ising 8 位缩放 ----------
def ising_matrix(q, offset):
    h, J, K = C.ising(q, offset)
    n = len(q)
    M = np.zeros((n + 1, n + 1))
    M[:-1, :-1] = -(J + J.T) / 2.0
    M[:-1, -1] = M[-1, :-1] = -h / 2.0
    return M


def ising_direct_8bit(q, offset, legal_bits, cut, n_illegal=200000, seed=7):
    M = ising_matrix(q, offset)
    mx = float(np.abs(M).max())
    scale = 127.0 / mx
    Mq = np.rint(M * scale)
    spins = np.column_stack([2.0 * legal_bits - 1.0, np.ones(len(legal_bits))])
    e_legal = -np.sum((spins @ Mq) * spins, axis=1)
    rng = np.random.default_rng(seed)
    n = len(q)
    e_illegal_min = np.inf
    for _ in range(max(1, n_illegal // 1000)):
        bits = np.zeros((1000, n))
        kind = rng.integers(0, 2, 1000)
        for t in range(1000):
            if kind[t] == 0:
                a, b = rng.choice(cut, 2, replace=False)
                bits[t, a] = bits[t, b] = 1
            else:
                bits[t, rng.integers(0, cut)] = 1
        sp = np.column_stack([2.0 * bits - 1.0, np.ones(1000)])
        e = -np.sum((sp @ Mq) * sp, axis=1)
        e_illegal_min = min(e_illegal_min, float(e.min()))
    return {
        "ising_max_abs_float": mx,
        "scale_to_127": scale,
        "max_abs_after_round": float(np.abs(Mq).max()),
        "legal_min_integer": float(e_legal.min()),
        "legal_max_integer": float(e_legal.max()),
        "illegal_min_integer_sampled": e_illegal_min,
        "illegal_beats_legal": bool(e_illegal_min < e_legal.min()),
        "legal_ties_at_min": int(np.sum(e_legal == e_legal.min())),
        "integral_fraction": float(np.mean(Mq == Mq)),
    }


# ---------- C. 三组 104 位分区模型 ----------
def build_partition(rows, x, lam=2.0, cap=0.02):
    block = [r for r in rows if r["X"] == x]
    left, right = C.layout(block)
    q, k, i, j, c = C.encode(block, left, right, lam=lam, cap=cap)
    q[i, j] = 4.0 * np.rint(c)
    return dict(block=block, left=left, right=right, q=q, offset=k, i=i, j=j, c=q[i, j])


def audit_partition(part, x):
    q, i, j, off = part["q"], part["i"], part["j"], part["offset"]
    h, J, K = C.ising(q, off)
    e = C.qubo_energies(q, off, i, j)
    raw = np.array([float(r["V_hat"]) for r in part["block"]])
    order = np.argsort(raw)
    best = int(order[0])
    n_left = len(part["left"])
    illegal = []
    for a, b in itertools.combinations(range(n_left), 2):
        illegal.append(off + q[a, a] + q[b, b] + q[a, b])
    for a in range(n_left):
        illegal.append(off + q[a, a])
    return {
        "x": x,
        "n_variables": int(q.shape[0]),
        "n_legal": int(len(e)),
        "offset": float(off),
        "h_max_abs": float(np.max(np.abs(h))),
        "J_max_abs": float(np.max(np.abs(J))),
        "ising_all_integral": bool(np.allclose(h, np.rint(h))
                                   and np.allclose(J, np.rint(J))
                                   and abs(K - round(K)) < 1e-9),
        "ising_constant": float(K),
        "legal_min_energy": float(e.min()),
        "legal_min_ties": int(np.sum(e == e.min())),
        "legal_max_energy": float(e.max()),
        "illegal_min_energy": float(min(illegal)),
        "illegal_separation": float(min(illegal) - e.min()),
        "group_raw_min": float(raw.min()),
        "group_raw_argmin": "|".join(C.key(part["block"][best])),
        "group_raw_second_gap": float(raw[order[1]] - raw[order[0]]),
        "matrix_argmin_matches_raw": bool(np.argmin(e) == best),
        "cost_levels": sorted({float(v) for v in part["c"]}),
        "qubo_sha256": C.sha256_array(q),
        "raw_second": float(raw[order[1]]),
    }


# ---------- D. 本地退火（复刻 SDK 参数，批量并行） ----------
def self_test_annealer():
    rng = np.random.default_rng(0)
    n = 6
    A = rng.normal(size=(n + 1, n + 1))
    M = (A + A.T) / 2
    M[-1, :] = M[:, -1] = rng.normal(size=n + 1) * 0.5
    s = np.column_stack([rng.choice([-1, 1], size=(1, n)), np.ones(1)]).astype(float)
    k = 2
    f = float((s @ M)[0, k])
    e0 = -float(s @ M @ s.T)
    s2 = s.copy()
    s2[0, k] *= -1
    e1 = -float(s2 @ M @ s2.T)
    return abs((e1 - e0) - 4.0 * s[0, k] * f) < 1e-9


def anneal_ising_batch(M, n_chains, seed=12345, iterations_per_t=30, alpha=0.9,
                       t_start_factor=2.0, t_stop_factor=1e-3):
    rng = np.random.default_rng(seed)
    n = M.shape[0] - 1
    mx = float(np.abs(M).max())
    T, T_min = t_start_factor * mx, t_stop_factor * mx
    cur = rng.choice([-1, 1], size=(n_chains, n)).astype(np.int8)
    best = cur.copy()
    s = np.column_stack([cur.astype(float), np.ones(n_chains)])
    best_e = -np.einsum("ij,ij->i", s @ M, s)
    rows = np.arange(n_chains)
    eye = np.eye(n + 1)
    while T > T_min:
        for _ in range(iterations_per_t):
            k = rng.integers(0, n, size=n_chains)
            s = np.column_stack([cur.astype(float), np.ones(n_chains)])
            f = np.einsum("ij,ij->i", s @ M, eye[k])
            delta = 4.0 * cur[rows, k] * f
            accept = (delta <= 0) | (rng.random(n_chains) < np.exp(-np.maximum(delta, 0.0) / max(T, 1e-12)))
            cur[rows[accept], k[accept]] *= -1
        s = np.column_stack([cur.astype(float), np.ones(n_chains)])
        e = -np.einsum("ij,ij->i", s @ M, s)
        better = e < best_e
        best[better] = cur[better]
        best_e[better] = e[better]
        T *= alpha
    return np.column_stack([best.astype(float), np.ones(n_chains)])


def run_hitrate(q, offset, raw, i, j, seeds=30, size_limit=10, **kw):
    M = ising_matrix(q, offset)
    spins = anneal_ising_batch(M, seeds * size_limit, **kw)
    bits = ((spins[:, :-1] * spins[:, -1:] + 1) // 2).astype(int)
    best_raw = float(raw.min())
    feasible = hits = 0
    hit_flags = []
    for row_bits in bits:
        ones = np.flatnonzero(row_bits)
        hit = False
        if len(ones) == 2 and ones[0] < 52 and ones[1] >= 52:
            a, jj = int(ones[0]), int(ones[1])   # j 已是绝对列号
            idx = np.where((i == a) & (j == jj))[0]
            if len(idx):
                feasible += 1
                if abs(raw[idx[0]] - best_raw) < 1e-12:
                    hits += 1
                    hit = True
        hit_flags.append(hit)
    runs_with_hit = sum(1 for c in range(seeds) if any(hit_flags[c * size_limit:(c + 1) * size_limit]))
    return {"seeds": seeds, "samples": len(bits), "feasible": feasible,
            "feasibility_rate": feasible / len(bits),
            "raw_opt_hits": hits, "raw_opt_hit_rate": hits / len(bits),
            "runs_with_hit": runs_with_hit}


def main():
    out = {"quantization": {}, "partition": {}, "hitrate": {}, "meta": {}}
    rows_q2 = C.ranked(C.read_csv(C.DATA / "q2_pool_predictions.csv"))
    rows_q3 = C.ranked(C.read_csv(C.DATA / "q3_pool_predictions.csv"))

    for tag, rows in (("q2", rows_q2), ("q3", rows_q3)):
        left, right = C.layout(rows)
        q, off, i, j, _ = C.encode(rows, left, right)
        rules = scale_rules(q)
        entry = {"max_abs_q": float(np.abs(q).max()), "rules": {}}
        for name, s in rules.items():
            ties, emin, qi = qubo_quant_ties(q, i, j, s)
            entry["rules"][name] = {"scale": float(s), "ties_at_min": ties,
                                    "integer_min_energy": emin,
                                    "max_abs_int_q": float(np.abs(qi).max())}
        bits = C.legal_decisions(len(q), i, j)
        entry["direct_ising_8bit"] = ising_direct_8bit(q, off, bits, 52 if tag == "q2" else 156)
        out["quantization"][tag] = entry
        print(f"[{tag}] 量化并列 127/4→{entry['rules']['exact_127_over_4']['ties_at_min']} "
              f"floor→{entry['rules']['floor_127_over_4']['ties_at_min']} | "
              f"直接 Ising 8 位非法反超={entry['direct_ising_8bit']['illegal_beats_legal']}")

    parts = {}
    for x in ("O3", "NO2", "FO2"):
        part = build_partition(rows_q3, x)
        info = audit_partition(part, x)
        parts[x] = part
        out["partition"][x] = info
        np.savez_compressed(
            C.MATRICES / f"partition_{x}_qubo.npz",
            qubo=part["q"], offset=np.array(part["offset"]),
            var_names=np.array([f"a:{a}" for a, _ in part["left"]] + [f"b:{b}" for b in part["right"]]),
            raw_scores=np.array([float(r["V_hat"]) for r in part["block"]]),
            left_idx=part["i"], right_idx=part["j"],
            candidate_id=np.array([int(r["id"]) for r in part["block"]]),
        )
        print(f"[{x}] 变量 {info['n_variables']} |h|={info['h_max_abs']:.0f} |J|={info['J_max_abs']:.0f} "
              f"整数Ising={info['ising_all_integral']} 组内最优={info['group_raw_argmin']} "
              f"保留={info['matrix_argmin_matches_raw']} 并列={info['legal_min_ties']} "
              f"非法间隙={info['illegal_separation']:.0f} 次优差={info['group_raw_second_gap']:.6f}")

    group_min = {x: out["partition"][x]["group_raw_min"] for x in parts}
    winner = min(group_min, key=group_min.get)
    out["meta"] = {"group_minima": group_min, "group_winner": winner,
                   "winner_material": out["partition"][winner]["group_raw_argmin"],
                   "self_test_delta_ok": self_test_annealer()}
    print(f"[组间] {group_min} -> {winner}: {out['meta']['winner_material']}")

    base = dict(iterations_per_t=30, alpha=0.9, size_limit=10)
    for x in ("O3", "NO2", "FO2"):
        raw = np.array([float(r["V_hat"]) for r in parts[x]["block"]])
        t0 = time.perf_counter()
        res = run_hitrate(parts[x]["q"], parts[x]["offset"], raw,
                          parts[x]["i"], parts[x]["j"], **base)
        res["wall_s"] = time.perf_counter() - t0
        out["hitrate"][f"{x}_base"] = res
        print(f"[命中 {x}] 可行 {res['feasible']}/{res['samples']} 命中 {res['raw_opt_hits']} "
              f"({res['raw_opt_hit_rate']:.1%}) {res['wall_s']:.1f}s")

    sweep = {}
    for it in (30, 100, 300):
        for alpha in (0.9, 0.99):
            raw = np.array([float(r["V_hat"]) for r in parts["O3"]["block"]])
            key = f"O3_it{it}_a{alpha}"
            t0 = time.perf_counter()
            res = run_hitrate(parts["O3"]["q"], parts["O3"]["offset"], raw,
                              parts["O3"]["i"], parts["O3"]["j"],
                              iterations_per_t=it, alpha=alpha)
            res["wall_s"] = time.perf_counter() - t0
            sweep[key] = res
            print(f"[扫描 O3] it={it} a={alpha} 可行 {res['feasibility_rate']:.1%} "
                  f"命中 {res['raw_opt_hit_rate']:.1%} {res['wall_s']:.1f}s")
    out["hitrate_sweep"] = sweep
    C.write_json(C.RESULTS / "stage2_quant_partition.json", out)
    print("写出 results/stage2_quant_partition.json")


if __name__ == "__main__":
    main()
