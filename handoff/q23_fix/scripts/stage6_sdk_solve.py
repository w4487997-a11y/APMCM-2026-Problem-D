# -*- coding: utf-8 -*-
"""阶段六：Kaiwu SDK 求解入口（本机缺 license，需在授权环境运行）。

用法：
    set KW_USER_ID=xxxx
    set KW_SDK_CODE=xxxx
    python stage6_sdk_solve.py --npz ../matrices/fixed_O3_K24_l8.npz \
        --seeds 30 --samples-per-run 10 --iterations 300 --alpha 0.99

设计：
  - 矩阵 -> kw.core.qubo_matrix_to_qubo_model / qubo_matrix_to_ising_matrix（真实 SDK 路径）
  - 8 位适配：优先 kw.preprocess.adjust_ising_matrix_precision；
    该模块在本机被系统策略拦截时，退回本地实现（round 到整数并检查范围），并明确标注
  - 30 个固定种子，每个种子返回 samples_per_run 个样本
  - 逐样本独立解码：独热合法性、候选池内合法性、原尺度 V̂、与浮点最优差距
  - 原始样本与汇总分别落盘
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C


def local_8bit_adapt(matrix):
    """本地 8 位适配：整体乘 2^k 后四舍五入，保证 max|·| ≤ 127。"""
    mx = float(np.abs(matrix).max())
    factor = 1.0
    while mx * factor > 127.0:
        factor /= 2.0
    out = np.rint(matrix * factor)
    return out, {"method": "local_round", "factor": factor, "max_abs": float(np.abs(out).max())}


def adapt_8bit(matrix):
    try:
        import kaiwu as kw
        adj = np.asarray(kw.preprocess.adjust_ising_matrix_precision(matrix.copy(), bit_width=8))
        return adj, {"method": "sdk_preprocess", "max_abs": float(np.abs(adj).max())}
    except Exception as exc:
        adj, info = local_8bit_adapt(matrix)
        info["sdk_preprocess_error"] = f"{type(exc).__name__}: {exc}"
        return adj, info


def decode_spins(spins):
    return ((spins[:, :-1] * spins[:, -1:] + 1) // 2).astype(int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--samples-per-run", type=int, default=10)
    ap.add_argument("--iterations", type=int, default=300)
    ap.add_argument("--alpha", type=float, default=0.99)
    ap.add_argument("--regime", choices=["unadjusted", "adjusted", "both"], default="both")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    z = C.load_matrix(args.npz)
    q = z["qubo"]
    offset = z["offset"]
    names = z["var_names"]
    raw_scores = z["raw_scores"]
    left = None if z["left_idx"] is None else z["left_idx"].astype(int)
    right = None if z["right_idx"] is None else z["right_idx"].astype(int)
    tag = args.tag or Path(args.npz).stem

    import kaiwu as kw
    from importlib import metadata
    model = kw.core.qubo_matrix_to_qubo_model(q.copy())
    matrix, bias = kw.core.qubo_matrix_to_ising_matrix(q.copy(), decimal=False)
    matrix = np.asarray(matrix, dtype=float)

    n_left = int(sum(not s.startswith("b:") for s in names))
    raw_min = float(raw_scores.min())
    key_min = None
    regimes = {"unadjusted": matrix}
    if args.regime in ("adjusted", "both"):
        adj, info = adapt_8bit(matrix)
        regimes["sdk_8bit_adjusted"] = adj
        print("8 位适配:", info)
    else:
        info = {"method": "none"}

    samples, runs = [], []
    for regime, M in regimes.items():
        mx = float(np.abs(M).max())
        for seed in range(args.seeds):
            opt = kw.classical.SimulatedAnnealingOptimizer(
                initial_temperature=2 * mx, cutoff_temperature=1e-3 * mx,
                alpha=args.alpha, iterations_per_t=args.iterations,
                size_limit=args.samples_per_run, rand_seed=seed, process_num=1,
                flag_evolution_history=False, verbose=False)
            t0 = time.perf_counter()
            spins = np.asarray(opt.solve(M.copy(), negtail_flip=False, sort_solutions=False))
            wall = (time.perf_counter() - t0) * 1000
            bits = decode_spins(spins)
            hits = feasible = 0
            for sid, (bit, sv) in enumerate(zip(bits, spins)):
                ones = np.flatnonzero(bit)
                legal = bool(len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left)
                score = None
                if legal and left is not None:
                    idx = np.where((left == ones[0]) & (right == ones[1]))[0]
                    if len(idx):
                        score = float(raw_scores[idx[0]])
                if score is not None:
                    feasible += 1
                    if abs(score - raw_min) < 1e-12:
                        hits += 1
                samples.append({"case": tag, "regime": regime, "seed": seed, "sample": sid,
                                "spin": " ".join(str(int(v)) for v in sv),
                                "energy_sdk": float(opt.get_hamiltonian()[sid]),
                                "legal": legal,
                                "V_hat": None if score is None else score,
                                "gap_to_float_optimum":
                                    None if score is None else score - raw_min})
            runs.append({"case": tag, "regime": regime, "seed": seed,
                         "returned": len(spins), "feasible": feasible, "hits": hits,
                         "wall_ms": wall})
        print(f"[{regime}] {args.seeds} 种子完成，样本 {len(samples)} 条")

    out = C.RESULTS / f"sdk_run_{tag}.json"
    C.write_json(out, {
        "kaiwu_version": metadata.version("kaiwu"),
        "matrix_file": str(args.npz), "matrix_sha256": C.sha256_file(Path(args.npz)),
        "qubo_sha256": C.sha256_array(q), "offset": offset,
        "sdk_spins": int(matrix.shape[0]), "sdk_bias": float(bias),
        "n_left": n_left, "raw_min": raw_min, "adapt_info": info,
        "config": {"seeds": args.seeds, "samples_per_run": args.samples_per_run,
                   "iterations_per_t": args.iterations, "alpha": args.alpha},
        "summary": {reg: {"runs": sum(1 for r in runs if r["regime"] == reg),
                          "samples": sum(r["returned"] for r in runs if r["regime"] == reg),
                          "feasible": sum(r["feasible"] for r in runs if r["regime"] == reg),
                          "hits": sum(r["hits"] for r in runs if r["regime"] == reg)}
                    for reg in regimes},
        "runs": runs,
    })
    if samples:
        C.write_csv(C.RESULTS / f"sdk_samples_{tag}.csv", samples)
    print("写出", out)


if __name__ == "__main__":
    main()
