# -*- coding: utf-8 -*-
"""阶段一：用真实 Kaiwu SDK 做矩阵导入与 Ising 转换，修正常数项，产出证据。

可用的 SDK 能力（本轮实测）：
  - kw.core.qubo_matrix_to_qubo_model     矩阵 -> 模型
  - kw.core.qubo_matrix_to_ising_matrix    QUBO -> SDK 的 Ising 矩阵（含参考自旋，宽度 n+1）
不可用：
  - kw.preprocess.*   DLL 被 Windows 应用程序控制策略拦截
  - kw.classical.*    求解需 license（user_id/sdk_code）
"""

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C

import kaiwu as kw


def sdk_model_checks(q, offset):
    """SDK 读入矩阵：模型变量数、偏移、矩阵回读一致性。"""
    model = kw.core.qubo_matrix_to_qubo_model(q.copy())
    positions = {int(k[2:-1]): v for k, v in model.get_variables().items()}
    order = [positions[i] for i in range(len(q))]
    back = model.get_matrix()[np.ix_(order, order)]
    return {
        "n_variables": len(model.get_variables()),
        "model_offset": float(model.get_offset()),
        "matrix_roundtrip_max_abs_diff": float(np.abs(back - q).max()),
        "roundtrip_ok": bool(np.allclose(back, q, atol=1e-12)),
    }


def sdk_ising_checks(q, offset, legal_bits):
    """SDK 的 QUBO->Ising 矩阵与独立公式对比，并核对常数修正。"""
    matrix, bias = kw.core.qubo_matrix_to_ising_matrix(q.copy(), decimal=False)
    matrix = np.asarray(matrix, dtype=float)
    n = len(q)
    h, J, K = C.ising(q, offset)
    expected = np.zeros((n + 1, n + 1))
    expected[:-1, :-1] = -(J + J.T) / 2.0
    expected[:-1, -1] = expected[-1, :-1] = -h / 2.0
    # SDK 能量的独立复算：E = -s^T M s（参考自旋固定为 +1）
    spins = np.column_stack([2.0 * legal_bits - 1.0, np.ones(len(legal_bits))])
    e_sdk = -np.sum((spins @ matrix) * spins, axis=1)
    legal_qubo = np.sum((legal_bits @ q) * legal_bits, axis=1)
    # 能量链：x^T Q x = E_sdk + bias ；Ising 常数 K = offset + tr(Q)/2 + Σ_{i<j}Q_ij
    return {
        "sdk_matrix_shape": list(matrix.shape),
        "sdk_spin_count": int(matrix.shape[0]),
        "sdk_conversion_bias": float(bias),
        "matrix_vs_formula_max_abs_diff": float(np.abs(matrix - expected).max()),
        "matrix_matches_formula": bool(np.allclose(matrix, expected, atol=1e-10)),
        "energy_chain_max_abs_diff": float(np.abs(e_sdk + bias - legal_qubo).max()),
        "energy_chain_ok": bool(np.allclose(e_sdk + bias, legal_qubo, atol=1e-6)),
        "bias_plus_offset_equals_K": bool(abs(bias + offset - K) < 1e-8),
        "K_archived_was_missing_offset": float(K - offset),
        "K_with_offset": float(K),
        "formula_K": float(K),
        "h_max_abs": float(np.max(np.abs(h))),
        "J_max_abs": float(np.max(np.abs(J))),
        "sdk_bias": float(bias),
        "offset": float(offset),
    }


def main():
    report = {"sdk": {}, "problems": {}}
    try:
        from importlib import metadata
        report["sdk"]["kaiwu_version"] = metadata.version("kaiwu")
        report["sdk"]["kaiwu_community"] = metadata.version("kaiwu-community")
    except Exception:
        report["sdk"]["kaiwu_version"] = "unknown"
    report["sdk"]["numpy"] = np.__version__
    report["sdk"]["python"] = sys.version.split()[0]

    cases = [("q2", "q2_pool_predictions.csv", 2704), ("q3", "q3_pool_predictions.csv", 8112)]
    for tag, fname, n_expected in cases:
        rows = C.ranked(C.read_csv(C.DATA / fname))
        left, right = C.layout(rows)
        q, offset, i, j, c = C.encode(rows, left, right)
        bits = C.legal_decisions(len(q), i, j)
        names = ([f"a:{a}" if tag == "q2" else f"u:{a}|{x}" for a, x in left]
                 + [f"b:{b}" for b in right])
        model = sdk_model_checks(q, offset)
        ising_part = sdk_ising_checks(q, offset, bits)
        h, J, K = C.ising(q, offset)
        np.savez_compressed(
            C.MATRICES / f"sdk_ising_{tag}.npz",
            qubo=q, qubo_offset=np.array(offset), var_names=np.array(names),
            h=h, J=J, ising_constant=np.array(K),
            raw_scores=np.array([float(r["V_hat"]) for r in rows]),
            candidate_id=np.array([int(r["id"]) for r in rows]),
            legal_left=i, legal_right=j,
        )
        report["problems"][tag] = {
            "pool_rows": len(rows),
            "expected_rows": n_expected,
            "n_variables": int(len(q)),
            "offset": float(offset),
            "sdk_model": model,
            "sdk_ising": ising_part,
            "matrix_file": f"sdk_ising_{tag}.npz",
            "matrix_sha256": C.sha256_file(C.MATRICES / f"sdk_ising_{tag}.npz"),
            "qubo_sha256": C.sha256_array(q),
            "nnz_including_diagonal": int(np.count_nonzero(q)),
            "nnz_offdiagonal": int(np.count_nonzero(np.triu(q, 1))),
        }
        print(f"[{tag}] SDK 模型 roundtrip={model['roundtrip_ok']} "
              f"Ising 公式一致={ising_part['matrix_matches_formula']} "
              f"能量链={ising_part['energy_chain_ok']} "
              f"bias+offset==K:{ising_part['bias_plus_offset_equals_K']} "
              f"spins={ising_part['sdk_spin_count']} K={K:.4f}")

    C.write_json(C.RESULTS / "stage1_sdk_ising.json", report)
    print("写出 results/stage1_sdk_ising.json")


if __name__ == "__main__":
    main()
