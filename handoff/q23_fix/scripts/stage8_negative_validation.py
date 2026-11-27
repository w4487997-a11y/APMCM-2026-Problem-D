# -*- coding: utf-8 -*-
"""阶段八 v2：候选校验负例（覆盖复审点名的 source_pool 三类缺口）。"""

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


def drop_field(rows, field):
    out = []
    for r in rows:
        d = dict(copy.deepcopy(r))
        d.pop(field, None)
        out.append(d)
    return out


def make_cases(rows, official_rows, label):
    other_label = "08" if label == "07" else "07"
    return {
        "pool_external_id": lambda rs: patch(rs, 0, id=str(max(int(r["id"]) for r in official_rows) + 1)),
        "wrong_composition": lambda rs: patch(
            rs, 0,
            A=next(r for r in official_rows if r["id"] != rs[0]["id"])["A"],
            B=next(r for r in official_rows if r["id"] != rs[0]["id"])["B"],
            X=next(r for r in official_rows if r["id"] != rs[0]["id"])["X"]),
        "wrong_pool": lambda rs: patch(rs, 0, pool=other_label),
        "wrong_source_pool": lambda rs: patch(rs, 0, source_pool=other_label),
        "source_pool_only_wrong": lambda rs: patch(rs, 0, source_pool=other_label),
        "pool_column_absent": lambda rs: drop_field(rs, "pool"),
        "source_pool_column_absent": lambda rs: drop_field(rs, "source_pool"),
        "duplicate_id": lambda rs: patch(rs, 1, id=rs[0]["id"]),
        "missing_row": lambda rs: [copy.deepcopy(r) for r in rs[:-1]],
        "nan_score": lambda rs: patch(rs, 0, V_hat="NaN"),
        "negative_score": lambda rs: patch(rs, 0, V_hat="-1.0"),
        "mixed_version": lambda rs: patch(rs, 0, model_version="vX"),
        "constant_table": lambda rs: [dict(copy.deepcopy(r), V_hat="1.0") for r in rs],
    }


def main():
    report = {}
    for problem, pred_name, official_name, label in (
            ("q2", "q2_pool_predictions.csv", "07_castelli_q2_pool.csv", "07"),
            ("q3", "q3_pool_predictions.csv", "08_castelli_q3_pool.csv", "08")):
        rows = C.read_csv(S7.DATA / "pred" / pred_name)
        official = C.read_csv(S7.DATA / "official" / official_name)
        ok = S7.validate_strict(rows, problem)
        checks = {}
        for name, fn in make_cases(rows, official, label).items():
            try:
                S7.validate_strict(fn(rows), problem)
            except ValueError as exc:
                checks[name] = {"rejected": True, "reason": str(exc)[:100]}
            else:
                checks[name] = {"rejected": False, "reason": "❌ 未被拒绝"}
        report[problem] = {"baseline_passed": ok, "checks": checks,
                           "all_rejected": all(v["rejected"] for v in checks.values())}
        print(f"[{problem}] 基线通过；{sum(v['rejected'] for v in checks.values())}/{len(checks)} 负例被拒绝")
        for k, v in checks.items():
            if not v["rejected"]:
                print(f"   ❌ {k}: {v['reason']}")
    C.write_json(C.RESULTS / "stage8_negative_validation.json", report)
    print("写出 results/stage8_negative_validation.json")


if __name__ == "__main__":
    main()
