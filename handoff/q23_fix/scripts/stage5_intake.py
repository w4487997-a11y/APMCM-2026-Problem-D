# -*- coding: utf-8 -*-
"""阶段五：预测入口校验（对应审计 P1-03）。

校验项：
  1. 行数与官方池一致；
  2. 官方候选 id 唯一、无重复、无缺失；
  3. 分数有限、非负；
  4. 模型版本单一且非空；
  5. 同分处理：保存全体最低并列，不做除零；
  6. 常量表（分数全相同）必须被拒绝，而不是静默归一化。

同时注入 6 类缺陷，验证每一项都能被拦下。
"""

import copy
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C

COLUMNS_Q = ["id", "formula", "A", "B", "X", "a_eq_b", "V_hat", "pool", "model_version", "source_pool"]


def validate(rows, problem, pool="full"):
    """严格校验；任何一个环节失败都抛 ValueError。"""
    expected = {"q2": {"full": 2704, "blind": 529}, "q3": {"full": 8112, "blind": 1587}}[problem][pool]
    if not rows:
        raise ValueError("空表")
    cols = list(rows[0])
    if cols != COLUMNS_Q:
        raise ValueError(f"列不合规: {cols}")
    if len(rows) != expected:
        raise ValueError(f"行数不符: {len(rows)} != {expected}")
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("存在重复 id")
    versions = {r["model_version"] for r in rows}
    if len(versions) != 1 or "" in versions:
        raise ValueError(f"版本不唯一或为空: {versions}")
    label = {("q2", "full"): "07", ("q2", "blind"): "11",
             ("q3", "full"): "08", ("q3", "blind"): "12"}[(problem, pool)]
    pools = {r["pool"] for r in rows}
    if pools != {label}:
        raise ValueError(f"pool 字段不符: {pools} != {{{label}}}")
    scores = np.array([float(r["V_hat"]) for r in rows])
    if not np.isfinite(scores).all():
        raise ValueError("存在非有限分数")
    if (scores < 0).any():
        raise ValueError("存在负分数")
    if np.ptp(scores) == 0:
        raise ValueError("常量表：分数全相同，拒绝归一化")
    order = np.argsort(scores, kind="stable")
    return {
        "rows": len(rows),
        "unique_ids": len(set(ids)),
        "scores_finite": True,
        "score_span": float(np.ptp(scores)),
        "first_gap": float(scores[order[1]] - scores[order[0]]),
        "ties_at_minimum": int(np.sum(scores == scores[order[0]])),
        "model_version": versions.pop(),
        "top3": [{"id": rows[i]["id"],
                  "material": "|".join(C.key(rows[i])),
                  "V_hat": float(scores[i])} for i in order[:3]],
    }


def inject_and_check(rows, problem):
    """逐项注入缺陷，确认校验会抛异常。"""
    cases = {
        "duplicate_id": lambda rs: _patch(rs, 1, id=rs[0]["id"]),
        "missing_row": lambda rs: [copy.deepcopy(r) for r in rs[:-1]],
        "nan_score": lambda rs: _patch(rs, 0, V_hat="NaN"),
        "negative_score": lambda rs: _patch(rs, 0, V_hat="-1.0"),
        "mixed_version": lambda rs: _patch(rs, 0, model_version="x2"),
        "constant_table": lambda rs: [dict(copy.deepcopy(r), V_hat="1.0") for r in rs],
        "wrong_pool": lambda rs: _patch(rs, 0, pool="07" if rs[0]["pool"] == "08" else "08"),
    }
    caught = {}
    for name, fn in cases.items():
        try:
            validate(fn(rows), problem)
        except ValueError as exc:
            caught[name] = str(exc)
        else:
            caught[name] = "❌ 未被拦截"
    return caught


def _patch(rows, idx, **kv):
    out = [copy.deepcopy(r) for r in rows]
    out[idx].update(kv)
    return out


def main():
    report = {}
    for problem, fname in (("q2", "q2_pool_predictions.csv"), ("q3", "q3_pool_predictions.csv")):
        rows = C.read_csv(C.DATA / fname)
        ok = validate(rows, problem)
        bad = inject_and_check(rows, problem)
        report[problem] = {"passed": ok, "negative_checks": bad,
                           "all_defects_caught": all(v != "❌ 未被拦截" for v in bad.values()),
                           "file_sha256": C.sha256_file(C.DATA / fname)}
        print(f"[{problem}] 行数 {ok['rows']} 唯一 id {ok['unique_ids']} "
              f"版本 {ok['model_version']} 最低并列 {ok['ties_at_minimum']} "
              f"首位差 {ok['first_gap']:.6f}")
        for k, v in bad.items():
            print(f"   注入 {k:<16} -> {v}")
    C.write_json(C.RESULTS / "stage5_intake.json", report)
    print("写出 results/stage5_intake.json")


if __name__ == "__main__":
    main()
