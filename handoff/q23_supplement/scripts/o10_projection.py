# -*- coding: utf-8 -*-
"""O-10：107 变量二阶投影对照（执行书 Q3-03）。

把 08 全池 8,112 个合法候选的代理分，投影到一个 107 变量（A 52 + B 52 + X 3）
的二阶加性模型：
    f = c + Σα_i a_i + Σβ_j b_j + Σγ_k x_k
        + Σδ_ij a_i b_j + Σε_ik a_i x_k + Σζ_jk b_j x_k
拟合用最小二乘（稀疏设计矩阵，每行 7 个非零元）。

对照对象：
  - 208 变量联合编码（q3_official_v12）
  - 104 变量分组编码（O13/q23_fix 已验证的三组分区）

指标：拟合误差、Top-K 重合、最优是否改变、原尺度 V̂ 损失、
变量数/非零耦合/动态范围、8 位可容纳性、量化并列、可行率、命中率、耗时。

运行（需要 scipy）：
    venv-mirna/Scripts/python.exe scripts/o10_projection.py
"""

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT.parent / "q23_fix"
sys.path.insert(0, str(FIX / "scripts"))
import common as C

OUT = ROOT / "O10"
RES = OUT / "results"
MAT = OUT / "matrices"
for d in (RES, MAT):
    d.mkdir(parents=True, exist_ok=True)


def write_csv(p, rows):
    with open(p, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def load_rows():
    return C.ranked(C.read_csv(FIX / "data" / "pred" / "q3_pool_predictions.csv"))


def design(rows, A, B, X):
    """返回 (feats, off, p)：feats 每行 7 个特征下标，纯 numpy 累加正规方程。"""
    nA, nB, nX = len(A), len(B), len(X)
    ia = {a: i for i, a in enumerate(A)}
    ib = {b: i for i, b in enumerate(B)}
    ix = {x: k for k, x in enumerate(X)}
    off = [0,
           1,
           1 + nA,
           1 + nA + nB,
           1 + nA + nB + nX,
           1 + nA + nB + nX + nA * nB,
           1 + nA + nB + nX + nA * nB + nA * nX]
    feats = np.empty((len(rows), 7), dtype=np.int64)
    for r, row in enumerate(rows):
        a, b, x = ia[row["A"]], ib[row["B"]], ix[row["X"]]
        feats[r] = [0,
                    off[1] + a,
                    off[2] + b,
                    off[3] + x,
                    off[4] + a * nB + b,
                    off[5] + a * nX + x,
                    off[5] + nA * nX + b * nX + x]
    p = 1 + nA + nB + nX + nA * nB + nA * nX + nB * nX
    return feats, off, p


def fit_normal_equations(feats, y, p, ridge=1e-8):
    """G = ΦᵀΦ（每行 7 个 1），b = Φᵀy；ridge 稳定后求解。"""
    G = np.zeros((p, p))
    b = np.zeros(p)
    for r in range(len(y)):
        f = feats[r]
        G[np.ix_(f, f)] += 1.0
        b[f] += y[r]
    G[np.diag_indices(p)] += ridge
    return np.linalg.solve(G, b)


def build_qubo(w, A, B, X, off):
    nA, nB, nX = len(A), len(B), len(X)
    n = nA + nB + nX
    q = np.zeros((n, n))
    linA = w[off[1]:off[1] + nA]
    linB = w[off[2]:off[2] + nB]
    linX = w[off[3]:off[3] + nX]
    q[np.arange(nA), np.arange(nA)] = linA
    q[nA + np.arange(nB), nA + np.arange(nB)] = linB
    q[nA + nB + np.arange(nX), nA + nB + np.arange(nX)] = linX
    ab = w[off[4]:off[4] + nA * nB].reshape(nA, nB)
    ax = w[off[5]:off[5] + nA * nX].reshape(nA, nX)
    bx = w[off[6]:off[6] + nB * nX].reshape(nB, nX)
    for a in range(nA):
        q[a, nA:nA + nB] += ab[a]
    for a in range(nA):
        q[a, nA + nB:] += ax[a]
    for b in range(nB):
        q[nA + b, nA + nB:] += bx[b]
    return q, float(w[0])


def legal_energy(q, offset, rows, A, B, X):
    nA = len(A)
    ia = {a: i for i, a in enumerate(A)}
    ib = {b: i for i, b in enumerate(B)}
    ix = {x: k for k, x in enumerate(X)}
    i = np.array([ia[r["A"]] for r in rows])
    j = np.array([nA + ib[r["B"]] for r in rows])
    k = np.array([nA + len(B) + ix[r["X"]] for r in rows])
    e = offset + q[i, i] + q[j, j] + q[k, k] + q[i, j] + q[i, k] + q[j, k]
    return e, i, j, k


def ranks(x):
    order = np.argsort(x, kind="stable")
    r = np.empty(len(x))
    r[order] = np.arange(len(x))
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    return float(ra @ rb / np.sqrt((ra @ ra) * (rb @ rb)))


def topk_overlap(score_a, score_b, ids, ks=(1, 5, 10, 25, 50)):
    out = []
    for k in ks:
        a = set(np.lexsort((ids, score_a))[:k].tolist())
        b = set(np.lexsort((ids, score_b))[:k].tolist())
        out.append({"K": k, "overlap": len(a & b), "ratio": len(a & b) / k})
    return out


def main():
    rows = load_rows()
    A = sorted({r["A"] for r in rows})
    B = sorted({r["B"] for r in rows})
    X = sorted({r["X"] for r in rows})
    raw = np.array([float(r["V_hat"]) for r in rows])
    ids = np.array([int(r["id"]) for r in rows])
    feats, off, p = design(rows, A, B, X)
    print(f"[拟合] 合法行 {feats.shape[0]}，每行 7 特征，参数 {p}")

    t0 = time.perf_counter()
    w = fit_normal_equations(feats, raw, p)
    fit_s = time.perf_counter() - t0
    q, offset = build_qubo(w, A, B, X, off)
    e, i, j, k = legal_energy(q, offset, rows, A, B, X)

    # 拟合误差（合法候选上）
    mae = float(np.mean(np.abs(e - raw)))
    rmse = float(np.sqrt(np.mean((e - raw) ** 2)))
    rho = spearman(raw, e)
    best_raw = int(np.argmin(raw))
    best_fit = int(np.argmin(e))
    topk = topk_overlap(raw, e, ids)
    print(f"[拟合] MAE={mae:.4f} RMSE={rmse:.4f} Spearman={rho:.4f} 用时 {fit_s*1000:.1f}ms")
    print(f"[最优] 原分最优 {C.key(rows[best_raw])}；拟合最优 {C.key(rows[best_fit])} "
          f"原尺度差 {raw[best_fit]-raw[best_raw]:+.6f}")

    # 惩罚：合法态观测范围 + 保守界
    L, U = float(e.min()), float(e.max())
    S = float(abs(offset) + np.abs(q).sum())
    lam_emp = (U - L) * 1.05
    lam_bound = 2 * S * 1.05
    nA, nB, nX = len(A), len(B), len(X)
    n = nA + nB + nX
    Q = q.copy()
    Q[:nA, :nA][np.triu_indices(nA, 1)] += 2 * lam_emp
    Q[nA:nA + nB, nA:nA + nB][np.triu_indices(nB, 1)] += 2 * lam_emp
    Q[nA + nB:, nA + nB:][np.triu_indices(nX, 1)] += 2 * lam_emp
    Q[np.arange(nA), np.arange(nA)] -= lam_emp
    Q[nA + np.arange(nB), nA + np.arange(nB)] -= lam_emp
    Q[nA + nB + np.arange(nX), nA + nB + np.arange(nX)] -= lam_emp
    Qoff = offset + 3 * lam_emp
    h, J, K = C.ising(Q, Qoff)
    M = np.zeros((n + 1, n + 1))
    M[:-1, :-1] = -(J + J.T) / 2
    M[:-1, -1] = M[-1, :-1] = -h / 2

    # 8 位适配检查
    mx = float(np.abs(M).max())
    scale = 127.0 / mx if mx else 1.0
    Mq = np.rint(M * scale)
    hq = -2 * Mq[:-1, -1]
    Jq = np.triu(-2 * Mq[:-1, :-1], 1)
    integral = bool(np.allclose(hq, np.rint(hq)) and np.allclose(Jq, np.rint(Jq)))
    fits8 = bool(np.abs(hq).max() <= 127 and np.abs(Jq).max() <= 127)

    # 量化后合法态并列
    qs = np.rint(Q * scale)
    eq = (Qoff * scale) + qs[i, i] + qs[j, j] + qs[k, k] + qs[i, j] + qs[i, k] + qs[j, k]
    ties = int(np.sum(np.abs(eq - eq.min()) < 1e-9))

    # 求解（本地退火，float 矩阵）
    sys.path.insert(0, str(FIX / "scripts"))
    from stage2_quant_partition import anneal_ising_batch
    t0 = time.perf_counter()
    spins = anneal_ising_batch(M, 300, iterations_per_t=300, alpha=0.99)
    solve_s = time.perf_counter() - t0
    bits = ((spins[:, :-1] * spins[:, -1:] + 1) // 2).astype(int)
    key_index = {C.key(r): t for t, r in enumerate(rows)}
    keyset = {f"{r['A']}|{r['B']}|{r['X']}" for r in rows}
    samples = []
    legal = hits = 0
    best_ret = None
    for sid, (b, sv) in enumerate(zip(bits, spins)):
        ones = np.flatnonzero(b)
        ok = (ones < nA).sum() == 1 and ((ones >= nA) & (ones < nA + nB)).sum() == 1 \
            and (ones >= nA + nB).sum() == 1
        material = score = energy = None
        if ok:
            a = int(ones[ones < nA][0])
            bb = int(ones[(ones >= nA) & (ones < nA + nB)][0] - nA)
            xx = int(ones[ones >= nA + nB][0] - nA - nB)
            material = f"{A[a]}|{B[bb]}|{X[xx]}"
            idx = key_index.get((A[a], B[bb], X[xx]))
            if idx is not None:
                score = float(raw[idx])
                energy = float(e[idx])
                legal += 1
                best_ret = score if best_ret is None else min(best_ret, score)
                if abs(score - raw.min()) < 1e-12:
                    hits += 1
        samples.append({"sample": sid, "legal": bool(ok and material in keyset),
                        "material": material, "V_hat": score,
                        "energy_projection": energy,
                        "spin": "".join(str(int(v)) for v in sv),
                        "bits": "".join(str(int(v)) for v in b)})
    hit_rate = hits / len(bits)
    feasible = legal / len(bits)

    summary = {
        "projection": {
            "variables": int(n), "n_candidates": int(len(rows)),
            "n_parameters": int(p),
            "fit_mae": mae, "fit_rmse": rmse, "spearman": rho,
            "fit_time_s": fit_s,
            "best_raw_material": "|".join(C.key(rows[best_raw])),
            "best_raw_V": float(raw[best_raw]),
            "best_fit_material": "|".join(C.key(rows[best_fit])),
            "best_fit_V_at_raw_scale": float(raw[best_fit]),
            "best_V_gap": float(raw[best_fit] - raw[best_raw]),
            "topk": topk,
            "legal_energy_range": [L, U],
            "negative_coefficients": int(np.sum(w < 0)),
            "lambda_empirical": lam_emp, "lambda_bound": lam_bound,
            "ising_h_max_abs": float(np.abs(h).max()),
            "ising_J_max_abs": float(np.abs(J).max()),
            "ising_spins": int(n + 1),
            "quant_scale": float(scale),
            "quant_h_max_abs": float(np.abs(hq).max()),
            "quant_J_max_abs": float(np.abs(Jq).max()),
            "quant_integral": integral, "fits_8bit": fits8,
            "quant_ties_at_min": ties,
            "solver": {"backend": "local SA (非 SDK)", "seeds": 30, "samples": 300,
                       "legal_ratio": feasible, "sample_hit_rate": hit_rate,
                       "best_returned_V": best_ret, "wall_s": solve_s},
        }
    }

    # 对照：208 联合编码
    Q2P = ROOT.parent / "q2_project"
    z = np.load(Q2P / "matrices" / "qubo_q3_official_v12.npz", allow_pickle=True)
    q20 = z["Q"]
    summary["joint_208"] = {
        "variables": int(q20.shape[0]),
        "nnz_including_diag": int(np.count_nonzero(q20)),
        "nnz_offdiag": int(np.count_nonzero(np.triu(q20, 1))),
        "max_abs_q": float(np.abs(q20).max()),
        "h_max_abs": float(np.abs(C.ising(q20, float(z["constant"]))[0]).max()),
        "J_max_abs": float(np.abs(C.ising(q20, float(z["constant"]))[1]).max()),
    }
    # 对照：104 分组（取 O3 组）
    meta = json.loads((ROOT / "O13" / "matrices" / "q3_O3_meta.json").read_text(encoding="utf-8"))
    summary["partition_104"] = {
        "variables": meta["variables"], "n_candidates": meta["n_candidates"],
        "max_abs_q": meta["q_abs_max"],
        "h_max_abs": meta["ising"]["h_max_abs"],
        "J_max_abs": meta["ising"]["J_max_abs"],
        "integral": meta["ising"]["integral"], "fits_8bit": meta["ising"]["fits_8bit"],
        "illegal_minus_legal": meta["ising"]["illegal_witness_minus_legal"],
        "ties_at_minimum": meta["enumeration"]["ties_at_minimum_integer"],
    }
    summary["projection"]["nnz_including_diag"] = int(np.count_nonzero(Q))
    summary["projection"]["nnz_offdiag"] = int(np.count_nonzero(np.triu(Q, 1)))
    C.write_json(RES / "o10_projection.json", summary)
    np.savez_compressed(MAT / "q3_projection_107.npz",
                        qubo=q, offset=np.array(offset),
                        penalized_qubo=Q, penalized_offset=np.array(Qoff),
                        ising_matrix=M, ising_constant=np.array(K),
                        lambda_empirical=np.array(lam_emp),
                        var_names=np.array([f"a:{a}" for a in A] + [f"b:{b}" for b in B]
                                           + [f"x:{x}" for x in X]),
                        weights=w, feature_offset=np.array(off))
    with open(RES / "o10_samples.csv", "w", encoding="utf-8-sig", newline="") as fh:
        wcsv = csv.DictWriter(fh, list(samples[0]))
        wcsv.writeheader()
        wcsv.writerows(samples)
    rows_csv = []
    for name, pack in (("107 投影", summary["projection"]), ("104 分组", summary["partition_104"]),
                       ("208 联合", summary["joint_208"])):
        rows_csv.append({"encoding": name, "variables": pack["variables"],
                         "ncand": pack.get("n_candidates", 8112),
                         "nnz_diag": pack.get("nnz_including_diag", ""),
                         "max_abs_q": pack.get("max_abs_q", ""),
                         "h_max_abs": round(float(pack.get("h_max_abs",
                                                          pack.get("ising_h_max_abs", 0))), 2),
                         "J_max_abs": round(float(pack.get("J_max_abs",
                                                          pack.get("ising_J_max_abs", 0))), 2),
                         "integral": pack.get("integral", ""),
                         "fits_8bit": pack.get("fits_8bit", ""),
                         "ties_at_min": pack.get("quant_ties_at_min",
                                                 pack.get("ties_at_minimum", ""))})
    write_csv(RES / "o10_comparison.csv", rows_csv)
    print("[对照]", json.dumps(rows_csv, ensure_ascii=False, indent=None))
    print("写出", OUT)


if __name__ == "__main__":
    main()
