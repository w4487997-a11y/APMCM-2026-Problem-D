# -*- coding: utf-8 -*-
"""把 P0-05/P0-06 补证内容合入 f274362 基线（可重复执行）。

作用：
  1. O-14 README：撤回“45–786 s”，改用八组原始 38.533–48.536 s；
  2. O-15 local_sa_timing.csv：补 run_id / 未舍入值 / 计时范围（保留 wall_s 2 位小数列）；
  3. O-15 resource_cost.csv：补 SDK 两种计时口径与 162.556 s UNVERIFIED 行；
  4. O-15 README：补对账说明；
  5. consistency_test.py：新增 3 项（运行 ID、O-11 对账、对账表）。
"""

import csv
import json
from pathlib import Path

S = Path(__file__).resolve().parents[1]

RUN_IDS = {("q2", "NO2"): "O15-R01", ("q3", "O3"): "O15-R02",
           ("q3", "NO2"): "O15-R03", ("q3", "FO2"): "O15-R04"}
SCOPE = "本地退火调用墙钟（t0 在调用前，结束在返回后）"
SRC = "q23_fix/results/entry_all_local_verified_it300.json"


def load_entry():
    return json.loads((S.parent / "q23_fix" / "results" /
                       "entry_all_local_verified_it300.json").read_text(encoding="utf-8"))


def write_local_sa():
    entry = load_entry()
    rows = []
    for prob, pack in entry["results"].items():
        for m in pack["models"]:
            ws = float(m["wall_s"])
            rows.append({
                "problem": prob, "model": m["group"], "variables": m["variables"],
                "seeds": 30, "samples": 300,
                "config": "it=300, alpha=0.99, 30 种子 x 10 样本",
                "wall_s": f"{ws:.2f}",
                "wall_s_unrounded": f"{ws:.6f}",
                "run_id": RUN_IDS[(prob, m["group"])],
                "per_sample_ms": f"{ws*1000/300:.3f}",
                "timing_scope": SCOPE,
                "source": SRC,
                "status": "VERIFIED（本包运行，原始 JSON 为记录）",
            })
    with open(S / "O15" / "local_sa_timing.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return sum(float(r["wall_s_unrounded"]) for r in rows)


def patch_resource_cost():
    path = S / "O15" / "resource_cost.csv"
    if "local_v1_frozen_30x10" in path.read_text(encoding="utf-8-sig"):
        return
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    fields = list(rows[0].keys()) + ["run_id"]
    entry = load_entry()
    sa = {}
    for prob, pack in entry["results"].items():
        for m in pack["models"]:
            sa[(prob, m["group"])] = float(m["wall_s"])
    out, inserted = [], False
    for r in rows:
        r.setdefault("run_id", "")
        if r["item"].startswith("本地退火 "):
            key_part = r["item"].replace("本地退火 ", "").split("(")[0].strip()
            prob, model = key_part.split("/")
            ws = sa[(prob, model)]
            r["item"] = f"本地退火 {prob}/{model}（{RUN_IDS[(prob, model)]}）"
            r["value"] = f"{ws:.6f}"
            r["config"] = "it=300, α=0.99, 30 种子×10 样本"
            r["status"] = "实测（本地 CPU，未舍入）"
            r["run_id"] = RUN_IDS[(prob, model)]
        if r["item"].startswith("SDK CPU 求解（正式 104 变量模型，每组）") and not inserted:
            r["item"] = "SDK CPU 求解（正式 104 变量模型，每组，完整流程）"
            r["source"] = "复审环境 Kaiwu 记录（非本机，起止未在本包归档）"
            r["status"] = "外部实测（复审环境）"
            out.append(r)
            out.append({"item": "SDK 求解调用（仅 opt.solve()，30 次）", "value": "0.48–0.69",
                        "unit": "s", "config": "30 runs；计时代码 q23_review/.../scripts/kaiwu_local.py L65-67",
                        "source": "审计包 sdk_*_runs.csv 的 wall_ms 之和；不含初始化/转换/适配/解码/合法性核对",
                        "status": "可复核（solve 调用级计时）", "run_id": ""})
            out.append({"item": "整合包 local_v1_frozen_30x10 四组合计", "value": "162.556",
                        "unit": "s", "config": "来源包不在当前仓库，待提供",
                        "source": "复审通知引用（本包无法复核）",
                        "status": "UNVERIFIED（不用于论文）", "run_id": ""})
            inserted = True
            continue
        out.append(r)
    assert inserted, "未找到正式 SDK 行"
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fields)
        w.writeheader()
        w.writerows(out)


def patch_o14_readme():
    p = S / "O14" / "README.md"
    t = p.read_text(encoding="utf-8")
    old = ("**耗时说明**：`timings.csv` 为墙钟时间，生成时机器上有并发任务，波动较大（45–786 s）；\n"
           "干净的单任务耗时见 O-15（104 变量、it=300 约 40–50 s）。")
    new = ("**耗时说明（2026-11-28 对账后）**：八组实测墙钟 **38.532520–48.535693 s**"
           "（运行 ID `O14-R01…R08`，登记见 `results/o14_runs.csv`，含未舍入值与矩阵哈希）。\n"
           "计时起止：`t0` 在 `anneal_ising_batch` 之前、`wall` 在其返回之后，即**仅本地退火调用**，\n"
           "不含建矩阵、Ising 转换、解码与合法性核对。旧表述“45–786 s”在本地无对应运行记录，\n"
           "已**撤回并标记 `UNVERIFIED`**；论文引用 **38.533–48.536 s**。")
    if old not in t:
        assert "38.532520" in t, "O14 README 既非原文也非补证后版本"
        return
    p.write_text(t.replace(old, new), encoding="utf-8")


def patch_o15_readme(total):
    p = S / "O15" / "README.md"
    t = p.read_text(encoding="utf-8")
    old = ("| **SDK CPU 求解（正式 104 变量模型，每组）** | **20.81–20.96 s** | 外部实测（复审环境） "
           "| 30 次尝试×每次最多 10 样本；本包审计 SDK 记录同口径仅 0.48–0.69 s/30 次，统计范围不同，分别保留 |")
    new = ("| **SDK CPU 求解（正式 104 变量模型，每组，完整流程）** | **20.81–20.96 s** | 外部实测（复审环境，起止未在本包归档） "
           "| 30 次尝试×每次最多 10 样本 |\n"
           "| SDK 求解调用（仅 `opt.solve()`，30 次） | 0.48–0.69 s | 可复核 | 审计包 `sdk_*_runs.csv` 的 `wall_ms` 之和；"
           "计时代码 `kaiwu_local.py` L65–67：start 在 solve 前、stop 在其后，**不含初始化/转换/适配/解码/合法性核对** |\n"
           "| 整合包 `local_v1_frozen_30x10` 四组合计 | 162.556 s | **UNVERIFIED** | 来源包不在当前仓库，待提供；仅登记 |")
    if old in t:
        t = t.replace(old, new)
    note = (f"\n**对账说明（2026-11-28，P0-05）**：`entry_all_local_verified_it300` 四组未舍入合计 = "
            f"**{total:.6f} s**；若各组先保留两位小数再相加得 178.14 s（差 0.004 s，属舍入）。\n"
            "论文引用未舍入合计 **178.132 s**，并注明运行 ID `O15-R01…R04`。"
            "整合包 `local_v1_frozen_30x10` 的 162.556 s 来源不在本仓库，标 `UNVERIFIED`，不用于论文。\n")
    anchor = "## 三、资源与成本总账"
    assert anchor in t
    if "P0-05" not in t:
        t = t.replace(anchor, note + "\n" + anchor, 1)
    p.write_text(t, encoding="utf-8")


def patch_consistency_test():
    p = S / "scripts" / "consistency_test.py"
    t = p.read_text(encoding="utf-8")
    if "def o15_sa_run_ids" in t:
        return
    anchor = "def o13_manifest():"
    assert anchor in t
    new_fns = '''def o15_sa_run_ids():
    rows = read_csv(ROOT / "O15" / "local_sa_timing.csv")
    ids = [r["run_id"] for r in rows]
    assert ids == ["O15-R01", "O15-R02", "O15-R03", "O15-R04"], f"运行 ID 异常: {ids}"
    for r in rows:
        assert r["wall_s_unrounded"] and r["timing_scope"], f"{r['run_id']} 缺未舍入值或计时范围"
    total = sum(float(r["wall_s_unrounded"]) for r in rows)
    assert abs(total - 178.131869) < 1e-3, f"未舍入合计 {total} 与记录不符"
    return "O15-R01..R04；未舍入合计 178.131869 s"


def o11_reconciliation():
    d = read_json(ROOT / "O11" / "reconciliation" / "o11_reconciliation.json")
    for key in ("O11-R01_stage2_entry", "O11-R02_stage3_entry"):
        r = d["runs"][key]
        assert r["legal_correct"] == 8 and r["hits_correct"] == 8, f"{key} 正确计数应为 8"
        assert r["legal_legacy_counter"] == 0 and r["hits_legacy_counter"] == 0, f"{key} 旧计数应为 0"
    assert d["matrices"]["qubo_identical"] and d["matrices"]["mapping_identical"], "两入口矩阵/映射不一致"
    assert d["explicit_seed_batches"]["samples"] == 300, "显式种子批次数异常"
    return "两入口 8/300；旧计数器 0/300；矩阵与映射一致"


def reconciliation_table():
    rows = read_csv(ROOT / "RECONCILIATION" / "reconciliation_table.csv")
    need = {"争议数字", "原始出处", "复核结论", "正文可用口径"}
    assert need <= set(rows[0].keys()), "对账表缺列"
    assert len(rows) >= 5, f"对账表仅 {len(rows)} 行"
    unv = [r for r in rows if "UNVERIFIED" in r["复核结论"]]
    assert unv, "对账表应保留 UNVERIFIED 项"
    return f"对账表 {len(rows)} 行，含 {len(unv)} 条 UNVERIFIED"


'''
    t = t.replace(anchor, new_fns + anchor, 1)
    old_list = '        ("O10 双最优表述", o10_readme),'
    assert old_list in t
    t = t.replace(old_list,
                  '        ("O15 本地退火运行 ID 与未舍入合计", o15_sa_run_ids),\n'
                  '        ("O11 历史 0/300 对账", o11_reconciliation),\n'
                  '        ("P0-05 对账表完整", reconciliation_table),\n'
                  + old_list, 1)
    p.write_text(t, encoding="utf-8")


def main():
    total = write_local_sa()
    patch_resource_cost()
    patch_o14_readme()
    patch_o15_readme(total)
    patch_consistency_test()
    print(f"合并完成：本地退火未舍入合计 {total:.6f} s；一致性检查扩到 23 项")


if __name__ == "__main__":
    main()
