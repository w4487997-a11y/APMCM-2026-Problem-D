# -*- coding: utf-8 -*-
"""反向自检：向自检样例中植入常见缺陷，确认审计脚本真的会报错。

一个只会全绿的审计脚本等于没有审计。这里对 6 类缺陷各做一次注入，
要求对应的检查项变成 FAIL；任何一项没被抓住，说明该检查形同虚设。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "data_fixture")
AUDIT = os.path.join(HERE, "task_a_audit.py")


def run_audit(data_dir, out):
    cmd = [sys.executable, AUDIT, "--data-dir", data_dir, "--out", out,
           "--mode", "synthetic"]
    subprocess.run(cmd, check=False, capture_output=True)
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)


def status_of(result, cid):
    for c in result["checks"]:
        if c["id"] == cid:
            return c["status"]
    return "MISSING"


def mutate(kind, workdir):
    f = lambda name: os.path.join(workdir, name)  # noqa: E731

    if kind == "dup_row":
        df = pd.read_csv(f("03_castelli_val.csv"))
        pd.concat([df, df.iloc[[0]]], ignore_index=True).to_csv(
            f("03_castelli_val.csv"), index=False)
        return "A2-1"

    if kind == "bad_token":
        df = pd.read_csv(f("06_castelli_no_physics.csv"))
        df.loc[0, "A"] = "Zz"
        df.to_csv(f("06_castelli_no_physics.csv"), index=False)
        return "A2-2"

    if kind == "v_tamper":
        df = pd.read_csv(f("02_castelli_train.csv"))
        df.loc[df.index[:10], "e_form"] = df.loc[df.index[:10], "e_form"] + 0.6
        df.to_csv(f("02_castelli_train.csv"), index=False)
        return "A3-2-02"

    if kind == "leak":
        va = pd.read_csv(f("03_castelli_val.csv"))
        te = pd.read_csv(f("04_castelli_test_holdout.csv"))
        pd.concat([va, te.iloc[:5]], ignore_index=True).to_csv(
            f("03_castelli_val.csv"), index=False)
        return "A2-6"

    if kind == "row_drop":
        df = pd.read_csv(f("07_castelli_q2_pool.csv"))
        df.iloc[2:].to_csv(f("07_castelli_q2_pool.csv"), index=False)
        return "A1-07"

    if kind == "cartesian_break":
        df = pd.read_csv(f("04_castelli_test_holdout.csv"))
        target = df.index[0]
        df.loc[target, "A"] = "Be"  # 不在 23 元素区块内
        df.to_csv(f("04_castelli_test_holdout.csv"), index=False)
        return "A5-04"

    raise ValueError(kind)


CASES = [
    ("dup_row", "03 里插入重复主键"),
    ("bad_token", "06 里出现表外元素 Zz"),
    ("v_tamper", "02 里改动 e_form 但不改 V"),
    ("leak", "把 04 的 5 条复制进 03（盲测泄漏）"),
    ("row_drop", "07 少 2 行"),
    ("cartesian_break", "04 换掉 1 个 A 元素，破坏笛卡尔积"),
]


def main():
    work_root = os.path.join(HERE, "_selftest")
    os.makedirs(work_root, exist_ok=True)
    print("=== 基线（干净样例）===")
    base = run_audit(FIXTURE, os.path.join(work_root, "base.json"))
    print("verdict:", base["summary"]["verdict"], "checks:", base["summary"]["total"])
    ok_all = True if base["summary"]["verdict"] == "PASS" else False
    if not ok_all:
        print("!! 干净样例未通过，先修正审计脚本")

    print("\n=== 缺陷注入 ===")
    results = []
    for kind, desc in CASES:
        tmp = os.path.join(work_root, kind)
        work = os.path.join(tmp, "data")
        if os.path.isdir(tmp):
            shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp, exist_ok=True)
        shutil.copytree(FIXTURE, work)
        cid = mutate(kind, work)
        res = run_audit(work, os.path.join(tmp, "r.json"))
        st = status_of(res, cid)
        caught = st == "FAIL"
        results.append((kind, desc, cid, st, caught))
        print(f"[{'OK ' if caught else 'MISS'}] {desc:<28} → {cid}: {st}")
        shutil.rmtree(tmp, ignore_errors=True)

    missed = [r for r in results if not r[4]]
    print("\n捕获 %d/%d 类缺陷" % (len(results) - len(missed), len(results)))
    return 0 if (not missed and ok_all) else 1


if __name__ == "__main__":
    sys.exit(main())
