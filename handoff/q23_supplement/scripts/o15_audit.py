# -*- coding: utf-8 -*-
"""O-15：四层误差归因 + 资源成本审计。

只做两件事：
  1. 实测本机可测的耗时：精确枚举、QUBO 构建、QUBO→Ising、精度适配（本地等价）；
     本地退火耗时直接复用 entry_all_local_verified_it300.json 里已记录的 wall_s，不重跑。
  2. 把四层误差（代理/映射/量化/采样）与成本逐项整理，标明来源与口径；
     拿不到的数据写 NA 或 PENDING，不估算。

产出（q23_supplement/O15/）：
  timings.csv            本机实测耗时（多次取中位数）
  error_attribution.csv  四层误差归因
  resource_cost.csv      资源与耗时总账（含来源）
  README.md              口径说明与结论
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


def write_csv(name, rows):
    with open(OUT / name, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
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


def main():
    rows = {p: C.ranked(C.read_csv(FIX / "data" / "pred" / f"{p}_pool_predictions.csv"))
            for p in ("q2", "q3")}
    timing_rows = []

    for problem in ("q2", "q3"):
        pred = rows[problem]
        raw = np.array([float(r["V_hat"]) for r in pred])

        def enumerate_():
            """经典精确枚举：把全部合法态的能量都算出来再取最小（与交付口径一致）。"""
            _q, _off, _i, _j = q, offset, i, j
            e = _q[_i, _i] + _q[_j, _j] + _q[_i, _j]
            order = np.argsort(e, kind="stable")
            _ = (e[order[0]], order[1])

        if problem == "q2":
            model = S7.build_q2(pred)
        else:
            model = S7.build_partition(pred, "O3")
        q, offset, i, j, block = model["q"], model["offset"], model["i"], model["j"], model["block"]
        q, offset, i, j, block = model["q"], model["offset"], model["i"], model["j"], model["block"]
        mq = np.array([float(r["V_hat"]) for r in block])

        def build_():
            S7.build_partition(pred, "O3") if problem == "q3" else S7.build_q2(pred)

        M = S7.ising_matrix(q, offset)[0] if isinstance(S7.ising_matrix(q, offset), tuple) \
            else S7.ising_matrix(q, offset)

        def convert_():
            S7.ising_matrix(q, offset)

        def adapt_():
            S7.adapt_8bit(M)

        def audit_():
            S7.post_adapt_audit(M, model)

        timing_rows.append({"problem": problem, "stage": "精确枚举（逐合法态能量+排序）",
                            **timeit(enumerate_)})
        timing_rows.append({"problem": problem, "stage": "完整交付流水线（构建→转换→适配→自检）",
                            **timeit(lambda: S7.post_adapt_audit(
                                S7.adapt_8bit(S7.ising_matrix(q, offset)[0])[0], model), repeat=20)})
        timing_rows.append({"problem": problem, "stage": "QUBO 构建",
                            **timeit(build_)})
        timing_rows.append({"problem": problem, "stage": "QUBO→Ising 转换",
                            **timeit(convert_)})
        timing_rows.append({"problem": problem, "stage": "8 位适配（本地等价）",
                            **timeit(adapt_)})
        timing_rows.append({"problem": problem, "stage": "适配后自检",
                            **timeit(audit_)})
    write_csv("timings.csv", timing_rows)
    for r in timing_rows:
        print(f"{r['problem']} {r['stage']:<22} 中位 {r['median_ms']:.3f} ms")

    # 本地退火耗时：直接复用已记录结果
    entry = json.loads((RES / "entry_all_local_verified_it300.json").read_text(encoding="utf-8"))
    sa_rows = []
    for prob, pack in entry["results"].items():
        for e in pack["models"]:
            sa_rows.append({"problem": prob, "model": e["group"],
                            "variables": e["variables"], "backend": e["backend"],
                            "iters": e["audit"] and 300, "seeds": 30, "samples": 10,
                            "wall_s": round(e["wall_s"], 2),
                            "per_sample_ms": round(e["wall_s"] * 1000 / 300, 3)})
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
                    "metric": "合法态能量链（E_sdk+bias vs xᵀQx）最大偏差",
                    "value": iso["energy_chain_max_abs_diff"], "unit": "能量",
                    "source": "stage1_sdk_ising.json", "status": "measured"})
        for scheme in ("qubo_x127/4", "direct_ising_8bit", "partition_O3" if prob == "q3" else "partition_NO2"):
            r = next((x for x in q11["retention"]
                      if x["problem"] == prob and x["scheme"] == scheme), None)
            if not r:
                continue
            err.append({"layer": "量化误差", "problem": prob,
                        "metric": f"{scheme} 最优候选是否保留",
                        "value": r["argmin_preserved"], "unit": "bool",
                        "source": "O11/sorting_retention.csv", "status": "measured"})
            err.append({"layer": "量化误差", "problem": prob,
                        "metric": f"{scheme} 最低档并列数",
                        "value": r["min_tier_ties"], "unit": "个",
                        "source": "O11/sorting_retention.csv", "status": "measured"})
            err.append({"layer": "量化误差", "problem": prob,
                        "metric": f"{scheme} 最优 V̂ 损失",
                        "value": r["best_V_loss"], "unit": "V̂",
                        "source": "O11/sorting_retention.csv", "status": "measured"})
    for prob, pack in entry["results"].items():
        for e in pack["models"]:
            err.append({"layer": "采样误差", "problem": prob,
                        "metric": f"{e['group']} 合法样本比例",
                        "value": e["solver"]["legal_ratio"], "unit": "比例",
                        "source": "entry_all_local_verified_it300.json", "status": "measured"})
            err.append({"layer": "采样误差", "problem": prob,
                        "metric": f"{e['group']} 种子命中比例",
                        "value": e["solver"]["seed_hit_ratio"], "unit": "比例",
                        "source": "entry_all_local_verified_it300.json", "status": "measured"})
            err.append({"layer": "采样误差", "problem": prob,
                        "metric": f"{e['group']} 最优返回 V̂ 损失",
                        "value": (e["solver"]["best_returned_V_hat"]
                                  - e["enumeration_optimum"]["V_hat"]) if e["solver"]["best_returned_V_hat"] else None,
                        "unit": "V̂", "source": "同上", "status": "measured"})
    err.append({"layer": "代理误差", "problem": "q1",
                "metric": "03 集 MAE / RMSE / Spearman / Top-25 / Top-50",
                "value": "2.4715 / 4.5827 / 0.9383 / 8-of-25 / 20-of-50",
                "unit": "混合", "source": "Q1 交付 handoff/v1_2/ACCEPTANCE.md",
                "status": "PENDING（待 Q1 负责人确认口径）"})
    write_csv("error_attribution.csv", err)

    # ---- 资源成本 ----
    cost = []
    for r in sa_rows:
        cost.append({"item": f"本地退火求解 {r['problem']}/{r['model']}",
                     "value": r["wall_s"], "unit": "s",
                     "config": "it=300, α=0.99, 30 seeds×10 samples",
                     "source": "entry_all_local_verified_it300.json", "status": "measured"})
    for row in timing_rows:
        cost.append({"item": f"{row['problem']} {row['stage']}",
                     "value": round(row["median_ms"], 4), "unit": "ms",
                     "config": f"{row['repeats']} 次取中位", "source": "O15/timings.csv",
                     "status": "measured"})
    cost += [
        {"item": "SDK CPU 求解（复审环境 1.4.3）", "value": 20.04, "unit": "ms（中位）",
         "config": "Q2 8bit 适配，30 runs", "source": "Kaiwu_Precheck_Phase1_Summary / 审计 results",
         "status": "外部实测（非本机）"},
        {"item": "历史真机 Q2 创建→结束", "value": 4, "unit": "s",
         "config": "q2_int_01, 17 变量, SPQC-550", "source": "平台任务详情截图",
         "status": "平台记录（截图，无导出原件）"},
        {"item": "历史真机 Q2 单次演化", "value": 1.1228, "unit": "ms",
         "config": "同上", "source": "平台任务详情截图", "status": "平台记录（截图）"},
        {"item": "历史真机 Q3 创建→结束", "value": 19, "unit": "s",
         "config": "q3_int_01, 30 变量, SPQC-550", "source": "平台任务详情截图",
         "status": "平台记录（截图）"},
        {"item": "历史真机 Q3 单次演化", "value": 8.7755, "unit": "ms",
         "config": "同上", "source": "平台任务详情截图", "status": "平台记录（截图）"},
        {"item": "历史真机排队时间", "value": None, "unit": "s",
         "config": "两次任务创建即完成，未见排队", "source": "平台任务详情",
         "status": "NA（平台未单列排队字段）"},
        {"item": "平台资源扣减", "value": 2, "unit": "次优化额度",
         "config": "两次任务各 1 次", "source": "平台控制台额度变化（截图）",
         "status": "平台记录（截图）"},
        {"item": "最终 104 变量真机任务", "value": None, "unit": "-",
         "config": "O-13 待执行", "source": "-", "status": "PENDING"},
    ]
    write_csv("resource_cost.csv", cost)
    print("写出", OUT)


if __name__ == "__main__":
    main()
