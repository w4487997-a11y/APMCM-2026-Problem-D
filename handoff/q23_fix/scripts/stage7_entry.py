# -*- coding: utf-8 -*-
"""正式复跑入口（对应复审意见第 1、2 条）。

一条命令走完：预测表校验 -> 建模型 -> 求解 -> 独立解码 -> 原尺度比较。

  python stage7_entry.py --problem q2              # 固定 NO2，104 位全池模型
  python stage7_entry.py --problem q3              # 三组 104 位，按原尺度 V̂ 比较
  python stage7_entry.py --problem all --iters 300 # 全流程

后端：
  --backend auto  有 license 用 SDK，否则用本地退火（结果里标注 backend）
  --backend sdk   强制 SDK（无 license 会明确失败）
  --backend local 强制本地退火（非 SDK）

矩阵由预测表现场重建，Q1 换模型后直接换 --pred 即可，不需要手工改字段。
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C

OFFICIAL = C.WORK / "task_a" / "data_real"
POOL_FILES = {
    ("q2", "full"): "07_castelli_q2_pool.csv",
    ("q2", "blind"): "11_castelli_q2_pool_blind.csv",
    ("q3", "full"): "08_castelli_q3_pool.csv",
    ("q3", "blind"): "12_castelli_q3_pool_blind.csv",
}
PRED_FILES = {
    ("q2", "full"): "q2_pool_predictions.csv",
    ("q3", "full"): "q3_pool_predictions.csv",
}


# ---------- 1. 严格校验：对齐官方候选池 ----------
def validate_strict(rows, problem, pool="full"):
    """行数/ID/组成/来源池/重复/缺失/有限/版本/常量表，逐项对齐官方池。"""
    official = C.read_csv(OFFICIAL / POOL_FILES[(problem, pool)])
    off_by_id = {r["id"]: r for r in official}
    problems = []
    if not rows:
        raise ValueError("空表")
    if len(rows) != len(official):
        problems.append(f"行数 {len(rows)} != 官方 {len(official)}")
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        problems.append("存在重复 id")
    missing = set(off_by_id) - set(ids)
    extra = set(ids) - set(off_by_id)
    if missing:
        problems.append(f"缺失官方候选 {len(missing)} 个（示例 {sorted(missing)[:3]}）")
    if extra:
        problems.append(f"池外 id {len(extra)} 个（示例 {sorted(extra)[:3]}）")
    for r in rows:
        off = off_by_id.get(r["id"])
        if off is not None and any(r[k] != off[k] for k in C.KEYS):
            problems.append(f"id {r['id']} 组成与官方不一致")
            break
    versions = {r.get("model_version", "") for r in rows}
    if len(versions) != 1 or "" in versions:
        problems.append(f"版本不唯一或为空: {versions}")
    if "pool" in rows[0] and {r["pool"] for r in rows} != {pool_label(problem, pool)}:
        problems.append(f"来源池字段不符: {{{','.join(sorted({r['pool'] for r in rows}))}}}")
    scores = np.array([float(r["V_hat"]) for r in rows])
    if not np.isfinite(scores).all():
        problems.append("存在非有限分数")
    if (scores < 0).any():
        problems.append("存在负分数")
    if np.ptp(scores) == 0:
        problems.append("常量表（分数全相同），拒绝归一化")
    if problems:
        raise ValueError("；".join(problems))
    order = np.argsort(scores, kind="stable")
    return {"rows": len(rows), "unique_ids": len(set(ids)),
            "model_version": versions.pop(),
            "score_min": float(scores.min()), "score_max": float(scores.max()),
            "first_gap": float(scores[order[1]] - scores[order[0]]),
            "ties_at_minimum": int(np.sum(scores == scores[order[0]])),
            "official_pool": POOL_FILES[(problem, pool)],
            "pool_sha256": C.sha256_file(OFFICIAL / POOL_FILES[(problem, pool)])}


def pool_label(problem, pool):
    return {("q2", "full"): "07", ("q2", "blind"): "11",
            ("q3", "full"): "08", ("q3", "blind"): "12"}[(problem, pool)]


# ---------- 2. 建模型 ----------
def build_q2(rows, lam=2.0):
    """固定 NO2：A 独热 + B 独热，104 位，代价按整池跨度缩放。"""
    left = sorted({(r["A"], r["X"]) for r in rows})
    right = sorted({r["B"] for r in rows})
    q, offset, i, j, c = C.encode(rows, left, right, lam=lam)
    names = [f"a:{a}" for a, _ in left] + [f"b:{b}" for b in right]
    return dict(problem="q2", group="NO2", q=q, offset=offset, names=names,
                i=i, j=j, block=rows, left=left, right=right, n_left=len(left))


def build_q3_group(rows, x, lam=8.0, cap=0.02, cost_scale=4.0, k=None):
    """单组 104 位（或 K 缩名单）模型；cost_scale=4 且 λ=8 时非法态严格劣于合法态。"""
    block = [r for r in rows if r["X"] == x]
    block = sorted(block, key=lambda r: (float(r["V_hat"]), int(r["id"])))
    if k:
        a_order, b_order = [], []
        for r in block:
            if r["A"] not in a_order:
                a_order.append(r["A"])
            if r["B"] not in b_order:
                b_order.append(r["B"])
            if len(a_order) >= k and len(b_order) >= k:
                break
        A, B = set(a_order[:k]), set(b_order[:k])
        block = [r for r in block if r["A"] in A and r["B"] in B]
    left = sorted({r["A"] for r in block})
    right = sorted({r["B"] for r in block})
    li = {a: n for n, a in enumerate(left)}
    ri = {b: n + len(left) for n, b in enumerate(right)}
    i = np.array([li[r["A"]] for r in block])
    j = np.array([ri[r["B"]] for r in block])
    raw = np.array([float(r["V_hat"]) for r in block])
    c = np.minimum(raw - raw.min(), cap) / cap
    q = np.eye(len(left) + len(right)) * -lam
    for s, e in [(0, len(left)), (len(left), len(q))]:
        q[s:e, s:e] += np.triu(np.full((e - s, e - s), 2 * lam), 1)
    q[np.ix_(range(len(left)), range(len(left), len(q)))] = 2 * lam
    q[i, j] = cost_scale * np.rint(c)
    return dict(problem="q3", group=x, q=q, offset=2 * lam,
                names=[f"a:{a}" for a in left] + [f"b:{b}" for b in right],
                i=i, j=j, block=block, left=left, right=right, n_left=len(left),
                raw=raw)


# ---------- 3. 求解后端 ----------
def ising_matrix(q, offset):
    h, J, K = C.ising(q, offset)
    n = len(q)
    M = np.zeros((n + 1, n + 1))
    M[:-1, :-1] = -(J + J.T) / 2.0
    M[:-1, -1] = M[-1, :-1] = -h / 2.0
    return M


def solve_sdk(M, seeds, samples, iters, alpha):
    import kaiwu as kw
    spins_all = []
    for seed in range(seeds):
        opt = kw.classical.SimulatedAnnealingOptimizer(
            initial_temperature=2 * float(np.abs(M).max()),
            cutoff_temperature=1e-3 * float(np.abs(M).max()),
            alpha=alpha, iterations_per_t=iters, size_limit=samples,
            rand_seed=seed, process_num=1, flag_evolution_history=False, verbose=False)
        spins_all.append(np.asarray(opt.solve(M.copy(), negtail_flip=False, sort_solutions=False)))
    return np.vstack(spins_all)


def solve_local(M, seeds, samples, iters, alpha):
    from stage2_quant_partition import anneal_ising_batch
    return anneal_ising_batch(M, seeds * samples, iterations_per_t=iters, alpha=alpha)


def pick_backend(name):
    if name in ("auto", "sdk"):
        try:
            import kaiwu  # noqa: F401
            try:
                probe = np.zeros((3, 3))
                solve_sdk(probe, 1, 1, 1, 0.9)
                return "sdk"
            except Exception as exc:
                if name == "sdk":
                    raise SystemExit(f"SDK 后端不可用：{type(exc).__name__}: {exc}")
                return "local"
        except ImportError:
            if name == "sdk":
                raise SystemExit("找不到 kaiwu 包")
            return "local"
    return "local"


# ---------- 4. 解码与统计 ----------
def evaluate(model, spins):
    q, offset, i, j = model["q"], model["offset"], model["i"], model["j"]
    n_left = model["n_left"]
    raw = np.array([float(r["V_hat"]) for r in model["block"]])
    best_raw = float(raw.min())
    bits = ((spins[:, :-1] * spins[:, -1:] + 1) // 2).astype(int)
    samples = slots = legal = hits = 0
    best_found = None
    per_seed = []
    for row_bits in bits:
        samples += 1
        ones = np.flatnonzero(row_bits)
        ok = len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left
        idx = None
        if ok:
            idx = np.where((i == ones[0]) & (j == ones[1]))[0]
            ok = len(idx) > 0
        if ok:
            legal += 1
            v = float(raw[idx[0]])
            best_found = v if best_found is None else min(best_found, v)
            if abs(v - best_raw) < 1e-12:
                hits += 1
        per_seed.append(ok and idx is not None and abs(float(raw[idx[0]]) - best_raw) < 1e-12)
    return {"samples": samples, "legal_samples": legal,
            "legal_ratio": legal / samples,
            "hit_samples": hits, "sample_hit_ratio": hits / samples,
            "best_V_hat": best_found,
            "gap_to_float_optimum": None if best_found is None else best_found - best_raw,
            "float_optimum_V_hat": best_raw,
            "material_at_float_optimum": "|".join(C.key(model["block"][int(np.argmin(raw))])),
            "per_sample_hit": per_seed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", choices=["q2", "q3", "all"], default="all")
    ap.add_argument("--pred", default=None, help="预测表路径；缺省用 v1 预测")
    ap.add_argument("--pool", choices=["full", "blind"], default="full")
    ap.add_argument("--backend", choices=["auto", "sdk", "local"], default="auto")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--samples", type=int, default=10)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--alpha", type=float, default=0.99)
    ap.add_argument("--k", type=int, default=None, help="Q3 每组缩名单宽度")
    args = ap.parse_args()

    backend = pick_backend(args.backend)
    results, table = {}, []
    problems = {"all": ["q2", "q3"]}.get(args.problem, [args.problem])

    for problem in problems:
        pred_path = Path(args.pred) if args.pred else C.DATA / PRED_FILES[(problem, args.pool)]
        rows = C.ranked(C.read_csv(pred_path))
        checks = validate_strict(rows, problem, args.pool)
        print(f"[{problem}] 校验通过：{checks['rows']} 行，版本 {checks['model_version']}，"
              f"首位差 {checks['first_gap']:.6f}")

        models = [build_q2(rows)] if problem == "q2" else [
            build_q3_group(rows, x, k=args.k) for x in ("O3", "NO2", "FO2")]
        for m in models:
            t0 = time.perf_counter()
            M = ising_matrix(m["q"], m["offset"])
            fn = solve_sdk if backend == "sdk" else solve_local
            spins = fn(M, args.seeds, args.samples, args.iters, args.alpha)
            wall = time.perf_counter() - t0
            stats = evaluate(m, spins)
            seed_hits = sum(1 for s in range(args.seeds)
                            if any(stats["per_sample_hit"][s * args.samples:(s + 1) * args.samples]))
            entry = {"problem": problem, "group": m["group"], "backend": backend,
                     "variables": int(len(m["q"])), "seeds": args.seeds,
                     "samples": stats["samples"], "legal_samples": stats["legal_samples"],
                     "legal_ratio": stats["legal_ratio"],
                     "hit_samples": stats["hit_samples"],
                     "sample_hit_ratio": stats["sample_hit_ratio"],
                     "seeds_with_hit": seed_hits,
                     "seed_hit_ratio": seed_hits / args.seeds,
                     "best_V_hat": stats["best_V_hat"],
                     "gap_to_float_optimum": stats["gap_to_float_optimum"],
                     "float_optimum_V_hat": stats["float_optimum_V_hat"],
                     "material_at_float_optimum": stats["material_at_float_optimum"],
                     "config": {"iters": args.iters, "alpha": args.alpha,
                                "k": args.k},
                     "wall_s": wall, "intake": checks,
                     "model_sha256": C.sha256_array(m["q"])}
            results.setdefault(problem, []).append(entry)
            table.append(entry)
            print(f"    {m['group']:<4} 变量 {entry['variables']:>3} 合法 {entry['legal_samples']:>3}/"
                  f"{entry['samples']} 样本命中 {entry['hit_samples']:>3} "
                  f"({entry['sample_hit_ratio']:.1%}) 种子命中 {seed_hits}/{args.seeds} "
                  f"({entry['seed_hit_ratio']:.1%}) 最佳 V̂={entry['best_V_hat']} "
                  f"{wall:.1f}s")

        if problem == "q3":
            best_by_group = {e["group"]: e["float_optimum_V_hat"] for e in results["q3"]}
            winner = min(best_by_group, key=best_by_group.get)
            w = next(e for e in results["q3"] if e["group"] == winner)
            print(f"[q3 原尺度比较] {best_by_group} -> {winner}: "
                  f"{w['material_at_float_optimum']} V̂={w['float_optimum_V_hat']:.6f}")
            results["q3_winner"] = {"group": winner,
                                    "material": w["material_at_float_optimum"],
                                    "V_hat": w["float_optimum_V_hat"],
                                    "group_minima": best_by_group}

    tag = f"{args.problem}_{backend}_it{args.iters}"
    out = C.RESULTS / f"entry_{tag}.json"
    C.write_json(out, {"backend": backend, "config": vars(args), "results": results})
    if table:
        flat = [{k: v for k, v in e.items() if k != "intake"} for e in table]
        C.write_csv(C.RESULTS / f"entry_{tag}_table.csv", flat)
    print("写出", out)


if __name__ == "__main__":
    main()
