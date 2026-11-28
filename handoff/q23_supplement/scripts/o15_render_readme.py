# -*- coding: utf-8 -*-
"""用 O15/timings.csv 的实测数据重新生成 README 的“本机实测耗时”一章。

目的：让 README 与 CSV 使用同一批数据，避免手写数字与实测脱节。
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "O15"
README = OUT / "README.md"

ORDER = ["q2_NO2", "q3_O3", "q3_NO2", "q3_FO2", "q3_三组合并(8,112)"]
STAGES = [
    "QUBO 构建（预测表已载入）",
    "QUBO→Ising 转换",
    "8 位适配",
    "适配后自检",
    "完整流水线（构建→转换→适配→自检）",
    "完整流水线（三组各构建→…→自检）",
]
STAGE_LABEL = {
    "QUBO 构建（预测表已载入）": "QUBO 构建（预测表已载入）",
    "QUBO→Ising 转换": "QUBO→Ising 转换",
    "8 位适配": "8 位适配",
    "适配后自检": "适配后自检",
    "完整流水线（构建→转换→适配→自检）": "**完整流水线（构建→转换→适配→自检）**",
    "完整流水线（三组各构建→…→自检）": "**完整流水线（三组各构建→…→自检）**",
}
ENUM_PREFIX = "精确枚举"


def main():
    rows = list(csv.DictReader(open(OUT / "timings.csv", encoding="utf-8-sig")))
    by = {}
    for r in rows:
        by.setdefault(r["scope"], {})[r["stage"]] = r

    lines = ["## 一、本机实测耗时", "",
             "由 `scripts/o15_render_readme.py` 从 `timings.csv` 自动生成，两边同源。", "",
             "| 范围 | 阶段 | 中位耗时 | 每次调用构建次数 |",
             "|---|---|---:|---:|"]
    for scope in ORDER:
        stages = by.get(scope, {})
        for stage in STAGES:
            if stage not in stages:
                continue
            r = stages[stage]
            calls = r.get("build_calls_per_call", "") or "0"
            lines.append(f"| {scope} | {STAGE_LABEL[stage]} | {float(r['median_ms']):.3f} ms | {calls} |")
        for stage, r in stages.items():
            if stage.startswith(ENUM_PREFIX):
                lines.append(f"| {scope} | {stage} | {float(r['median_ms']):.3f} ms | 0 |")

    lines += ["",
              "口径说明（与 CSV 字段一一对应）：",
              "",
              "1. `build_calls_per_call` 由脚本内的构建计数器统计：单组流水线每调用一次构建 1 次，"
              "三组合并每调用一次构建 3 次；计时区间内构建次数为 0 时脚本直接断言失败。",
              "2. Q3 单列三组各自 2,704 候选的计时，并单列“三组合并(8,112)”一行；"
              "后者是三组矩阵各跑一次的和，不是对 8,112 状态做单一矩阵运算。",
              "3. 所有枚举均为向量化实现（numpy 一次算完全部合法态），不能与逐点循环实现直接比较。",
              ""]

    text = README.read_text(encoding="utf-8")
    start = text.index("## 一、本机实测耗时")
    end = text.index("## 二、四层误差归因")
    README.write_text(text[:start] + "\n".join(lines) + "\n" + text[end:], encoding="utf-8")
    print("README 第一章已由 timings.csv 重新生成")


if __name__ == "__main__":
    main()
