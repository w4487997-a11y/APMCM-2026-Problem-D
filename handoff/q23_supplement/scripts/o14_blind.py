# -*- coding: utf-8 -*-
"""O-14：盲池 11/12 独立建模与求解。

oracle-free 原则：代价只由预测分线性缩放得到，不使用枚举最优身份。
  M1 浮点版：cost = (V_hat − min) / (max − min) ∈ [0,1]，精确保持排序；
  M2 8 位版：cost = 4·round(c·4) ∈ {0,4,8,12,16}，整数 Ising，|h|≤127。

产出 q23_supplement/O14/：
  matrices/*.npz / *.csv     矩阵与变量映射
  results/o14_results.json   求解、解码、合法性、命中率、与枚举对照
  results/samples_*.csv       逐样本原始返回
  results/timings.csv         各阶段耗时
  README.md                   说明
"""

import csv
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT.parent / "q23_fix"
sys.path.insert(0, str(FIX / "scripts"))
import common as C

SRC_BLIND = (ROOT.parent / "q23_review" / "q23_review" / "received" /
             "repository" / "handoff" / "v1_2")
OUT = ROOT / "O14"
MAT = OUT / "matrices"
RES = OUT / "results"
for d in (MAT, RES):
    d.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str((ROOT / "scripts")))
from stage2_quant_partition import anneal_ising_batch  # noqa: E402


def write_csv(p, rows):
    with open(p, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def load_blind(problem):
    name = {"q2": "q2_blind_predictions.csv", "q3": "q3_blind_predictions.csv"}[problem]
    src = SRC_BLIND / name
    dst = FIX / "data" / "pred" / name
    if not dst.exists():
        shutil.copy2(src, dst)
    rows = C.read_csv(dst)
    return C.ranked(rows)


def validate(rows, problem):
    pool = {"q2": "11", "q3": "12"}[problem]
    official = C.read_csv(FIX / "data" / "official" /
                          {"q2": "11_castelli_q2_pool_blind.csv",
                           "q3": "12_castelli_q3_pool_blind.csv"}[problem])
    off = {r["id"]: r for r in official}
    assert len(rows) == len(official), (len(rows), len(official))
    ids = [r["id"] for r in rows]
    assert len(set(ids)) == len(ids)
    assert set(ids) == set(off)
    for r in rows:
        assert all(r[k] == off[r["id"]][k] for k in C.KEYS), r["id"]
        assert r["pool"] == pool and r["source_pool"] == pool
    return {"rows": len(rows), "pool": pool,
            "official_sha256": C.sha256_file(FIX / "data" / "official" /
                                             {"q2": "11_castelli_q2_pool_blind.csv",
                                              "q3": "12_castelli_q3_pool_blind.csv"}[problem])}


def build(block, lam=2.0, mode="float", levels=4):
    """left/right 为全 52 元素；block 只给合法配对赋代价，其余保持掩码 M=2λ。"""
    """oracle-free 线性缩放；mode=float 用连续代价，integer 用 4·round(c·levels)。"""
    left = sorted({r["A"] for r in block})
    right = sorted({r["B"] for r in block})
    li = {a: n for n, a in enumerate(left)}
    ri = {b: n + len(left) for n, b in enumerate(right)}
    i = np.array([li[r["A"]] for r in block])
    j = np.array([ri[r["B"]] for r in block])
    raw = np.array([float(r["V_hat"]) for r in block])
    c = (raw - raw.min()) / (raw.max() - raw.min())
    cost = c if mode == "float" else 4.0 * np.rint(c * levels)
    n = len(left) + len(right)
    q = np.eye(n) * -lam
    for s, e in [(0, len(left)), (len(left), n)]:
        q[s:e, s:e] += np.triu(np.full((e - s, e - s), 2 * lam), 1)
    q[np.ix_(range(len(left)), range(len(left), n))] = 2 * lam
    q[i, j] = cost
    return dict(q=q, offset=2 * lam, i=i, j=j, raw=raw, left=left, right=right,
                block=block, n_left=len(left))


def ising_matrix(q, offset):
    h, J, K = C.ising(q, offset)
    n = len(q)
    M = np.zeros((n + 1, n + 1))
    M[:-1, :-1] = -(J + J.T) / 2.0
    M[:-1, -1] = M[-1, :-1] = -h / 2.0
    return M, h, J, K


def verify(model, mode):
    q, off, i, j, raw = model["q"], model["offset"], model["i"], model["j"], model["raw"]
    M, h, J, K = ising_matrix(q, off)
    e = q[i, i] + q[j, j] + q[i, j]
    best_raw = int(np.argmin(raw))
    ties_raw = int(np.sum(raw == raw.min()))
    # 非法态最小能量：单侧只选 1 个
    illegal = [off + q[a, a] for a in range(model["n_left"])]
    integral = bool(np.allclose(h, np.rint(h)) and np.allclose(J, np.rint(J)))
    return {
        "mode": mode,
        "variables": int(len(q)),
        "n_candidates": int(len(raw)),
        "h_max_abs": float(np.abs(h).max()),
        "J_max_abs": float(np.abs(J).max()),
        "integral_ising": integral,
        "fits_8bit": bool(np.abs(h).max() <= 127 and np.abs(J).max() <= 127),
        "raw_best_in_ground": bool(abs(e[best_raw] - e.min()) < 1e-9),
        "argmin_matches_raw": bool(int(np.argmin(e)) == best_raw),
        "ground_ties_energy": int(np.sum(np.abs(e - e.min()) < 1e-9)),
        "raw_min_ties": ties_raw,
        "illegal_min_minus_legal_min": float(min(illegal) - e.min()),
        "best_material": "|".join(C.key(model["block"][best_raw])),
    }


def solve(model, seeds=30, samples=10, iters=300, alpha=0.99):
    M, _, _, _ = ising_matrix(model["q"], model["offset"])
    t0 = time.perf_counter()
    spins = anneal_ising_batch(M, seeds * samples, iterations_per_t=iters, alpha=alpha)
    wall = time.perf_counter() - t0
    bits = ((spins[:, :-1] * spins[:, -1:] + 1) // 2).astype(int)
    n_left = model["n_left"]
    rows, flags = [], []
    for sid, (b, sv) in enumerate(zip(bits, spins)):
        ones = np.flatnonzero(b)
        legal = len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left
        material = score = None
        if legal:
            idx = np.where((model["i"] == ones[0]) & (model["j"] == ones[1]))[0]
            if len(idx):
                material = "|".join(C.key(model["block"][idx[0]]))
                score = float(model["raw"][idx[0]])
            else:
                legal = False
        flags.append(legal and score is not None and abs(score - model["raw"].min()) < 1e-12)
        rows.append({"sample": sid, "legal": legal, "material": material, "V_hat": score})
    legal_rows = [r for r in rows if r["legal"]]
    best = min(legal_rows, key=lambda r: r["V_hat"]) if legal_rows else None
    seed_hits = sum(1 for s in range(seeds) if any(flags[s * samples:(s + 1) * samples]))
    return rows, {
        "samples": len(rows),
        "legal": len(legal_rows),
        "legal_ratio": len(legal_rows) / len(rows),
        "sample_hit_rate": sum(flags) / len(rows),
        "seeds_with_hit": seed_hits,
        "seed_hit_ratio": seed_hits / seeds,
        "best_returned_material": None if best is None else best["material"],
        "best_returned_V_hat": None if best is None else best["V_hat"],
        "wall_s": wall,
    }


def main():
    out = {"oracle_free_statement": (
        "代价仅由预测分线性缩放得到（不使用枚举最优身份），矩阵由盲池 11/12 独立构建。"),
        "problems": {}}
    timings = []
    for problem in ("q2", "q3"):
        rows = load_blind(problem)
        checks = validate(rows, problem)
        groups = ["NO2"] if problem == "q2" else ["O3", "NO2", "FO2"]
        out["problems"][problem] = {"intake": checks, "models": []}
        for g in groups:
            block = sorted([r for r in rows if r["X"] == g],
                           key=lambda r: (float(r["V_hat"]), int(r["id"])))
            for mode in ("float", "integer"):
                if mode == "float":
                    levels = 4
                    t0 = time.perf_counter()
                    model = build(block, mode=mode, levels=levels)
                    build_s = time.perf_counter() - t0
                else:
                    # 自适应档位：保证整数 Ising 的 |h| ≤ 127
                    levels, model, build_s = None, None, 0.0
                    for lv in (4, 3, 2, 1):
                        t0 = time.perf_counter()
                        cand = build(block, mode=mode, levels=lv)
                        build_s = time.perf_counter() - t0
                        a = verify(cand, mode)
                        if a["h_max_abs"] <= 127:
                            levels, model = lv, cand
                            break
                    if model is None:
                        raise SystemExit(f"{problem}/{g} 无可行整数档位")
                audit = verify(model, mode)
                audit["levels"] = levels
                samples, stats = solve(model)
                entry = {"problem": problem, "group": g, "encoding": mode,
                         "build_s": build_s, **audit, **stats,
                         "matrix_sha256": C.sha256_array(model["q"])}
                out["problems"][problem]["models"].append(entry)
                timings.append({"problem": problem, "group": g, "encoding": mode,
                                "build_ms": round(build_s * 1000, 3),
                                "solve_s": round(stats["wall_s"], 3)})
                np.savez_compressed(
                    MAT / f"{problem}_{g}_{mode}.npz",
                    qubo=model["q"], offset=np.array(model["offset"]),
                    var_names=np.array([f"a:{a}" for a in model["left"]]
                                       + [f"b:{b}" for b in model["right"]]),
                    raw_scores=model["raw"], left_idx=model["i"], right_idx=model["j"],
                    candidate_keys=np.array(["|".join(C.key(r)) for r in model["block"]]),
                    candidate_ids=np.array([int(r["id"]) for r in model["block"]]),
                    oracle_free=np.array(True),
                    encoding=np.array(mode),
                )
                if mode == "integer":
                    np.savetxt(MAT / f"{problem}_{g}_{mode}.csv",
                               model["q"].astype(np.int64), delimiter=",", fmt="%d")
                write_csv(RES / f"samples_{problem}_{g}_{mode}.csv", samples)
                print(f"[{problem}/{g}/{mode}] 变量 {audit['variables']} "
                      f"|h|={audit['h_max_abs']:.0f} 整数={audit['integral_ising']} "
                      f"最优在基态={audit['raw_best_in_ground']} 基态并列={audit['ground_ties_energy']} "
                      f"合法 {stats['legal']}/{stats['samples']} "
                      f"种子命中 {stats['seeds_with_hit']}/30 "
                      f"返回最优 {stats['best_returned_material']}")

        if problem == "q3":
            for mode in ("float", "integer"):
                ms = [e for e in out["problems"]["q3"]["models"] if e["encoding"] == mode]
                w = min(ms, key=lambda e: e["best_returned_V_hat"]
                        if e["best_returned_V_hat"] is not None else 1e9)
                out["problems"]["q3"][f"winner_{mode}"] = {
                    "group": w["group"], "material": w["best_returned_material"],
                    "V_hat": w["best_returned_V_hat"],
                    "basis": "solver-returned legal samples"}
                print(f"[q3/{mode} 冠军] {w['group']} {w['best_returned_material']} "
                      f"V_hat={w['best_returned_V_hat']}")

    write_csv(RES / "timings.csv", timings)
    C.write_json(RES / "o14_results.json", out)
    print("写出", OUT)


if __name__ == "__main__":
    main()
