# -*- coding: utf-8 -*-
"""O-14 运行登记：把八组结果导出为可追溯的运行表（未舍入耗时）。

输出：O14/results/o14_runs.csv
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = json.loads((ROOT / "O14" / "results" / "o14_results.json").read_text(encoding="utf-8"))
OUT = ROOT / "O14" / "results" / "o14_runs.csv"

rows = []
idx = 0
for prob, pack in RES["problems"].items():
    for e in pack["models"]:
        idx += 1
        wall = float(e["wall_s"])
        rows.append({
            "run_id": f"O14-R{idx:02d}",
            "problem": prob,
            "group": e["group"],
            "encoding": e["encoding"],
            "variables": e["variables"],
            "seeds": 30,
            "samples": 300,
            "config": "it=300, alpha=0.99, 30 种子 x 10 样本",
            "matrix_file": f"{e['problem']}_{e['group']}_{e['encoding']}.npz",
            "matrix_sha256": e["matrix_sha256"],
            "wall_s_unrounded": f"{wall:.6f}",
            "wall_s_2dp": f"{wall:.2f}",
            "solve_s_2dp": e.get("solve_s"),
            "timing_scope": "仅本地退火调用：t0 在 anneal_ising_batch 之前、wall 在其返回之后；"
                            "不含建矩阵/转换/解码/合法性核对",
            "status": "VERIFIED（本包重跑，结果 JSON 为原始记录）",
        })
with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
total = sum(float(r["wall_s_unrounded"]) for r in rows)
rounded = sum(float(r["wall_s_2dp"]) for r in rows)
print(f"写出 {OUT}")
print(f"八组合计（未舍入）: {total:.6f} s；各组先保留两位小数再相加: {rounded:.2f} s")
for r in rows:
    print(f"  {r['run_id']} {r['problem']}/{r['group']}/{r['encoding']}: {r['wall_s_unrounded']} s")
