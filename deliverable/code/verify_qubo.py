# -*- coding: utf-8 -*-
"""任务 C：QUBO 数学路径验证（对应 V0.4 的 C2/C3/C4）。

三件事：
  1. 问题二 2×2 人工代价表，4 变量枚举 16 状态；
  2. 问题三 3 个 2×2 矩阵，8 变量枚举 256 状态；
  3. 真实候选池规模下，逐条核对矩阵能量与公式能量是否一致（代价用占位向量，
     只验证编码，不验证预测精度）。
"""

import itertools
import json

import numpy as np
import pandas as pd

LAM = 2.0
LAM_L = 2.0
EPS_TOL = 1e-9


def qubo_from_terms(n, const, diag, quad):
    """把 diag/quad 写进上三角矩阵 Q，使 H(x) = xᵀQx + const。"""
    Q = np.zeros((n, n))
    for i, v in diag.items():
        Q[i, i] += v
    for (i, j), v in quad.items():
        if i == j:
            Q[i, i] += v
        else:
            a, b = min(i, j), max(i, j)
            Q[a, b] += v
    return Q, const


def energy(Q, const, bits):
    idx = [i for i, b in enumerate(bits) if b]
    e = const
    for i in idx:
        e += Q[i, i]
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            e += Q[idx[a], idx[b]]
    return e


def brute(Q, const, n):
    best, arg, feas = np.inf, None, 0
    rows = []
    for bits in itertools.product([0, 1], repeat=n):
        e = energy(Q, const, bits)
        rows.append((bits, e))
        if e < best - 1e-12:
            best, arg = e, bits
    return best, arg, rows


# ---------------------------------------------------------------- Q2
def build_q2(C, n=2, lam=LAM, illegal=()):
    """C: n×n 代价；illegal: 需要禁止的 (i,j)。"""
    idx_a = list(range(n))
    idx_b = list(range(n, 2 * n))
    diag, quad = {}, {}
    const = 0.0
    for i in idx_a:
        diag[i] = diag.get(i, 0.0) - lam
    for j in idx_b:
        diag[j] = diag.get(j, 0.0) - lam
    for i in range(n):
        for j in range(i + 1, n):
            quad[(idx_a[i], idx_a[j])] = quad.get((idx_a[i], idx_a[j]), 0.0) + 2 * lam
            quad[(idx_b[i], idx_b[j])] = quad.get((idx_b[i], idx_b[j]), 0.0) + 2 * lam
    const += 2 * lam
    for i in range(n):
        for j in range(n):
            quad[(idx_a[i], idx_b[j])] = quad.get((idx_a[i], idx_b[j]), 0.0) + C[i, j]
            if (i, j) in illegal:
                quad[(idx_a[i], idx_b[j])] += LAM_L
    Q, c = qubo_from_terms(2 * n, const, diag, quad)
    return Q, c


def analyse_q2(C, illegal=(), tag=""):
    n = C.shape[0]
    Q, const = build_q2(C, n, illegal=illegal)
    best, arg, rows = brute(Q, const, 2 * n)
    ok_onehot = True
    for bits, e in rows:
        if abs(e - best) < 1e-9:
            a_ok = sum(bits[:n]) == 1
            b_ok = sum(bits[n:]) == 1
            ok_onehot &= bool(a_ok and b_ok)
    # 公式能量 vs 矩阵能量
    max_dev = 0.0
    for bits, e in rows:
        a = bits[:n]
        b = bits[n:]
        f = 0.0
        for i in range(n):
            for j in range(n):
                f += C[i, j] * a[i] * b[j]
                if (i, j) in illegal:
                    f += LAM_L * a[i] * b[j]
        f += LAM * (sum(a) - 1) ** 2 + LAM * (sum(b) - 1) ** 2
        max_dev = max(max_dev, abs(f - e))
    # 解码
    chosen = None
    for bits, e in rows:
        if abs(e - best) < 1e-9 and sum(bits[:n]) == 1 and sum(bits[n:]) == 1:
            chosen = (int(np.argmax(bits[:n])), int(np.argmax(bits[n:])))
            break
    res = {"tag": tag, "vars": 2 * n, "states": 2 ** (2 * n),
           "best_energy": round(float(best), 10), "argmin": chosen,
           "argmin_cost": None if chosen is None else float(C[chosen]),
           "all_optima_legal": bool(ok_onehot),
           "max_formula_vs_matrix": float(max_dev)}
    return res


# ---------------------------------------------------------------- Q3
def build_q3(mats, n_a=2, n_x=3, n_b=2, lam=LAM, illegal=()):
    """mats[k][i,j] = C(A_i, B_j, X_k)。变量：u_(i,k) 共 n_a*n_x 个，b_j 共 n_b 个。"""
    n_u = n_a * n_x
    n = n_u + n_b
    diag, quad = {}, {}
    const = 0.0
    for t in range(n_u):
        diag[t] = diag.get(t, 0.0) - lam
    for j in range(n_b):
        diag[n_u + j] = diag.get(n_u + j, 0.0) - lam
    for i in range(n_u):
        for j in range(i + 1, n_u):
            quad[(i, j)] = quad.get((i, j), 0.0) + 2 * lam
    for i in range(n_b):
        for j in range(i + 1, n_b):
            quad[(n_u + i, n_u + j)] = quad.get((n_u + i, n_u + j), 0.0) + 2 * lam
    const += 2 * lam
    for k in range(n_x):
        for i in range(n_a):
            u = i * n_x + k
            for j in range(n_b):
                quad[(u, n_u + j)] = quad.get((u, n_u + j), 0.0) + mats[k][i, j]
                if (i, j, k) in illegal:
                    quad[(u, n_u + j)] += LAM_L
    Q, c = qubo_from_terms(n, const, diag, quad)
    return Q, c


def analyse_q3(mats, tag="", illegal=()):
    Q, const = build_q3(mats, illegal=illegal)
    n = Q.shape[0]
    best, arg, rows = brute(Q, const, n)
    n_u = 6
    legal = True
    for bits, e in rows:
        if abs(e - best) < 1e-9:
            legal &= (sum(bits[:n_u]) == 1 and sum(bits[n_u:]) == 1)
    max_dev = 0.0
    for bits, e in rows:
        u, b = bits[:n_u], bits[n_u:]
        f = 0.0
        for k in range(3):
            for i in range(2):
                for j in range(2):
                    f += mats[k][i, j] * u[i * 3 + k] * b[j]
                    if (i, j, k) in illegal:
                        f += LAM_L * u[i * 3 + k] * b[j]
        f += LAM * (sum(u) - 1) ** 2 + LAM * (sum(b) - 1) ** 2
        max_dev = max(max_dev, abs(f - e))
    # 解码
    chosen = None
    for bits, e in rows:
        if abs(e - best) < 1e-9 and sum(bits[:n_u]) == 1 and sum(bits[n_u:]) == 1:
            t = int(np.argmax(bits[:n_u]))
            chosen = (t // 3, int(np.argmax(bits[n_u:])), t % 3)  # (A, B, X) 0-based
            break
    return {"tag": tag, "vars": n, "states": 2 ** n,
            "best_energy": round(float(best), 10), "argmin": chosen,
            "argmin_cost": None if chosen is None else float(mats[chosen[2]][chosen[0], chosen[1]]),
            "all_optima_legal": bool(legal),
            "max_formula_vs_matrix": float(max_dev)}


# ---------------------------------------------------------------- 真实池
def real_pool_check(pool_csv, mode="q2", seed=7):
    df = pd.read_csv(pool_csv, encoding="utf-8-sig")
    rng = np.random.default_rng(seed)
    elem_a = sorted(df["A"].unique())
    elem_b = sorted(df["B"].unique())
    ia = {e: i for i, e in enumerate(elem_a)}
    ib = {e: i for i, e in enumerate(elem_b)}
    if mode == "q2":
        xs = ["NO2"]
    else:
        xs = sorted(df["X"].unique())
    ix = {x: i for i, x in enumerate(xs)}

    cost = {}
    for a, b, x in df[["A", "B", "X"]].itertuples(index=False, name=None):
        cost[(a, b, x)] = float(rng.random())

    n_a, n_b, n_x = len(elem_a), len(elem_b), len(xs)
    if mode == "q2":
        n = n_a + n_b
        diag = {i: -LAM for i in range(n)}
        quad = {}
        for i in range(n_a):
            for j in range(i + 1, n_a):
                quad[(i, j)] = 2 * LAM
        for i in range(n_b):
            for j in range(i + 1, n_b):
                quad[(n_a + i, n_a + j)] = 2 * LAM
        const = 2 * LAM
        for (a, b, x), c in cost.items():
            quad[(ia[a], n_a + ib[b])] = c
    else:
        n_u = n_a * n_x
        n = n_u + n_b
        diag = {i: -LAM for i in range(n)}
        quad = {}
        for i in range(n_u):
            for j in range(i + 1, n_u):
                quad[(i, j)] = 2 * LAM
        for i in range(n_b):
            for j in range(i + 1, n_b):
                quad[(n_u + i, n_u + j)] = 2 * LAM
        const = 2 * LAM
        for (a, b, x), c in cost.items():
            quad[(ia[a] * n_x + ix[x], n_u + ib[b])] = c
    Q, c0 = qubo_from_terms(n, const, diag, quad)

    max_dev, worst = 0.0, None
    best, arg = np.inf, None
    for (a, b, x), cv in cost.items():
        bits = [0] * n
        bits[ia[a] * n_x + ix[x]] = 1 if mode != "q2" else 1
        if mode == "q2":
            bits = [0] * n
            bits[ia[a]] = 1
            bits[n_a + ib[b]] = 1
        else:
            bits[ia[a] * n_x + ix[x]] = 1
            bits[n_u + ib[b]] = 1
        e = energy(Q, c0, bits)
        d = abs(e - cv)
        if d > max_dev:
            max_dev, worst = d, (a, b, x)
        if e < best:
            best, arg = e, ((a, b, x), cv)
    return {"mode": mode, "pairs": len(cost), "vars": int(n),
            "max_energy_error": float(max_dev), "worst": worst,
            "argmin_matches": bool(abs(best - arg[1]) < 1e-9),
            "best_cost": float(arg[1])}


def main():
    out = {"q2": [], "q3": [], "pool": []}

    C = np.array([[0.30, 0.10], [0.50, 0.20]])
    out["q2"].append(analyse_q2(C, tag="Q2 基准"))
    out["q2"].append(analyse_q2(C, illegal={(0, 1)}, tag="Q2 禁用最优对 (A1,B2)"))

    mats = [np.array([[0.30, 0.20], [0.45, 0.50]]),
            np.array([[0.10, 0.35], [0.40, 0.60]]),
            np.array([[0.25, 0.55], [0.05, 0.70]])]
    out["q3"].append(analyse_q3(mats, tag="Q3 基准"))
    out["q3"].append(analyse_q3(mats, tag="Q3 禁用最优 (A2,B1,X3)", illegal={(1, 0, 2)}))

    import os
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_real")
    out["pool"].append(real_pool_check(os.path.join(base, "07_castelli_q2_pool.csv"), "q2"))
    out["pool"].append(real_pool_check(os.path.join(base, "08_castelli_q3_pool.csv"), "q3"))

    print("== Q2 ==")
    for r in out["q2"]:
        print(f"  {r['tag']}: vars={r['vars']} states={r['states']} "
              f"min_energy={r['best_energy']} argmin={r['argmin']} cost={r['argmin_cost']} "
              f"legal={r['all_optima_legal']} |Eform-Emtx|max={r['max_formula_vs_matrix']:.1e}")
    print("== Q3 ==")
    for r in out["q3"]:
        print(f"  {r['tag']}: vars={r['vars']} states={r['states']} "
              f"min_energy={r['best_energy']} argmin(A,B,X)={r['argmin']} cost={r['argmin_cost']} "
              f"legal={r['all_optima_legal']} |Eform-Emtx|max={r['max_formula_vs_matrix']:.1e}")
    print("== 真实池 ==")
    for r in out["pool"]:
        print(f"  {r['mode']}: vars={r['vars']} candidates={r['pairs']:,} "
              f"max|E-cost-const|={r['max_energy_error']:.1e} argmin_ok={r['argmin_matches']}")

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "qubo_verify.json"),
              "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    main()
