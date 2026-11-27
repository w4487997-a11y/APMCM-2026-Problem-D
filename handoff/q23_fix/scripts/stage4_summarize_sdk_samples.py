# -*- coding: utf-8 -*-
"""阶段四：整理审计环境中真实 SDK 运行样本的原尺度差距，并给出可复跑的 SDK 求解入口。

说明：
  - 这里的 SDK 样本来自审计包 results/sdk_*_raw_samples.csv（审计者本地 1.4.3 授权环境），
    不是本机运行结果；本机缺 license，无法复现同一批样本。
  - 本机已能用真实 SDK 完成矩阵导入与 Ising 转换（stage1），并在 installed 1.4.4 上验证。
  - stage4_sdk_solve.py 提供带 license 后可一键复跑的入口。
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C

REVIEW = C.WORK / "q23_review" / "q23_review" / "results"
CASES = {
    "q3_official_v12": ("sdk_q3_official_v12_raw_samples.csv", 8112),
    "q3_partition_O3": ("sdk_q3_partition_O3_raw_samples.csv", 2704),
    "q3_partition_NO2": ("sdk_q3_partition_NO2_raw_samples.csv", 2704),
    "q3_partition_FO2": ("sdk_q3_partition_FO2_raw_samples.csv", 2704),
    "q3_intising": ("sdk_q3_intising_raw_samples.csv", 144),
    "q2_official_v12": ("sdk_q2_official_v12_raw_samples.csv", 2704),
    "q2_intising": ("sdk_q2_intising_raw_samples.csv", 72),
}


def main():
    out = {"source": "audit package results/ (Kaiwu 1.4.3, local CPU, not this machine)",
           "cases": {}}
    pool_rows = {"q2": C.ranked(C.read_csv(C.DATA / "q2_pool_predictions.csv")),
                 "q3": C.ranked(C.read_csv(C.DATA / "q3_pool_predictions.csv"))}
    minima = {"q2": float(pool_rows["q2"][0]["V_hat"]), "q3": float(pool_rows["q3"][0]["V_hat"])}

    for name, (fname, n_legal) in CASES.items():
        path = REVIEW / fname
        if not path.exists():
            continue
        rows = C.read_csv(path)
        problem = "q2" if name.startswith("q2") else "q3"
        best = minima[problem]
        entry = {"file": fname, "samples": len(rows)}
        for regime in sorted({r["regime"] for r in rows}):
            sub = [r for r in rows if r["regime"] == regime]
            feasible = [r for r in sub if r["feasible"] in ("True", "true", True, "1")]
            scores = []
            for r in feasible:
                if r.get("original_raw_score") not in (None, "", "None"):
                    scores.append(float(r["original_raw_score"]))
            entry[regime] = {
                "samples": len(sub),
                "feasible": len(feasible),
                "feasibility_rate": len(feasible) / len(sub),
                "best_V_hat": min(scores) if scores else None,
                "gap_to_float_optimum": (min(scores) - best) if scores else None,
                "median_gap": (float(np.median(np.array(scores) - best)) if scores else None),
                "min_energy": min(float(r["energy_sdk"]) for r in sub) if sub else None,
            }
        out["cases"][name] = entry
        base = entry.get("unadjusted", {})
        adj = entry.get("sdk_8bit_adjusted", {})
        print(f"[{name}] unadj 可行 {base.get('feasible')}/{base.get('samples')} "
              f"最佳V̂={base.get('best_V_hat')} 差距={base.get('gap_to_float_optimum')} | "
              f"8bit 可行 {adj.get('feasible')}/{adj.get('samples')} "
              f"最佳V̂={adj.get('best_V_hat')} 差距={adj.get('gap_to_float_optimum')}")

    C.write_json(C.RESULTS / "stage4_sdk_samples_summary.json", out)
    print("写出 results/stage4_sdk_samples_summary.json")


if __name__ == "__main__":
    main()
