# -*- coding: utf-8 -*-
"""把文档中所有耗时数字改为由 O15/timings.csv / local_sa_timing.csv 生成。

范围：
  1. 顶层 README 的“三、O-15 核心结论”整节；
  2. O15/README.md 成本表的流水线/枚举行，以及“四、结论”的第 1、2 条；
  3. O13/README.md 与 O15/README.md 中的真机耗时因果表述 → 统一中性句；
  4. DELIVERY_2026-11-28.md 中过期的“推断 1”和 99.9% 推导表述。

用法：python scripts/render_docs.py
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT
TIM = S / "O15" / "timings.csv"
SA = S / "O15" / "local_sa_timing.csv"


def load_timings():
    rows = list(csv.DictReader(open(TIM, encoding="utf-8-sig")))
    out = {}
    for r in rows:
        out.setdefault(r["scope"], {})[r["stage"]] = r
    return out


def ms(scope_stage, timings):
    scope, stage = scope_stage
    return f"{float(timings[scope][stage]['median_ms']):.3f}"


def render_top_readme(timings):
    p = S / "README.md"
    text = p.read_text(encoding="utf-8")
    q2 = "q2_NO2"
    q3s = ["q3_O3", "q3_NO2", "q3_FO2"]
    tot = "q3_三组合并(8,112)"
    b = lambda sc, st: float(timings[sc][st]["median_ms"])
    enum_stage = next(s for s in timings[q2] if s.startswith("精确枚举"))
    enum_stage3 = next(s for s in timings[q3s[0]] if s.startswith("精确枚举"))
    enum_tot_stage = next(s for s in timings[tot] if s.startswith("精确枚举"))
    sa = list(csv.DictReader(open(SA, encoding="utf-8-sig")))
    sa_map = {r["model"]: float(r["wall_s"]) for r in sa}

    block = [
        "## 三、O-15 核心结论（详见 `O15/README.md`）",
        "",
        "耗时以 `O15/timings.csv` 为**唯一数值来源**；下表与 O-15 第一章表格均由该 CSV 生成，"
        "完整表格见 [O15/README 第一章](O15/README.md#一本机实测耗时)。",
        "",
        "| 阶段 | Q2 | Q3 O3 | Q3 NO2 | Q3 FO2 | Q3 三组合并 |",
        "|---|---:|---:|---:|---:|---:|",
        f"| QUBO 构建 | {b(q2,'QUBO 构建（预测表已载入）'):.3f} ms | "
        f"{b(q3s[0],'QUBO 构建（预测表已载入）'):.3f} | "
        f"{b(q3s[1],'QUBO 构建（预测表已载入）'):.3f} | "
        f"{b(q3s[2],'QUBO 构建（预测表已载入）'):.3f} | — |",
        f"| QUBO→Ising | {b(q2,'QUBO→Ising 转换'):.3f} ms | "
        f"{b(q3s[0],'QUBO→Ising 转换'):.3f} | {b(q3s[1],'QUBO→Ising 转换'):.3f} | "
        f"{b(q3s[2],'QUBO→Ising 转换'):.3f} | — |",
        f"| 8 位适配 | {b(q2,'8 位适配'):.3f} ms | {b(q3s[0],'8 位适配'):.3f} | "
        f"{b(q3s[1],'8 位适配'):.3f} | {b(q3s[2],'8 位适配'):.3f} | — |",
        f"| 适配后自检 | {b(q2,'适配后自检'):.3f} ms | {b(q3s[0],'适配后自检'):.3f} | "
        f"{b(q3s[1],'适配后自检'):.3f} | {b(q3s[2],'适配后自检'):.3f} | — |",
        f"| **完整流水线（含构建）** | **{b(q2,'完整流水线（构建→转换→适配→自检）'):.3f} ms** | "
        f"**{b(q3s[0],'完整流水线（构建→转换→适配→自检）'):.3f}** | "
        f"**{b(q3s[1],'完整流水线（构建→转换→适配→自检）'):.3f}** | "
        f"**{b(q3s[2],'完整流水线（构建→转换→适配→自检）'):.3f}** | "
        f"**{b(tot,'完整流水线（三组各构建→…→自检）'):.3f} ms** |",
        f"| 精确枚举（逐合法态能量） | {b(q2,enum_stage):.3f} ms | {b(q3s[0],enum_stage3):.3f} | "
        f"{b(q3s[1],enum_stage3):.3f} | {b(q3s[2],enum_stage3):.3f} | {b(tot,enum_tot_stage):.3f} ms |",
        "",
        f"本地退火（it=300, α=0.99, 30 批次×10 样本）：Q2 {sa_map.get('NO2', 0):.1f} s、"
        f"Q3 O3 {sa_map.get('O3', 0):.1f} s、NO2 {sa_map.get('NO2', 0):.1f} s（与 Q2 同模型）、"
        f"FO2 {sa_map.get('FO2', 0):.1f} s。",
        "真机：四组 104 变量任务创建至结束 16–112 秒；平台另报单次演化时长，排队和整任务执行时长未单列，记为 `NA`；"
        "额度 31 → 24，共扣 7 次（含早期探针任务）。",
        "四层误差表见 `O15/error_attribution.csv`，成本总账见 `O15/resource_cost.csv`。",
        "",
    ]
    start = text.index("## 三、O-15 核心结论")
    end = text.index("## 四点五、O-14 结论")
    p.write_text(text[:start] + "\n".join(block) + "\n" + text[end:], encoding="utf-8")
    print("顶层 README 第三节已由 CSV 生成")


def render_o15_readme(timings):
    p = S / "O15" / "README.md"
    text = p.read_text(encoding="utf-8")
    q2, q3s, tot = "q2_NO2", ["q3_O3", "q3_NO2", "q3_FO2"], "q3_三组合并(8,112)"
    b = lambda sc, st: float(timings[sc][st]["median_ms"])
    pipe_stage = "完整流水线（构建→转换→适配→自检）"
    enum_stage = next(s for s in timings[q2] if s.startswith("精确枚举"))
    enum_tot_stage = next(s for s in timings[tot] if s.startswith("精确枚举"))

    # 成本表中的两行
    text = re.sub(
        r"\| 本机完整流水线（Q2 / Q3 单组 / Q3 三组） \|[^\n]*\n",
        f"| 本机完整流水线（含构建；Q2 / Q3 单组 ×3 / Q3 三组） | "
        f"{b(q2,pipe_stage):.3f} / {b(q3s[0],pipe_stage):.3f}、{b(q3s[1],pipe_stage):.3f}、"
        f"{b(q3s[2],pipe_stage):.3f} / {b(tot,'完整流水线（三组各构建→…→自检）'):.3f} ms | 实测 | `timings.csv` |\n",
        text)
    text = re.sub(
        r"\| 本机精确枚举（2,704 / 8,112） \|[^\n]*\n",
        f"| 本机精确枚举（2,704 / 8,112） | {b(q2,enum_stage):.3f} / "
        f"{b(tot,enum_tot_stage):.3f} ms | 实测 | `timings.csv` |\n",
        text)

    # 结论第 1 条
    text = re.sub(
        r"1\. \*\*求解成本分层\*\*[^\n]*\n[^\n]*\n[^\n]*\n",
        f"1. **求解成本分层**：完整流水线（含构建）在本机为毫秒级——Q2 {b(q2,pipe_stage):.3f} ms、"
        f"Q3 单组 {b(q3s[0],pipe_stage):.3f}/{b(q3s[1],pipe_stage):.3f}/{b(q3s[2],pipe_stage):.3f} ms、"
        f"三组合并 {b(tot,'完整流水线（三组各构建→…→自检）'):.3f} ms；"
        f"经典精确枚举 {b(q2,enum_stage):.3f}/{b(tot,enum_tot_stage):.3f} ms；本地退火 40–50 s/模型；"
        f"SDK CPU 每组约 20.8–21.0 s。\n",
        text)

    # 结论第 2 条
    text = re.sub(
        r"2\. \*\*平台耗时不能用于论证退火参数因果\*\*[^\n]*\n[^\n]*\n",
        "2. **真机耗时只作事实记录**：四组 104 变量任务的创建至结束耗时为 16–112 秒。"
        "平台另报单次演化时长，排队和整任务执行时长未单列，记为 `NA`。\n",
        text)
    p.write_text(text, encoding="utf-8")
    print("O15 README 成本表与结论已由 CSV 生成")


def neutralize_causal():
    fixed = ("四组 104 变量任务的创建至结束耗时为 16–112 秒。"
             "平台另报单次演化时长，排队和整任务执行时长未单列，记为 `NA`。")
    # O13 README
    p = S / "O13" / "README.md"
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"1\. \*\*总耗时主要由排队/调度决定，与矩阵规模无关\*\*[^\n]*\n[^\n]*\n",
               f"1. **真机耗时只作事实记录**：{fixed}\n", t)
    p.write_text(t, encoding="utf-8")
    # O15 README（若仍有残留）
    q = S / "O15" / "README.md"
    t = q.read_text(encoding="utf-8")
    t = t.replace("真机总耗时 4–112 s（主要由排队/调度决定）。", fixed)
    t = t.replace("总耗时主要由排队/调度决定，与矩阵规模无关", "真机耗时只作事实记录")
    q.write_text(t, encoding="utf-8")
    print("因果表述已替换为中性句")


def fix_delivery():
    p = S / "DELIVERY_2026-11-28.md"
    t = p.read_text(encoding="utf-8")
    t = t.replace("额度标“推断 1（页面数值未提供）”", "额度实测 1（31 → 24，共 7 次）")
    t = t.replace("| 真机排队时间 | **NA**，平台未单列；总耗时−演化≈99.9%，不得据此推断排队因果 |",
                  "| 真机排队时间 | **NA**，平台未单列；四组 104 变量任务创建至结束 16–112 秒，"
                  "不据此推断排队或调度因果 |")
    p.write_text(t, encoding="utf-8")
    print("DELIVERY 过期表述已修正")


def main():
    timings = load_timings()
    render_top_readme(timings)
    render_o15_readme(timings)
    neutralize_causal()
    fix_delivery()


if __name__ == "__main__":
    main()
