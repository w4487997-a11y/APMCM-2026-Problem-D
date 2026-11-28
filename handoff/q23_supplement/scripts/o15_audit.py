# -*- coding: utf-8 -*-
"""O-15：四层误差归因 + 资源成本总账（v2，按复审口径修正）。

修正点：
  1. Q3 计时覆盖 **三组各自 2,704 候选**，并单独测“三组合并 8,112”的总耗时，注明口径；
  2. “完整流水线”改为**包含 QUBO 构建**的整段（构建→转换→适配→自检），不再复用预建矩阵；
  3. 资源成本补入 O-13 六个真机任务（4 新 + 2 历史）；
  4. 补录正式模型 SDK CPU 耗时（每组约 20.81–20.96 s，30 次尝试×最多 10 样本），
     历史 20.04 ms 保留为不同配置记录；
  5. 四层误差中量化层引用 O-11 的新口径（原最优是否在最低档 / 按 ID 决胜是否仍第一）。

产出：O15/timings.csv、local_sa_timing.csv、error_attribution.csv、resource_cost.csv、README.md
"""

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT.parent / "q23_fix"
sys.path.insert(0, str(FIX / "scripts"))
import common as C
import stage7_entry as S7

OUT = ROOT / "O15"
OUT.mkdir(parents=True, exist_ok=True)
RES = FIX / "results"

BUILD_CALLS = {"n": 0}   # 用于证明计时段内确实执行了构建


def write_csv(name, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(OUT / name, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, keys, restval="")
        w.writeheader()
        w.writerows(rows)


def timeit(fn, repeat=50):
    ts = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t0) * 1000)
    return {"median_ms": float(np.median(ts)), "min_ms": float(np.min(ts)),
            "max_ms": float(np.max(ts)), "repeats": repeat}


def build_models():
    q2 = C.ranked(C.read_csv(FIX / "data" / "pred" / "q2_pool_predictions.csv"))
    q3 = C.ranked(C.read_csv(FIX / "data" / "pred" / "q3_pool_predictions.csv"))
    return {
        "q2_NO2": S7.build_q2(q2),
        "q3_O3": S7.build_partition(q3, "O3"),
        "q3_NO2": S7.build_partition(q3, "NO2"),
        "q3_FO2": S7.build_partition(q3, "FO2"),
    }


def enumerate_model(model):
    q, off, i, j = model["q"], model["offset"], model["i"], model["j"]
    e = q[i, i] + q[j, j] + q[i, j]
    order = np.argsort(e, kind="stable")
    return e[order[0]]


def main():
    rows_q2 = C.ranked(C.read_csv(FIX / "data" / "pred" / "q2_pool_predictions.csv"))
    rows_q3 = C.ranked(C.read_csv(FIX / "data" / "pred" / "q3_pool_predictions.csv"))
    models = build_models()

    def build_call(scope):
        BUILD_CALLS["n"] += 1
        if scope.startswith("q3"):
            return S7.build_partition(rows_q3, scope.split("_")[-1])
        return S7.build_q2(rows_q2)

    def pipeline_scope(scope):
        """完整流水线：构建 → 转换 → 适配 → 自检（构建在计时段内）。"""
        model = build_call(scope)
        M, _, _, _ = S7.ising_matrix(model["q"], model["offset"])
        adj, _ = S7.adapt_8bit(M)
        S7.post_adapt_audit(adj, model)
    timing_rows, enum_rows = [], []
    for name, m in models.items():
        q, off, i, j = m["q"], m["offset"], m["i"], m["j"]
        M = S7.ising_matrix(q, off)[0]
        timing_rows.append({"scope": name, "stage": "QUBO 构建（预测表已载入）",
                            **timeit(lambda: build_call(name))})
        timing_rows.append({"scope": name, "stage": "QUBO→Ising 转换",
                            **timeit(lambda: S7.ising_matrix(q, off))})
        timing_rows.append({"scope": name, "stage": "8 位适配",
                            **timeit(lambda: S7.adapt_8bit(M))})
        timing_rows.append({"scope": name, "stage": "适配后自检",
                            **timeit(lambda: S7.post_adapt_audit(M, m))})
        BUILD_CALLS["n"] = 0
        t_pipeline = timeit(lambda: pipeline_scope(name), repeat=20)
        assert BUILD_CALLS["n"] == 20, f"计时段内构建次数异常: {BUILD_CALLS['n']} != 20"
        timing_rows.append({"scope": name, "stage": "完整流水线（构建→转换→适配→自检）",
                            **t_pipeline, "build_calls_per_call": 1})
        timing_rows.append({"scope": name, "stage": f"精确枚举（{len(m['block'])} 合法态能量+排序）",
                            **timeit(lambda: enumerate_model(m))})
        enum_rows.append({"scope": name, "candidates": len(m["block"]),
                          "enumeration_ms": None})
    # Q3 三组合并的总耗时（口径：三组矩阵各跑一次，含构建）
    q3_models = [models["q3_O3"], models["q3_NO2"], models["q3_FO2"]]
    BUILD_CALLS["n"] = 0
    q3_total = timeit(lambda: [pipeline_scope(s) for s in ("q3_O3", "q3_NO2", "q3_FO2")], repeat=20)
    assert BUILD_CALLS["n"] == 60, f"三组合并计时段构建次数异常: {BUILD_CALLS['n']} != 60"
    q3_enum = timeit(lambda: [enumerate_model(m) for m in q3_models])
    timing_rows.append({"scope": "q3_三组合并(8,112)", "stage": "完整流水线（三组各构建→…→自检）",
                        **q3_total, "build_calls_per_call": 3})
    timing_rows.append({"scope": "q3_三组合并(8,112)", "stage": "精确枚举（三组 2,704×3 逐组能量+排序）",
                        **q3_enum})
    write_csv("timings.csv", timing_rows)
    for r in timing_rows:
        print(f"{r['scope']:<22} {r['stage']:<34} {r['median_ms']:>9.3f} ms")

    # 本地退火耗时（复用已记录结果）
    entry = json.loads((RES / "entry_all_local_verified_it300.json").read_text(encoding="utf-8"))
    sa_rows = []
    for prob, pack in entry["results"].items():
        for e in pack["models"]:
            sa_rows.append({"problem": prob, "model": e["group"], "variables": e["variables"],
                            "config": "it=300, α=0.99, 30 种子×10 样本",
                            "wall_s": round(e["wall_s"], 2),
                            "per_sample_ms": round(e["wall_s"] * 1000 / 300, 3),
                            "source": "entry_all_local_verified_it300.json（本地退火，非 SDK）"})
    write_csv("local_sa_timing.csv", sa_rows)

    # ---- 四层误差 ----
    st1 = json.loads((RES / "stage1_sdk_ising.json").read_text(encoding="utf-8"))
    q11 = json.loads((ROOT / "O11" / "o11_metrics.json").read_text(encoding="utf-8"))
    err = []
    for prob in ("q2", "q3"):
        iso = st1["problems"][prob]["sdk_ising"]
        err.append({"layer": "映射误差", "problem": prob,
                    "metric": "SDK Ising 与独立公式矩阵最大偏差",
                    "value": iso["matrix_vs_formula_max_abs_diff"], "unit": "系数",
                    "source": "stage1_sdk_ising.json（真实 SDK）", "status": "measured"})
        err.append({"layer": "映射误差", "problem": prob,
                    "metric": "合法态能量链 E_sdk+bias vs xᵀQx 最大偏差",
                    "value": iso["energy_chain_max_abs_diff"], "unit": "能量",
                    "source": "stage1_sdk_ising.json", "status": "measured"})
        for scheme in ("qubo_x127/4", "qubo_xfloor", "direct_ising_8bit",
                       "clip_d0.4_l1.02", "partition_O3" if prob == "q3" else "partition_NO2"):
            r = next((x for x in q11["retention"]
                      if x["problem"] == prob and x["scheme"] == scheme), None)
            if not r:
                continue
            err.append({"layer": "量化误差", "problem": prob,
                        "metric": f"{scheme} 原最优是否仍在最低能量档",
                        "value": r["best_in_min_tier"], "unit": "bool",
                        "source": "O11/sorting_retention.csv", "status": "measured"})
            err.append({"layer": "量化误差", "problem": prob,
                        "metric": f"{scheme} 按 (能量,ID) 决胜后原最优是否第一",
                        "value": r["argmin_after_id_break"], "unit": "bool",
                        "source": "O11/sorting_retention.csv", "status": "measured"})
            err.append({"layer": "量化误差", "problem": prob,
                        "metric": f"{scheme} 最低档并列数",
                        "value": r["min_tier_ties"], "unit": "个",
                        "source": "O11/sorting_retention.csv", "status": "measured"})
            err.append({"layer": "量化误差", "problem": prob,
                        "metric": f"{scheme} 按 ID 决胜后的 V̂ 损失（并列造成，非能量差）",
                        "value": r["best_V_loss"], "unit": "V̂",
                        "source": "O11/sorting_retention.csv", "status": "measured"})
    for prob, pack in entry["results"].items():
        for e in pack["models"]:
            err.append({"layer": "采样误差", "problem": prob,
                        "metric": f"{e['group']} 合法样本比例（本地退火 it=300）",
                        "value": e["solver"]["legal_ratio"], "unit": "比例",
                        "source": "entry_all_local_verified_it300.json", "status": "measured"})
            err.append({"layer": "采样误差", "problem": prob,
                        "metric": f"{e['group']} 批次命中率（30 批×10 样本，任一批含最优即记命中）",
                        "value": e["solver"]["seed_hit_ratio"], "unit": "比例",
                        "source": "entry_all_local_verified_it300.json", "status": "measured"})
    err.append({"layer": "代理误差", "problem": "q1",
                "metric": "03 集 MAE / RMSE / Spearman / Top-25 / Top-50",
                "value": "2.4715 / 4.5827 / 0.9383 / 8-of-25 / 20-of-50",
                "unit": "混合",
                "source": "Q1 交付 experiments/q1_v12/REPORT.md、PROJECT_STATUS.md、README.md（本组未独立复算）",
                "status": "外部记录（Q1 交付，引用未复算）"})
    write_csv("error_attribution.csv", err)

    # ---- 资源成本 ----
    cost = []
    for r in sa_rows:
        cost.append({"item": f"本地退火 {r['problem']}/{r['model']}", "value": r["wall_s"],
                     "unit": "s", "config": r["config"], "source": r["source"],
                     "status": "measured（本地 CPU）"})
    for row in timing_rows:
        cost.append({"item": f"{row['scope']} {row['stage']}", "unit": "ms",
                     "value": round(row["median_ms"], 4),
                     "config": f"{row['repeats']} 次取中位", "source": "O15/timings.csv",
                     "status": "measured（本机）"})
    cost += [
        {"item": "SDK CPU 求解（正式 104 变量模型，每组）", "value": "20.81–20.96", "unit": "s",
         "config": "30 次尝试，每次最多返回 10 样本",
         "source": "复审环境 Kaiwu 记录（非本机）；本包审计 SDK 运行记录同口径仅 0.48–0.69 s/30 次，"
                   "两者统计范围不同，分别保留",
         "status": "外部实测（复审环境）"},
        {"item": "SDK CPU 求解（历史配置，Q2 8 位适配）", "value": 20.04, "unit": "ms（中位）",
         "config": "30 runs，单次运行中位",
         "source": "Kaiwu_Precheck_Phase1_Summary / 审计 results", "status": "外部实测（不同配置）"},
        {"item": "真机 q2_NO2.csv_01（104 变量）", "value": 22, "unit": "s",
         "config": "创建→结束；单次演化 15.0116 ms；样本 10，合法 1",
         "source": "O13/receipt_template.csv、O13/evidence/", "status": "平台记录"},
        {"item": "真机 22222_01（q3_O3，104 变量）", "value": 74, "unit": "s",
         "config": "创建→结束；单次演化 9.7488 ms；样本 10，合法 4",
         "source": "O13/receipt_template.csv、O13/evidence/", "status": "平台记录"},
        {"item": "真机 333333_01（q3_NO2，104 变量）", "value": 112, "unit": "s",
         "config": "创建→结束；单次演化 0.6991 ms；样本 7，合法 0（原始反例保留）",
         "source": "O13/receipt_template.csv、O13/evidence/", "status": "平台记录"},
        {"item": "真机 444444_01（q3_FO2，104 变量）", "value": 16, "unit": "s",
         "config": "创建→结束；单次演化 7.3587 ms；样本 5，合法 1",
         "source": "O13/receipt_template.csv、O13/evidence/", "status": "平台记录"},
        {"item": "真机 q2_int_01（历史 17 变量）", "value": 4, "unit": "s",
         "config": "创建→结束；单次演化 1.1228 ms；样本 10，合法 1",
         "source": "O13/evidence/q2_int_01_task_page.png", "status": "平台记录"},
        {"item": "真机 q3_int_01（历史 30 变量）", "value": 19, "unit": "s",
         "config": "创建→结束；单次演化 8.7755 ms；样本 10，合法 1",
         "source": "O13/evidence/q3_int_01_task_page.png", "status": "平台记录"},
        {"item": "真机排队时间", "value": None, "unit": "s",
         "config": "平台未单列；总耗时含排队与执行",
         "source": "O13 任务详情", "status": "NA（平台未单列）"},
        {"item": "真机额度扣减（优化额度）", "value": 7, "unit": "次",
         "config": "31（2026-11-27 18:31）→ 24（2026-11-28 16:32）；平台显示 7 个任务，每次 1 次；31−24=7",
         "source": "O13/evidence/credits_before_2026-11-27.png、credits_after_2026-11-28.png；O13/results/credits_ledger.csv",
         "status": "实测（起止均有凭证）"},
        {"item": "真机任务平均运行时间（平台口径）", "value": 6.1030, "unit": "ms",
         "config": "平台“用量总览”对 7 个任务的统计，未说明是否含排队",
         "source": "O13/evidence/credits_after_2026-11-28.png", "status": "平台记录（口径未说明）"},
        {"item": "真机总耗时 − 单次演化（推导）", "value": "21.99 / 73.99 / 111.99 / 15.99", "unit": "s",
         "config": "q2_NO2 / q3_O3 / q3_NO2 / q3_FO2；仅说明总耗时中约 99.9% 不在单次演化内",
         "source": "O13/receipt_template.csv 由 total_seconds 与 evolve_ms 相减",
         "status": "推导值（含排队/调度/启动，非实测排队）"},
    ]
    write_csv("resource_cost.csv", cost)
    print("写出", OUT)


if __name__ == "__main__":
    main()
