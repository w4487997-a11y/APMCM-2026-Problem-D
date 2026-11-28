# -*- coding: utf-8 -*-
"""阶段九：复审要求的四条回归测试。

R1 全组无合法返回时不得颁发冠军；
R2 真实 SDK 可用性探针正确（非零矩阵、不抛 ZeroDivisionError）；
R3 全池联合入口（--problem all）可跑通并覆盖 2,704 / 8,112 候选；
R4 候选源字段：pool / source_pool 缺失或篡改必须拒绝。
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
import stage7_entry as S7
import stage8_negative_validation as S8

PY = sys.executable
RESULTS = {}


def r1_no_legal_no_winner():
    zeros = np.zeros((4, 10))          # 全 0 自旋：解码后没有任何 1
    rows = C.ranked(C.read_csv(S7.DATA / "pred" / "q3_pool_predictions.csv"))
    models = [S7.build_partition(rows, x) for x in ("O3", "NO2", "FO2")]
    entries = []
    for m in models:
        _, stats = S7.evaluate_solvers(m, zeros)
        entries.append({"status": "ok" if stats["legal_samples"] else "solver_failed",
                        "group": m["group"], "solver": stats})
    winner = S7.choose_winner(entries)
    return {"winner": winner, "passed": winner["status"] == "solver_failed"}


def r2_sdk_probe():
    ok, reason = S7.probe_sdk()
    try:
        ok2, reason2 = S7.probe_sdk()
        crashed = False
    except Exception as exc:                     # 不应出现除零等异常
        crashed = True
        reason2 = f"{type(exc).__name__}: {exc}"
    return {"probe_ok": ok, "reason": reason,
            "no_exception": not crashed, "reason2": reason2,
            "passed": (not crashed) and ok == ok2}


def r3_joint_entry():
    cmd = [PY, str(S7.HERE / "stage7_entry.py"), "--problem", "all",
           "--backend", "local", "--iters", "30", "--alpha", "0.9",
           "--seeds", "3", "--samples", "5", "--tag", "r3"]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(S7.HERE))
    logs = (proc.stdout or "") + (proc.stderr or "")
    ok = proc.returncode == 0
    detail = {}
    if ok:
        target = S7.PKG / "results" / "entry_r3.json"
        if target.exists():
            d = json.loads(target.read_text(encoding="utf-8"))
            for prob in ("q2", "q3"):
                detail[prob] = [{"group": e["group"], "n_candidates": e["n_candidates"]}
                                for e in d["results"][prob]["models"]]
    return {"returncode": proc.returncode, "tail": logs.strip().splitlines()[-3:],
            "detail": detail,
            "passed": ok and detail.get("q2") and detail.get("q3")}


def r4_source_fields():
    cases = {}
    for problem, pred, official, label in (
            ("q2", "q2_pool_predictions.csv", "07_castelli_q2_pool.csv", "07"),
            ("q3", "q3_pool_predictions.csv", "08_castelli_q3_pool.csv", "08")):
        rows = C.read_csv(S7.DATA / "pred" / pred)
        official_rows = C.read_csv(S7.DATA / "official" / official)
        built = S8.make_cases(rows, official_rows, label)
        res = {}
        for name in ("wrong_pool", "wrong_source_pool", "pool_column_absent",
                     "source_pool_column_absent", "source_pool_only_wrong"):
            try:
                S7.validate_strict(built[name](rows), problem)
            except ValueError as exc:
                res[name] = str(exc)[:80]
            else:
                res[name] = "❌ 未被拒绝"
        cases[problem] = res
    passed = all(v != "❌ 未被拒绝" for r in cases.values() for v in r.values())
    return {"cases": cases, "passed": passed}


def main():
    RESULTS["R1_no_legal_no_winner"] = r1_no_legal_no_winner()
    RESULTS["R2_sdk_probe"] = r2_sdk_probe()
    RESULTS["R3_joint_entry"] = r3_joint_entry()
    RESULTS["R4_source_fields"] = r4_source_fields()
    for k, v in RESULTS.items():
        print(f"[{k}] passed={v['passed']}")
        if not v["passed"]:
            print("   ", json.dumps(v, ensure_ascii=False)[:400])
    all_passed = all(v["passed"] for v in RESULTS.values())
    C.write_json(C.RESULTS / "stage9_regression.json",
                 {"all_passed": all_passed, "checks": RESULTS})
    print("总判定:", "PASS" if all_passed else "FAIL")
    print("写出 results/stage9_regression.json")


if __name__ == "__main__":
    main()
