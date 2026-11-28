# -*- coding: utf-8 -*-
"""从已归档的 O-15 CSV 更新交付文档中的耗时表及摘要。"""

import csv
import re
from pathlib import Path

import o15_render_readme

ROOT = Path(__file__).resolve().parents[1]
S = ROOT
TIM = S / "O15" / "timings.csv"
SA = S / "O15" / "local_sa_timing.csv"


def load_timings():
    timings = {}
    with TIM.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            timings.setdefault(row["scope"], {})[row["stage"]] = row
    return timings


def load_local_sa():
    with SA.open(encoding="utf-8-sig", newline="") as fh:
        return {(r["problem"], r["model"]): float(r["wall_s"]) for r in csv.DictReader(fh)}


def render_top_readme(timings, sa):
    p = S / "README.md"
    text = p.read_text(encoding="utf-8")
    q2 = "q2_NO2"
    q3s = ["q3_O3", "q3_NO2", "q3_FO2"]
    tot = "q3_三组合并(8,112)"
    b = lambda sc, st: float(timings[sc][st]["median_ms"])
    enum_stage = next(s for s in timings[q2] if s.startswith("精确枚举"))
    enum_stage3 = next(s for s in timings[q3s[0]] if s.startswith("精确枚举"))
    enum_tot_stage = next(s for s in timings[tot] if s.startswith("精确枚举"))

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
        f"本地退火（it=300, α=0.99, 30 批次×10 样本）：Q2 {sa['q2', 'NO2']:.2f} s，"
        f"Q3 O3 {sa['q3', 'O3']:.2f} s、NO2 {sa['q3', 'NO2']:.2f} s、FO2 {sa['q3', 'FO2']:.2f} s。",
        "真机：四组 104 变量任务创建至结束 16–112 秒；平台另报单次演化时长，排队和整任务执行时长未单列，记为 `NA`；"
        "额度 31 → 24，共扣 7 次（含早期探针任务）。",
        "四层误差表见 `O15/error_attribution.csv`，成本总账见 `O15/resource_cost.csv`。",
        "",
    ]
    start = text.index("## 三、O-15 核心结论")
    end = text.index("## 四点五、O-14 结论")
    p.write_text(text[:start] + "\n".join(block) + "\n" + text[end:], encoding="utf-8")
    print("顶层 README 第三节已由 CSV 生成")


def replace_line(text, prefix, line):
    updated, count = re.subn(r"^" + re.escape(prefix) + r".*$", lambda _: line, text, flags=re.M)
    if count != 1:
        raise ValueError(f"预期恰好一行以 {prefix!r} 开头，实际找到 {count} 行")
    return updated


def render_o15_readme(timings, sa):
    p = S / "O15" / "README.md"
    text = p.read_text(encoding="utf-8")
    q2, q3s, tot = "q2_NO2", ["q3_O3", "q3_NO2", "q3_FO2"], "q3_三组合并(8,112)"
    b = lambda sc, st: float(timings[sc][st]["median_ms"])
    pipe_stage = "完整流水线（构建→转换→适配→自检）"
    enum_stage = next(s for s in timings[q2] if s.startswith("精确枚举"))
    enum_tot_stage = next(s for s in timings[tot] if s.startswith("精确枚举"))

    text = replace_line(
        text, "| 本机完整流水线（",
        f"| 本机完整流水线（含构建；Q2 / Q3 单组 ×3 / Q3 三组） | "
        f"{b(q2,pipe_stage):.3f} / {b(q3s[0],pipe_stage):.3f}、{b(q3s[1],pipe_stage):.3f}、"
        f"{b(q3s[2],pipe_stage):.3f} / {b(tot,'完整流水线（三组各构建→…→自检）'):.3f} ms | 实测 | `timings.csv` |")
    text = replace_line(
        text, "| 本机精确枚举（2,704 / 8,112） |",
        f"| 本机精确枚举（2,704 / 8,112） | {b(q2,enum_stage):.3f} / "
        f"{b(tot,enum_tot_stage):.3f} ms | 实测 | `timings.csv` |")
    text = replace_line(
        text, "| 本地退火（it=300, α=0.99, 30×10） |",
        f"| 本地退火（it=300, α=0.99, 30×10） | Q2 {sa['q2', 'NO2']:.2f} s，"
        f"Q3 O3 {sa['q3', 'O3']:.2f} s、NO2 {sa['q3', 'NO2']:.2f} s、FO2 {sa['q3', 'FO2']:.2f} s"
        " | 实测（本地 CPU） | `local_sa_timing.csv` |")
    text = replace_line(
        text, "1. **求解成本分层**",
        f"1. **求解成本分层**。完整流水线（含构建）在本机为毫秒级。Q2 {b(q2,pipe_stage):.3f} ms，"
        f"Q3 单组 {b(q3s[0],pipe_stage):.3f}/{b(q3s[1],pipe_stage):.3f}/{b(q3s[2],pipe_stage):.3f} ms、"
        f"三组合并 {b(tot,'完整流水线（三组各构建→…→自检）'):.3f} ms。"
        f"经典精确枚举为 {b(q2,enum_stage):.3f}/{b(tot,enum_tot_stage):.3f} ms。"
        "本地退火和 SDK CPU 求解的分组耗时见成本表。")
    p.write_text(text, encoding="utf-8")
    print("O15 README 成本表与结论已由 CSV 生成")


def main():
    timings = load_timings()
    sa = load_local_sa()
    o15_render_readme.main()
    render_top_readme(timings, sa)
    render_o15_readme(timings, sa)


if __name__ == "__main__":
    main()
