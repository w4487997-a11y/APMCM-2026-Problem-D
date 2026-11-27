# -*- coding: utf-8 -*-
"""任务 3 + 6：用真实代理预测重建 QUBO 矩阵并交付 NPZ。

流程（V0.4 的 B2 + D1）：
  02+03 重训 -> 预测 07 / 08 -> 保序缩放到 [0,1] -> 建 104 / 208 变量矩阵
  -> 枚举全部合法候选，核对「矩阵能量 == 缩放后代价」 -> 输出最优材料 -> 存 NPZ
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

SEED = 42
LAM = 2.0
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data_real")
RES = os.path.join(HERE, "results")
MAT = os.path.join(HERE, "matrices")
CONVENTION = ("H(x) = x^T Q x + constant；Q 为上三角矩阵（i<j 的耦合放在 Q[i,j]，"
              "对角线为线性项），x 为 0/1 向量")


def load(name):
    return pd.read_csv(os.path.join(DATA, name), encoding="utf-8-sig")


def make_encoder(elems, xs):
    ai = {e: i for i, e in enumerate(elems)}
    xi = {x: i for i, x in enumerate(xs)}
    nA, nB, nX = len(elems), len(elems), len(xs)

    def encode(df):
        m = np.zeros((len(df), nA + nB + nX), dtype=np.float32)
        rows = np.arange(len(df))
        m[rows, df["A"].map(ai).to_numpy()] = 1.0
        m[rows, df["B"].map(ai).to_numpy() + nA] = 1.0
        m[rows, df["X"].map(xi).to_numpy() + nA + nB] = 1.0
        return m

    return encode, ai, xi


def build_q2(costs, ai, bi, nA=52, lam=LAM):
    """costs: dict[(a,b)] -> c，覆盖全部合法对。"""
    n = nA + nA
    Q = np.zeros((n, n), dtype=np.float64)
    for i in range(nA):
        Q[i, i] += -lam
        Q[nA + i, nA + i] += -lam
    for i in range(nA):
        for j in range(i + 1, nA):
            Q[i, j] += 2 * lam
            Q[nA + i, nA + j] += 2 * lam
    const = 2 * lam
    for (a, b), c in costs.items():
        Q[ai[a], nA + bi[b]] += c
    return Q, const


def build_q3(costs, ai, xi, bi, nA=52, nX=3, lam=LAM):
    """costs: dict[(a,b,x)] -> c；变量 u_(i,k) 在前，b_j 在后。"""
    n_u = nA * nX
    n = n_u + nA
    Q = np.zeros((n, n), dtype=np.float64)
    for i in range(n_u):
        Q[i, i] += -lam
    for j in range(nA):
        Q[n_u + j, n_u + j] += -lam
    for i in range(n_u):
        for j in range(i + 1, n_u):
            Q[i, j] += 2 * lam
    for i in range(nA):
        for j in range(i + 1, nA):
            Q[n_u + i, n_u + j] += 2 * lam
    const = 2 * lam
    for (a, b, x), c in costs.items():
        Q[ai[a] * nX + xi[x], n_u + bi[b]] += c
    return Q, const


def energy(Q, const, idx):
    e = const
    for i in idx:
        e += Q[i, i]
    for p in range(len(idx)):
        for q in range(p + 1, len(idx)):
            i, j = sorted((idx[p], idx[q]))
            e += Q[i, j]
    return e


def main():
    os.makedirs(RES, exist_ok=True)
    os.makedirs(MAT, exist_ok=True)

    tr = pd.concat([load("02_castelli_train.csv"), load("03_castelli_val.csv")],
                   ignore_index=True)
    pools = {"q2": load("07_castelli_q2_pool.csv"), "q3": load("08_castelli_q3_pool.csv")}

    elems = sorted(set(tr["A"]) | set(tr["B"]) | set(pools["q2"]["A"]) | set(pools["q3"]["A"]))
    xs_q3 = sorted(pools["q3"]["X"].unique())        # Q3 的 3 个基团，用于矩阵索引
    xs_all = sorted(tr["X"].unique())                # 训练用全部 7 类
    encode_train, ai, _ = make_encoder(elems, xs_all)
    encode_pool, _, _ = make_encoder(elems, xs_all)  # 池子也用同一编码，保证特征维度一致
    xi = {x: i for i, x in enumerate(xs_q3)}         # 仅用于 Q3 的 u_(i,k) 索引
    print(f"elements={len(elems)}, X(train)={len(xs_all)}, X(q3)={xs_q3}")

    Xtr = encode_train(tr)
    ytr = tr["V"].to_numpy(float)
    model = Ridge(alpha=1.0)
    model.fit(Xtr, ytr)
    print(f"ridge fitted on {Xtr.shape}, train MAE={np.abs(model.predict(Xtr)-ytr).mean():.4f}")

    summary = {"seed": SEED, "model": "Ridge(alpha=1.0)", "features": "one-hot(A,B,X)",
               "lambda": LAM, "convention": CONVENTION, "matrices": {}}

    for key, pool in pools.items():
        Xp = encode_pool(pool)
        raw = model.predict(Xp)
        lo, hi = float(raw.min()), float(raw.max())
        if hi - lo < 1e-12:
            scaled = np.zeros_like(raw)
        else:
            scaled = (raw - lo) / (hi - lo)

        if key == "q2":
            costs = {}
            for (a, b), c in zip(pool[["A", "B"]].itertuples(index=False, name=None), scaled):
                costs[(a, b)] = float(c)
            Q, const = build_q2(costs, ai, ai)
            nA, nX = 52, 1
            var_names = ([f"a:{e}" for e in elems] + [f"b:{e}" for e in elems])
        else:
            costs = {}
            for (a, b, x), c in zip(
                    pool[["A", "B", "X"]].itertuples(index=False, name=None), scaled):
                costs[(a, b, x)] = float(c)
            Q, const = build_q3(costs, ai, xi, ai)
            nA, nX = 52, len(xs_q3)
            var_names = ([f"u:{e}|{x}" for e in elems for x in xs_q3]
                         + [f"b:{e}" for e in elems])

        # 逐候选核对
        max_err, best, best_key = 0.0, np.inf, None
        for (k, c) in costs.items():
            if key == "q2":
                idx = [ai[k[0]], 52 + ai[k[1]]]
            else:
                idx = [ai[k[0]] * nX + xi[k[2]], nA * nX + ai[k[1]]]
            e = energy(Q, const, idx)
            max_err = max(max_err, abs(e - c))
            if e < best:
                best, best_key = e, k

        # 理论最优（直接取最小缩放代价）
        k_star = min(costs, key=lambda k: costs[k])
        assert abs(costs[k_star] - costs[best_key]) < 1e-12, "oracle 不一致"

        nnz = int(np.count_nonzero(Q))
        info = {
            "n_vars": int(Q.shape[0]), "candidates": int(len(costs)),
            "constant": float(const), "lambda": LAM,
            "scaling": {"lo": lo, "hi": hi, "method": "min-max -> [0,1]"},
            "raw_range": [float(raw.min()), float(raw.max())],
            "max_energy_vs_cost": float(max_err),
            "nnz": nnz, "coef_abs_min": float(np.abs(Q[Q != 0]).min()),
            "coef_abs_max": float(np.abs(Q).max()),
            "oracle": {"material": list(k_star), "scaled": float(costs[k_star]),
                       "raw": float(raw[list(costs).index(k_star)]),
                       "energy": float(best)},
        }
        summary["matrices"][key] = info

        # 交付
        path = os.path.join(MAT, f"qubo_{key}.npz")
        np.savez_compressed(
            path,
            Q=Q, constant=np.array(const), convention=np.array(CONVENTION),
            var_names=np.array(var_names),
            candidate_A=np.array([k[0] for k in costs]),
            candidate_B=np.array([k[1] for k in costs]),
            candidate_X=np.array([k[2] if len(k) > 2 else "NO2" for k in costs]),
            candidate_id=pool["id"].to_numpy(),
            raw_scores=np.array([float(raw[list(costs).index(k)]) for k in costs]),
            scaled_scores=np.array([costs[k] for k in costs]),
            scaling=np.array([lo, hi]),
            penalty=np.array([LAM, LAM]),
            oracle_material=np.array([json.dumps(list(k_star))]),
            oracle_score=np.array([costs[k_star]]),
            oracle_raw_score=np.array([float(raw[list(costs).index(k_star)])]),
            meta=np.array([json.dumps(info, ensure_ascii=False)]),
        )
        print(f"{key}: vars={Q.shape[0]} cand={len(costs):,} "
              f"max|E-cost|={max_err:.1e} oracle={k_star} raw={info['oracle']['raw']:.4f} "
              f"scaled={costs[k_star]:.4f} nnz={nnz:,}")

        # 预测表（便于复核）
        out = pool.copy()
        out["V_hat"] = raw
        out["scaled_cost"] = scaled
        out.to_csv(os.path.join(RES, f"{key}_pool_predictions.csv"), index=False,
                   encoding="utf-8-sig")

    with open(os.path.join(RES, "matrix_build.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print("saved matrices to", MAT)


if __name__ == "__main__":
    main()
