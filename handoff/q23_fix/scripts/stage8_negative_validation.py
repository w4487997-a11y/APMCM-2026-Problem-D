# -*- coding: utf-8 -*-
"""阶段八：候选校验的负例测试（复审意见第 2 条）。

复审指出旧校验放过了三类问题：池外 ID、错误组成、错误来源池。
这里逐项注入，验证正式入口 stage7.validate_strict 会拒绝，并保存结果。
"""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
import stage7_entry as S7


def patch(rows, idx, **kv):
    out = [copy.deepcopy(r) for r in rows]
    out[idx].update(kv)
    return out


def cases(rows, official_rows):
    other = official_rows[0]
    foreign_id = str(max(int(r["id"]) for r in official_rows) + 1)
    return {
        "pool_external_id": lambda rs: patch(rs, 0, id=foreign_id),
        "wrong_composition": lambda rs: patch(
            rs, 0,
            A=next(r for r in official_rows if r["id"] != rs[0]["id"])["A"],
            B=next(r for r in official_rows if r["id"] != rs[0]["id"])["B"],
            X=next(r for r in official_rows if r["id"] != rs[0]["id"])["X"]),
        "wrong_source_pool": lambda rs: patch(rs, 0, pool="08" if rs[0]["pool"] == "07" else "07"),
        "duplicate_id": lambda rs: patch(rs, 1, id=rs[0]["id"]),
        "missing_row": lambda rs: [copy.deepcopy(r) for r in rs[:-1]],
        "nan_score": lambda rs: patch(rs, 0, V_hat="NaN"),
        "negative_score": lambda rs: patch(rs, 0, V_hat="-1.0"),
        "mixed_version": lambda rs: patch(rs, 0, model_version="vX"),
        "constant_table": lambda rs: [dict(copy.deepcopy(r), V_hat="1.0") for r in rs],
    }


def main():
    report = {}
    for problem, pred_name, official_name in (
            ("q2", "q2_pool_predictions.csv", "07_castelli_q2_pool.csv"),
            ("q3", "q3_pool_predictions.csv", "08_castelli_q3_pool.csv")):
        rows = C.read_csv(C.DATA / pred_name)
        official = C.read_csv(S7.OFFICIAL / official_name)
        ok = S7.validate_strict(rows, problem)
        checks = {}
        for name, fn in cases(rows, official).items():
            try:
                S7.validate_strict(fn(rows), problem)
            except ValueError as exc:
                checks[name] = {"rejected": True, "reason": str(exc)[:120]}
            else:
                checks[name] = {"rejected": False, "reason": "❌ 未被拒绝"}
        all_rejected = all(v["rejected"] for v in checks.values())
        report[problem] = {"baseline_passed": ok, "negative_checks": checks,
                           "all_rejected": all_rejected}
        print(f"[{problem}] 基线 {ok['rows']} 行通过；负例全部拒绝={all_rejected}")
        for k, v in checks.items():
            print(f"   {k:<20} {'拒绝' if v['rejected'] else '放过'}  {v['reason'][:80]}")
    C.write_json(C.RESULTS / "stage8_negative_validation.json", report)
    print("写出 results/stage8_negative_validation.json")


if __name__ == "__main__":
    main()
