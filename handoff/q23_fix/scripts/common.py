# -*- coding: utf-8 -*-
"""Q2/Q3 补做工作公共模块。

模型构造与审计脚本 verify.py 的口径保持一致（便于逐条对账）：
  - QUBO：上三角，对角 -λ，块内 2λ，块间缩放代价，常数 2λ；
  - Ising：s=2x-1，J=Q/4，h=Q_ii/2+¼Σ(Q_ij+Q_ji)，K = offset + tr(Q)/2 + Σ_{i<j}Q_ij；
  - 分区模型：按 X 分组，代价按 min+Δ 截断，Δ=0.02，再乘 4 取整 → 代价 ∈ {0,4}。
"""

import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent          # q23_fix/scripts
ROOT = HERE.parent                               # q23_fix
WORK = ROOT.parent                               # workspace
DATA = WORK / "q2_project" / "data_official"
RESULTS = ROOT / "results"
MATRICES = ROOT / "matrices"
LOGS = ROOT / "logs"
for _d in (RESULTS, MATRICES, LOGS):
    _d.mkdir(parents=True, exist_ok=True)

KEYS = ["id", "formula", "A", "B", "X", "a_eq_b"]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_array(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def read_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(p, rows):
    rows = list(rows)
    if not rows:
        raise ValueError("empty rows")
    with open(p, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write_json(p, obj):
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, default=str)


def read_json(p):
    with open(p, encoding="utf-8-sig") as fh:
        return json.load(fh)


def load_predictions(problem, pool="full"):
    """读取 v1 预测表；problem ∈ {q2,q3}。返回按 (V_hat, id) 升序的行。"""
    name = {"q2": "q2_pool_predictions.csv", "q3": "q3_pool_predictions.csv"}[problem]
    rows = read_csv(DATA / name)
    return ranked(rows)


def ranked(rows):
    return sorted(rows, key=lambda r: (float(r["V_hat"]), int(r["id"])))


def key(row):
    return tuple(row[k] for k in ("A", "B", "X"))


def layout(rows):
    """左块 = (A,X)（q3）或 A（q2），右块 = B。"""
    left = sorted({(r["A"], r["X"]) for r in rows})
    right = sorted({r["B"] for r in rows})
    return left, right


def encode(rows, left, right, lam=2.0, cap=None, cost_scale=None):
    """构造上三角 QUBO。

    cap=None 时按整池跨度线性缩放（原全池口径）；
    cap=Δ 时按 min+Δ 截断后缩放（分区口径），再用 cost_scale 取整到格点。
    """
    left_idx = {t: i for i, t in enumerate(left)}
    right_idx = {t: i + len(left) for i, t in enumerate(right)}
    i = np.array([left_idx[(r["A"], r["X"])] for r in rows])
    j = np.array([right_idx[r["B"]] for r in rows])
    raw = np.array([float(r["V_hat"]) for r in rows])
    width = float(np.ptp(raw)) if cap is None else float(cap)
    c = np.minimum(raw - raw.min(), width) / width if width else np.zeros_like(raw)
    q = np.eye(len(left) + len(right)) * -lam
    for start, end in [(0, len(left)), (len(left), len(q))]:
        q[start:end, start:end] += np.triu(np.full((end - start, end - start), 2 * lam), 1)
    q[np.ix_(range(len(left)), range(len(left), len(q)))] = 2 * lam
    if cost_scale is not None:
        c = cost_scale * np.rint(c)
    q[i, j] = c
    return q, 2 * lam, i, j, c


def ising(q, offset):
    """s=2x-1 下的 Ising 系数，K 含 QUBO 常数 offset。"""
    J = np.triu(q, 1) / 4.0
    h = np.diag(q) / 2.0 + (J + J.T).sum(axis=1)
    K = float(offset + np.trace(q) / 2.0 + J.sum())
    return h, J, K


def qubo_energies(q, const, i, j):
    return const + q[i, i] + q[j, j] + q[i, j]


def ising_energy(h, J, K, bits):
    s = 2.0 * np.asarray(bits, dtype=float) - 1.0
    return K + float((J * np.outer(s, s)).sum()) + float(h @ s)


def legal_decisions(n_vars, i, j):
    b = np.zeros((len(i), n_vars))
    b[np.arange(len(i)), i] = 1.0
    b[np.arange(len(i)), j] = 1.0
    return b


def intake_checks(rows, problem, pool="full"):
    """预测入口核对：官方 ID、重复、缺行、非有限分数、版本、同分。"""
    n_expected = {"q2": {"full": 2704, "blind": 529}, "q3": {"full": 8112, "blind": 1587}}[problem][pool]
    out = {"problem": problem, "pool": pool, "rows": len(rows), "expected_rows": n_expected}
    ids = [r["id"] for r in rows]
    out["unique_ids"] = len(set(ids))
    out["duplicate_ids"] = len(ids) - len(set(ids))
    out["rows_ok"] = out["rows"] == n_expected
    scores = np.array([float(r["V_hat"]) for r in rows])
    out["nonfinite_scores"] = int((~np.isfinite(scores)).sum())
    out["negative_scores"] = int((scores < 0).sum())
    versions = {r.get("model_version", "") for r in rows}
    out["model_versions"] = sorted(versions)
    out["single_version"] = len(versions) == 1 and bool(next(iter(versions)))
    keys = [key(r) for r in rows]
    out["unique_compositions"] = len(set(keys))
    out["duplicate_compositions"] = len(keys) - len(set(keys))
    order = np.argsort(scores, kind="stable")
    ordered = scores[order]
    if len(ordered) > 1:
        out["first_gap"] = float(ordered[1] - ordered[0])
        out["ties_at_minimum"] = int(np.sum(ordered == ordered[0]))
        out["second_min_ties"] = int(np.sum(ordered == ordered[1]))
    # 常量表保护：跨度为零时不能做归一等分
    span = float(ordered[-1] - ordered[0]) if len(ordered) else 0.0
    out["score_span"] = span
    out["constant_table"] = span == 0.0
    out["passed"] = bool(out["rows_ok"] and out["duplicate_ids"] == 0
                         and out["nonfinite_scores"] == 0
                         and out["single_version"] and not out["constant_table"])
    return out


def load_matrix(path):
    """兼容多种 npz 字段命名（qubo/Q、offset/qubo_offset/constant、left_idx/legal_left 等）。"""
    z = np.load(path, allow_pickle=True)
    files = set(z.files)

    def pick(*aliases):
        for a in aliases:
            if a in files:
                return z[a]
        raise KeyError(f"缺少字段，候选别名 {aliases}；实际 {sorted(files)}")

    out = {
        "qubo": np.asarray(pick("qubo", "Q"), dtype=float),
        "offset": float(pick("offset", "qubo_offset", "constant")),
        "var_names": [str(x) for x in pick("var_names")],
        "raw_scores": np.asarray(pick("raw_scores", "raw"), dtype=float),
    }
    for key, aliases in {"left_idx": ("left_idx", "legal_left"),
                         "right_idx": ("right_idx", "legal_right"),
                         "candidate_id": ("candidate_id",)}.items():
        try:
            out[key] = np.asarray(pick(*aliases))
        except KeyError:
            out[key] = None
    return out
