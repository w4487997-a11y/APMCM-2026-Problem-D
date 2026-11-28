# -*- coding: utf-8 -*-
"""O-11：把惩罚系数与退火预算扫描全部汇入 mcc_summary.csv。

来源（直接复用已有数据，不重跑）：
  q23_fix/results/stage2_quant_partition.json
    - hitrate        3 组基础配置（本地退火，30 种子×10 样本）
    - hitrate_sweep  6 组退火预算配置
  q23_fix/results/stage3_hitrate_fix.json
    - scan           18 组（K × λ）模型扫描
    - runs           4 组求解配置
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT.parent / "q23_fix" / "results"
OUT = ROOT / "O11" / "mcc_summary.csv"


def main():
    s2 = json.loads((FIX / "stage2_quant_partition.json").read_text(encoding="utf-8"))
    s3 = json.loads((FIX / "stage3_hitrate_fix.json").read_text(encoding="utf-8"))
    rows = []

    for name, v in s2.get("hitrate", {}).items():
        rows.append({
            "source": "stage2/hitrate",
            "kind": "本地退火基线",
            "problem": "q3",
            "config": name,
            "parameters": "seeds=30, samples=10, it=30, alpha=0.9, λ=2 两档分区",
            "samples": v.get("samples"),
            "legal_samples": v.get("feasible"),
            "legal_ratio": round(v.get("feasibility_rate", 0), 4),
            "hits": v.get("raw_opt_hits"),
            "hit_rate": round(v.get("raw_opt_hit_rate", 0), 4),
            "min_tier_ties": "",
            "note": f"wall={v.get('wall_s'):.1f}s" if v.get("wall_s") else "",
        })
    for name, v in s2.get("hitrate_sweep", {}).items():
        if not isinstance(v, dict):
            continue
        rows.append({
            "source": "stage2/hitrate_sweep",
            "kind": "退火预算扫描",
            "problem": "q3",
            "config": name,
            "parameters": "seeds=30, samples=10, λ=2 两档分区",
            "samples": v.get("samples"),
            "legal_samples": v.get("feasible"),
            "legal_ratio": round(v.get("feasibility_rate", 0), 4),
            "hits": v.get("hits", v.get("raw_opt_hits")),
            "hit_rate": round(v.get("hit_rate", v.get("raw_opt_hit_rate", 0)), 4),
            "min_tier_ties": "",
            "note": f"wall={v.get('wall_s'):.1f}s" if v.get("wall_s") else "",
        })
    for entry in s3.get("scan", []):
        rows.append({
            "source": "stage3/scan",
            "kind": "K×λ 模型扫描",
            "problem": "q3",
            "config": f"K={entry.get('K')}, λ={entry.get('lambda')}",
            "parameters": (f"vars={entry.get('n_variables')}, "
                           f"|h|={entry.get('h_max_abs')}, |J|={entry.get('J_max_abs')}, "
                           f"integral={entry.get('integral_ising')}, "
                           f"fits8={entry.get('fits_8bit')}, "
                           f"strict_sep={entry.get('strict_separation')}"),
            "samples": "",
            "legal_samples": "",
            "legal_ratio": "",
            "hits": "",
            "hit_rate": "",
            "min_tier_ties": entry.get("legal_ties"),
            "note": (f"组内最优保留={entry.get('argmin_matches_raw')}；"
                     f"非法间隙={entry.get('separation_gap')}"),
        })
    for name, v in s3.get("runs", {}).items():
        rows.append({
            "source": "stage3/runs",
            "kind": "本地退火（K24/λ8 与基线对比）",
            "problem": "q3",
            "config": name,
            "parameters": "seeds=30, samples=10",
            "samples": v.get("samples"),
            "legal_samples": v.get("feasible"),
            "legal_ratio": round(v.get("feasibility_rate", 0), 4),
            "hits": v.get("hits"),
            "hit_rate": round(v.get("hit_rate", 0), 4),
            "min_tier_ties": "",
            "note": f"wall={v.get('wall_s'):.1f}s" if v.get("wall_s") else "",
        })

    with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"写出 {OUT}：{len(rows)} 条")
    for kind in ("本地退火基线", "退火预算扫描", "K×λ 模型扫描", "本地退火（K24/λ8 与基线对比）"):
        n = sum(1 for r in rows if r["kind"] == kind)
        print(f"  {kind}: {n} 条")


if __name__ == "__main__":
    main()
