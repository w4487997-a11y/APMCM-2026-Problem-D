# -*- coding: utf-8 -*-
"""正式复跑入口 v3（一次修完复审 P0/P1）。

与上一版的差别：
  1. 默认模型改为**已验收的 λ=2 全覆盖整数分区**（Q2 NO2 一组、Q3 三组），
     Ising 系数全整数、|h|=102 ≤127，SDK 8 位适配应为恒等变换；
     λ=8 只保留给 48 位短名单（需显式 --scheme shortlist）。
  2. 适配后强制自检：|h|/|J| 范围、整数性、非法见证是否低于合法最低；不通过直接失败。
  3. Q3 冠军只从**求解器实际返回的合法样本**中选；无合法返回写 solver_failed。
  4. SDK 探针使用非退化矩阵；--backend sdk 失败即报错，auto 回退打印原因。
  5. --pred-q2 / --pred-q3 分开传；默认数据随包（data/ 目录）。
  6. 归档每个模型的原始返回：自旋串、解码材料、合法性、能源、V̂。

用法示例：
    python stage7_entry.py --problem all --backend local --iters 300 --alpha 0.99
    python stage7_entry.py --problem q3 --scheme shortlist --shortlist-k 24
    python stage7_entry.py --problem all --pred-q2 ../data/pred/q2.csv --pred-q3 ../data/pred/q3.csv
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
DATA = PKG / "data"
POOL_FILES = {
    ("q2", "full"): "official/07_castelli_q2_pool.csv",
    ("q3", "full"): "official/08_castelli_q3_pool.csv",
    ("q2", "blind"): "official/11_castelli_q2_pool_blind.csv",
    ("q3", "blind"): "official/12_castelli_q3_pool_blind.csv",
}
PRED_FILES = {"q2": "pred/q2_pool_predictions.csv", "q3": "pred/q3_pool_predictions.csv"}
POOL_LABEL = {("q2", "full"): "07", ("q2", "blind"): "11",
              ("q3", "full"): "08", ("q3", "blind"): "12"}


# ---------- 1. 校验 ----------
def validate_strict(rows, problem, pool="full", data_dir=None):
    base = Path(data_dir) if data_dir else DATA
    official = C.read_csv(base / POOL_FILES[(problem, pool)])
    off = {r["id"]: r for r in official}
    label = POOL_LABEL[(problem, pool)]
    problems = []
    if len(rows) != len(official):
        problems.append(f"行数 {len(rows)} != 官方 {len(official)}")
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        problems.append("存在重复 id")
    missing, extra = set(off) - set(ids), set(ids) - set(off)
    if missing:
        problems.append(f"缺失官方候选 {len(missing)} 个（示例 {sorted(missing)[:3]}）")
    if extra:
        problems.append(f"池外 id {len(extra)} 个（示例 {sorted(extra)[:3]}）")
    for r in rows:
        o = off.get(r["id"])
        if o and any(r[k] != o[k] for k in C.KEYS):
            problems.append(f"id {r['id']} 组成与官方不一致")
            break
    for field in ("pool", "source_pool"):
        if field not in rows[0]:
            problems.append(f"缺少 {field} 列")
        elif {r[field] for r in rows} != {label}:
            problems.append(f"{field} 字段不符: {{{','.join(sorted({r[field] for r in rows}))}}}")
    versions = {r.get("model_version", "") for r in rows}
    if len(versions) != 1 or "" in versions:
        problems.append(f"版本不唯一或为空: {versions}")
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
    return {"rows": len(rows), "model_version": versions.pop(),
            "first_gap": float(scores[order[1]] - scores[order[0]]),
            "ties_at_minimum": int(np.sum(scores == scores[order[0]])),
            "pool": label,
            "official_sha256": C.sha256_file(base / POOL_FILES[(problem, pool)]),
            "prediction_sha256": None}


# ---------- 2. 模型（默认 λ=2 全覆盖整数分区） ----------
def build_partition(rows, x, lam=2.0, cap=0.02, cost_scale=4.0, k=None):
    block = sorted([r for r in rows if r["X"] == x],
                   key=lambda r: (float(r["V_hat"]), int(r["id"])))
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
                i=i, j=j, block=block, left=left, right=right,
                n_left=len(left), raw=raw, lam=lam)


def build_q2(rows, lam=2.0, cap=0.02, cost_scale=4.0):
    m = build_partition(rows, rows[0]["X"], lam=lam, cap=cap, cost_scale=cost_scale)
    m["problem"] = "q2"
    m["group"] = "NO2"
    return m


# ---------- 3. Ising 与 8 位适配 ----------
def ising_matrix(q, offset):
    h, J, K = C.ising(q, offset)
    n = len(q)
    M = np.zeros((n + 1, n + 1))
    M[:-1, :-1] = -(J + J.T) / 2.0
    M[:-1, -1] = M[-1, :-1] = -h / 2.0
    return M, h, J, K


def adapt_8bit(M):
    """优先 SDK 官方适配；不可用时用本地等价实现（整数矩阵即恒等）。"""
    try:
        import kaiwu as kw
        adj = np.asarray(kw.preprocess.adjust_ising_matrix_precision(M.copy(), bit_width=8))
        return adj, {"method": "sdk_preprocess", "max_abs": float(np.abs(adj).max())}
    except Exception as exc:
        adj = M.copy()
        info = {"method": "local_identity_check", "max_abs": float(np.abs(adj).max()),
                "sdk_error": f"{type(exc).__name__}: {str(exc)[:80]}"}
        return adj, info


def post_adapt_audit(M_adj, model, tol=1e-9):
    """适配后自检：范围、整数性、非法见证不得优于合法最低。"""
    h, J, K = C.ising_from_sdk_matrix(M_adj) if hasattr(C, "ising_from_sdk_matrix") else (None, None, None)
    n = len(model["q"])
    # 由适配矩阵反推 h、J（M[:-1,-1]=-h/2，M[:-1,:-1]=-(J+J.T)/2）
    h = -2.0 * M_adj[:-1, -1]
    Js = -2.0 * M_adj[:-1, :-1]
    J = np.triu(Js, 1)
    # SDK 约定 M_ij = -J_ij/2、M_i,ref = -h_i/2，矩阵本身为半整数属正常；
    # 8 位要求的是反推出来的 h、J 为整数且落在 ±127。
    integral = bool(np.allclose(h, np.rint(h), atol=1e-9) and
                    np.allclose(J, np.rint(J), atol=1e-9))
    maxh, maxJ = float(np.abs(h).max()), float(np.abs(J).max())
    spins = np.column_stack([2.0 * C.legal_decisions(n, model["i"], model["j"]) - 1.0,
                             np.ones(len(model["i"]))])
    e_legal = -np.sum((spins @ M_adj) * spins, axis=1)
    # 非法见证：单侧只选 1 个，另一侧全 0
    n_left = model["n_left"]
    bits = np.zeros((2, n))
    bits[0, 0] = 1
    bits[1, n_left] = 1
    sp = np.column_stack([2.0 * bits - 1.0, np.ones(2)])
    e_illegal = -np.sum((sp @ M_adj) * sp, axis=1)
    diff = float(e_illegal.min() - e_legal.min())
    return {
        "matrix_integral": integral, "h_max_abs": maxh, "J_max_abs": maxJ,
        "fits_8bit": bool(maxh <= 127 and maxJ <= 127),
        "legal_min_energy": float(e_legal.min()),
        "legal_ties_at_min": int(np.sum(np.abs(e_legal - e_legal.min()) < tol)),
        "illegal_witness_min_energy": float(e_illegal.min()),
        "illegal_minus_legal": diff,
        "passed": bool(integral and maxh <= 127 and maxJ <= 127 and diff > 0),
    }


# ---------- 4. 求解后端 ----------
def probe_sdk():
    """用非退化矩阵探测 SDK 可用性；返回 (ok, reason)。"""
    try:
        import kaiwu as kw
    except ImportError as exc:
        return False, f"import 失败: {exc}"
    M = np.array([[1.0, 0.0], [0.0, 1.0]])   # max|M|=1，温度正常
    try:
        opt = kw.classical.SimulatedAnnealingOptimizer(
            initial_temperature=2.0, cutoff_temperature=2e-3, alpha=0.9,
            iterations_per_t=2, size_limit=1, rand_seed=0, process_num=1,
            flag_evolution_history=False, verbose=False)
        opt.solve(M.copy(), negtail_flip=False, sort_solutions=False)
        return True, "ok"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {str(exc)[:120]}"


def solve_sdk(M, seeds, samples, iters, alpha):
    import kaiwu as kw
    out = []
    mx = max(float(np.abs(M).max()), 1.0)     # 防零温度
    for seed in range(seeds):
        opt = kw.classical.SimulatedAnnealingOptimizer(
            initial_temperature=2 * mx, cutoff_temperature=1e-3 * mx,
            alpha=alpha, iterations_per_t=iters, size_limit=samples,
            rand_seed=seed, process_num=1, flag_evolution_history=False, verbose=False)
        out.append(np.asarray(opt.solve(M.copy(), negtail_flip=False, sort_solutions=False)))
    return np.vstack(out)


def solve_local(M, seeds, samples, iters, alpha):
    from stage2_quant_partition import anneal_ising_batch
    return anneal_ising_batch(M, seeds * samples, iterations_per_t=iters, alpha=alpha)


# ---------- 5. 解码（只用返回样本） ----------
def evaluate_solvers(model, spins):
    n_left = model["n_left"]
    raw = model["raw"]
    bits = ((spins[:, :-1] * spins[:, -1:] + 1) // 2).astype(int)
    rows = []
    for sid, (b, sv) in enumerate(zip(bits, spins)):
        ones = np.flatnonzero(b)
        legal = bool(len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left)
        material, score = None, None
        if legal:
            idx = np.where((model["i"] == ones[0]) & (model["j"] == ones[1]))[0]
            if len(idx):
                material = "|".join(C.key(model["block"][idx[0]]))
                score = float(raw[idx[0]])
            else:
                legal = False
        rows.append({"sample": sid, "spin": "".join(str(int(v)) for v in sv),
                     "legal": legal, "material": material, "V_hat": score})
    legal_rows = [r for r in rows if r["legal"]]
    best = min(legal_rows, key=lambda r: r["V_hat"]) if legal_rows else None
    return rows, {"samples": len(rows), "legal_samples": len(legal_rows),
                  "legal_ratio": len(legal_rows) / len(rows),
                  "best_returned_material": None if best is None else best["material"],
                  "best_returned_V_hat": None if best is None else best["V_hat"]}


def seed_level_hits(model, spins, samples_per_seed, best_V):
    bits = ((spins[:, :-1] * spins[:, -1:] + 1) // 2).astype(int)
    n_left = model["n_left"]
    flags = []
    for b in bits:
        ones = np.flatnonzero(b)
        ok = False
        if len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left:
            idx = np.where((model["i"] == ones[0]) & (model["j"] == ones[1]))[0]
            ok = len(idx) and abs(float(model["raw"][idx[0]]) - best_V) < 1e-12
        flags.append(bool(ok))
    return sum(1 for s in range(len(flags) // samples_per_seed)
               if any(flags[s * samples_per_seed:(s + 1) * samples_per_seed]))


# ---------- 6. 主流程 ----------

def choose_winner(entries):
    """冠军只从“状态 ok（有合法返回样本）”的模型里选；否则明确失败。"""
    solved = [e for e in entries if e["status"] == "ok"]
    if not solved:
        return {"status": "solver_failed",
                "reason": "三组均无合法返回样本，不给出冠军"}
    w = min(solved, key=lambda e: e["solver"]["best_returned_V_hat"])
    return {"status": "ok", "group": w["group"],
            "material": w["solver"]["best_returned_material"],
            "V_hat": w["solver"]["best_returned_V_hat"],
            "basis": "solver-returned legal samples"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", choices=["q2", "q3", "all"], default="all")
    ap.add_argument("--pred-q2", default=None)
    ap.add_argument("--pred-q3", default=None)
    ap.add_argument("--data-dir", default=None, help="含 official/ 与 pred/ 的目录，默认包内 data/")
    ap.add_argument("--pool", choices=["full", "blind"], default="full")
    ap.add_argument("--backend", choices=["auto", "sdk", "local"], default="auto")
    ap.add_argument("--scheme", choices=["verified", "shortlist"], default="verified")
    ap.add_argument("--shortlist-k", type=int, default=24)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--samples", type=int, default=10)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--alpha", type=float, default=0.99)
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    backend = args.backend
    if backend in ("auto", "sdk"):
        ok, reason = probe_sdk()
        print(f"[SDK 探针] 可用={ok} 原因={reason}")
        if backend == "sdk" and not ok:
            raise SystemExit(f"--backend sdk 不可用：{reason}")
        if backend == "auto":
            backend = "sdk" if ok else "local"

    base = Path(args.data_dir) if args.data_dir else DATA
    problems = ["q2", "q3"] if args.problem == "all" else [args.problem]
    results = {}
    for prob in problems:
        pred = {"q2": args.pred_q2, "q3": args.pred_q3}[prob]
        pred_path = Path(pred) if pred else base / PRED_FILES[prob]
        rows = C.ranked(C.read_csv(pred_path))
        checks = validate_strict(rows, prob, args.pool, base)
        checks["prediction_sha256"] = C.sha256_file(pred_path)
        print(f"[{prob}] 校验通过 {checks['rows']} 行 版本 {checks['model_version']} "
              f"首位差 {checks['first_gap']:.6f} pool={checks['pool']}")

        if prob == "q2":
            models = [build_q2(rows)]
        elif args.scheme == "verified":
            models = [build_partition(rows, x) for x in ("O3", "NO2", "FO2")]
        else:
            models = [build_partition(rows, x, lam=8.0, k=args.shortlist_k)
                      for x in ("O3", "NO2", "FO2")]
        results[prob] = {"intake": checks, "models": []}
        for m in models:
            M, h, J, K = ising_matrix(m["q"], m["offset"])
            M_adj, adapt_info = adapt_8bit(M)
            audit = post_adapt_audit(M_adj, m)
            if not audit["passed"]:
                raise SystemExit(f"[{prob}/{m['group']}] 适配后自检失败: {audit}")
            t0 = time.perf_counter()
            spins = (solve_sdk if backend == "sdk" else solve_local)(
                M_adj, args.seeds, args.samples, args.iters, args.alpha)
            wall = time.perf_counter() - t0
            rows_raw, stats = evaluate_solvers(m, spins)
            best_V = float(m["raw"].min())
            seed_hits = seed_level_hits(m, spins, args.samples, best_V)
            entry = {"problem": prob, "group": m["group"], "variables": int(len(m["q"])),
                     "backend": backend, "scheme": args.scheme, "lambda": m["lam"],
                     "n_candidates": int(len(m["block"])),
                     "adapt": adapt_info, "audit": audit,
                     "enumeration_optimum": {
                         "material": "|".join(C.key(m["block"][int(np.argmin(m["raw"]))])),
                         "V_hat": best_V},
                     "solver": {"samples": stats["samples"],
                                "legal_samples": stats["legal_samples"],
                                "legal_ratio": stats["legal_ratio"],
                                "seeds_with_legal_hit": seed_hits,
                                "seed_hit_ratio": seed_hits / args.seeds,
                                "best_returned_material": stats["best_returned_material"],
                                "best_returned_V_hat": stats["best_returned_V_hat"]},
                     "wall_s": wall,
                     "matrix_sha256": C.sha256_array(m["q"]),
                     "status": "ok" if stats["legal_samples"] else "solver_failed"}
            np.savez_compressed(PKG / "matrices" / f"entry_{prob}_{m['group']}.npz",
                                qubo=m["q"], offset=m["offset"],
                                ising_adapted=M_adj, var_names=m["names"],
                                raw_scores=m["raw"], left_idx=m["i"], right_idx=m["j"],
                                candidate_id=np.array([int(r["id"]) for r in m["block"]]))
            C.write_csv(C.RESULTS / f"samples_{prob}_{m['group']}.csv",
                        [{"backend": backend, "group": m["group"], **r} for r in rows_raw])
            results[prob]["models"].append(entry)
            print(f"    {m['group']:<4} 变量 {entry['variables']} 适配 {adapt_info['method']} "
                  f"|h|={audit['h_max_abs']:.0f} 见证差={audit['illegal_minus_legal']:.1f} | "
                  f"合法 {stats['legal_samples']}/{stats['samples']} 种子命中 {seed_hits}/{args.seeds} "
                  f"返回最优 {stats['best_returned_material']} "
                  f"V̂={stats['best_returned_V_hat']} ({wall:.1f}s)")

        if prob == "q3":
            results["q3"]["winner"] = choose_winner(results["q3"]["models"])
            print(f"[q3 冠军] {results['q3']['winner']}")

    tag = args.tag or f"{args.problem}_{backend}_{args.scheme}_it{args.iters}"
    out = C.RESULTS / f"entry_{tag}.json"
    C.write_json(out, {"backend": backend, "args": vars(args), "results": results})
    flat = []
    for prob in problems:
        for e in results[prob]["models"]:
            flat.append({"problem": prob, "group": e["group"], "backend": backend,
                         "scheme": args.scheme, "n_candidates": e["n_candidates"],
                         "legal_samples": e["solver"]["legal_samples"],
                         "samples": e["solver"]["samples"],
                         "legal_ratio": e["solver"]["legal_ratio"],
                         "seeds_with_hit": e["solver"]["seeds_with_legal_hit"],
                         "seed_hit_ratio": e["solver"]["seed_hit_ratio"],
                         "best_returned_material": e["solver"]["best_returned_material"],
                         "best_returned_V_hat": e["solver"]["best_returned_V_hat"],
                         "enumeration_V_hat": e["enumeration_optimum"]["V_hat"],
                         "illegal_minus_legal": e["audit"]["illegal_minus_legal"],
                         "status": e["status"]})
    if flat:
        C.write_csv(C.RESULTS / f"entry_{tag}_table.csv", flat)
    print("写出", out)


if __name__ == "__main__":
    main()
