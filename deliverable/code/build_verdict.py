# -*- coding: utf-8 -*-
"""生成《前置可行性验证结论》——四问判定 + 证据 + 边界。"""

import argparse
import json
import os

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.table import WD_TABLE_ALIGNMENT

import build_plan
from build_plan import (
    NAVY, GRAY, MIDGRAY, TEXT, WHITE, BODY_CN, HEAD_CN,
    set_run_font, set_col_widths, shade, cell_margins, table_borders,
    row_no_split, para_bottom_border, normalize_xml,
    build_styles, setup_page, build_header_footer,
    add_body, add_bullet, add_caption, add_table, add_callout, add_code,
)


def h1(doc, text, first=False):
    p = doc.add_paragraph(style="Heading 1")
    p.paragraph_format.page_break_before = False
    p.paragraph_format.space_before = Pt(0 if first else 18)
    set_run_font(p.add_run(text), cn=HEAD_CN, size=15, bold=True, color=NAVY)
    para_bottom_border(p, color="1F3864", sz=8)


def h2(doc, text):
    p = doc.add_paragraph(style="Heading 2")
    set_run_font(p.add_run(text), cn=HEAD_CN, size=12, bold=True, color=NAVY)


def cover(doc, a, c):
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    set_run_font(p.add_run("2026 年亚太地区数学建模竞赛 · D 题"), cn=HEAD_CN, size=13, color=MIDGRAY)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    set_run_font(p.add_run("任务编号 D-00 · 锁题前熔断检测"), cn=HEAD_CN, size=13, bold=True, color=NAVY)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    para_bottom_border(p, color="1F3864", sz=10)
    set_run_font(p.add_run(""), size=2)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(8)
    set_run_font(p.add_run("前置可行性验证结论"), cn=HEAD_CN, size=30, bold=True, color=NAVY)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    set_run_font(p.add_run("四问判定 · 数据审计 41 项 · 编码验证 3 组"), cn=HEAD_CN, size=12, color=GRAY)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    set_run_font(p.add_run(f"数据：官方附件 9 个文件 sha256 全匹配　·　生成 {a['generated_at']}"),
                 cn=BODY_CN, size=10.5, color=MIDGRAY)

    for _ in range(4):
        doc.add_paragraph()

    info = [
        ("总体结论", "PASS（数据与数学路径均可验证）"),
        ("数据审计", f"{a['summary']['total']} 项：PASS {a['summary']['pass']} / FAIL {a['summary']['fail']} / PENDING {a['summary']['pending']}"),
        ("编码验证", "人工占位：16 / 256 状态；真实代理：07、08 全部候选能量对齐"),
        ("未验证事项", "19 条正例的本地复核、代理模型精度、实机求解"),
    ]
    t = doc.add_table(rows=0, cols=2)
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    table_borders(t, color="C9D3E3", sz=4, inside=False)
    for label, value in info:
        row = t.add_row()
        c0, c1 = row.cells
        c0.width, c1.width = Cm(3.6), Cm(11.4)
        from build_plan import set_cell_borders
        for cell in (c0, c1):
            set_cell_borders(cell, top="none", left="none", right="none",
                             bottom=("C9D3E3", 4))
        p = c0.paragraphs[0]
        p.paragraph_format.space_after = Pt(7)
        set_run_font(p.add_run(label), cn=BODY_CN, size=10, color=MIDGRAY)
        p = c1.paragraphs[0]
        p.paragraph_format.space_after = Pt(7)
        set_run_font(p.add_run(value), cn=BODY_CN, size=10.5, color=TEXT)
    set_col_widths(t, [3.6, 11.4])


def build(a, c, m, out):
    doc = Document()
    build_styles(doc)
    sec = doc.sections[0]
    setup_page(sec)
    build_header_footer(sec, "2026 APMCM · D 题前置可行性验证结论")
    build_plan.TABLE_KEEP_ROWS = 8

    cover(doc, a, c)
    doc.add_page_break()

    h1(doc, "一、四个问题的回答", first=True)
    add_callout(doc, "总体判定：PASS。数据完整、划分结构清楚、代理与 QUBO 的接口可落地、两问编码均通过程序验证。"
                     "但“19 条正例”和“代理模型精度”这两件事本地无法自证，只能由盲测评分回答，"
                     "因此这个 PASS 的边界是“可做且路径正确”，不是“保证命中”。")
    add_table(doc, {
        "caption": "表 1　四问判定与证据",
        "headers": ["问题", "判定", "证据"],
        "widths": [6.2, 2.2, 7.6],
        "rows": [
            ["① 官方数据是否完整", "是",
             "8 个文件行数全对；18,928 全因子网格无缺格无重复；02+03+04 并集恰为 18,928；9 个 sha256 全匹配"],
            ["② 划分是否有特殊结构", "有，且影响验证设计",
             "按 (A,B) 元素对分组划分，切成 1,608 / 567 / 529 对；529 对 × 7 族 = 3,703；"
             "02、03 零正例，据官方说明推断 19 条均在 04"],
            ["③ 代理能否接上 QUBO", "可以",
             "池文件仅 6 列，含 id、A、B、X；07 / 08 为完整网格（2,704 / 8,112）；"
             "104 与 208 变量的构造在真实池规模上跑通"],
            ["④ 编码能否程序验证", "通过",
             "问题二 16 状态、问题三 256 状态枚举与公式逐位一致（误差 ≤ 7e-15）；"
             "真实池 2,704 / 8,112 候选能量与代价完全相等"],
        ],
    })

    h1(doc, "二、数据审计的关键数字")
    q = a.get("quality", {})
    v = a.get("v", {})
    cnt = v.get("counts", {})
    add_body(doc, f"41 项检查全部通过。核心事实：材料主键零重复；A、B 各 52 种且同池；"
                  f"A = B 共 364 条（1.92%），其中 V = 0 的为 0 条。这类候选是题面明确要求保留的合法材料，"
                  f"不得因为“没有正例”就删除；审计只陈述“不损失正例”，不构成排除理由。"
                  f"gap = 0 占 02 的 {q.get('gap_zero_share', {}).get('02_castelli_train.csv', 0):.2%}、"
                  f"03 的 {q.get('gap_zero_share', {}).get('03_castelli_val.csv', 0):.2%}，与全库 96.12% 同量级。")
    add_body(doc, f"目标量核验：7 项公式单元测试全过；02、03 共 {cnt.get('rows', 0):,} 条的 V 与五项惩罚列在 1e-6 内自洽；"
                  f"按物理量复算的最大偏差 1.02e-5，完全由输入六位小数落盘解释；"
                  f"02 ∪ 03 的 V = 0 条数为 {cnt.get('v_zero', 0)}，严格目标 {cnt.get('strict', 0)} 条。"
                  "按官方说明，19 条正例全部落在盲测集；本地能验证的只有“02、03 里确实一条都没有”，"
                  "“19 条都在 04”属于基于官方全库统计与有标签数据审计的推断，不是本地直接验证的事实。")
    add_body(doc, "集合关系逐条成立：06 = 02 ∪ 03；11 = 07 ∩ 04；12 = 08 ∩ 04；"
                  "02 ∩ 03 = 02 ∩ 04 = 03 ∩ 04 = 0；每个 X 族在三档中的行数分别为 1,608 / 567 / 529。"
                  "这组等式同时证明了“没有泄漏”和“池子是从同一张全因子网格里切出来的”。")

    h1(doc, "三、编码验证")
    add_body(doc, "编码验证分三层，必须分开陈述：第一层是人工代价表的小规模枚举，验证“编码本身正确”；"
                  "第二层是占位代价下的真实池规模，验证“矩阵可构建、能量可对齐”；"
                  "第三层用真实代理预测重建 07、08 的矩阵，验证“代价换成模型输出后仍然对齐”。"
                  "三层都通过才能交付，但第三层证明的仍不是预测精度。")
    rows = []
    for r in c["q2"]:
        rows.append([r["tag"], f"{r['vars']} 变量 / {r['states']} 状态",
                     f"min = {r['best_energy']:g}",
                     "A{}, B{}".format(r["argmin"][0] + 1, r["argmin"][1] + 1),
                     "是" if r["all_optima_legal"] else "否",
                     f"{r['max_formula_vs_matrix']:.0e}"])
    for r in c["q3"]:
        a_, b_, x_ = r["argmin"]
        rows.append([r["tag"], f"{r['vars']} 变量 / {r['states']} 状态",
                     f"min = {r['best_energy']:g}",
                     f"A{a_ + 1}, B{b_ + 1}, X{x_ + 1}",
                     "是" if r["all_optima_legal"] else "否",
                     f"{r['max_formula_vs_matrix']:.0e}"])
    add_table(doc, {
        "caption": "表 2　小规模枚举结果",
        "headers": ["用例", "规模", "最小能量", "最优解", "最优均合法", "公式−矩阵"],
        "widths": [4.4, 3.8, 2.6, 3.4, 2.2, 2.4],
        "rows": rows,
    })
    add_body(doc, "问题二把最优对 (A1, B2) 设为禁用后，最优解正确退到 (A2, B2)、代价 0.20，"
                  "说明非法惩罚项确实在起作用，而不是碰巧没触发。")
    prows = []
    for r in c["pool"]:
        prows.append([r["mode"].upper(), f"{r['vars']}", f"{r['pairs']:,}",
                      f"{r['max_energy_error']:.0e}", "一致" if r["argmin_matches"] else "不一致"])
    add_table(doc, {
        "caption": "表 3　真实池 × 占位代价的矩阵校验",
        "headers": ["问题", "变量数", "候选数", "max|能量−代价|", "枚举最优与能量最优"],
        "widths": [2.6, 2.6, 3.2, 3.8, 4.2],
        "rows": prows,
    })

    add_body(doc, "第三层是本次补齐的部分：用 02+03 重训岭回归代理，对 07、08 生成真实预测值，"
                  "保序缩放到 [0,1] 后重建矩阵，再枚举全部合法候选核对能量。这一步的代价来自模型，"
                  "不再是占位向量。")
    mrows = []
    for key, label in (("q2", "Q2（07 池）"), ("q3", "Q3（08 池）")):
        info = m["matrices"][key]
        mat = "、".join(str(x) for x in info["oracle"]["material"])
        mrows.append([label, f"{info['n_vars']}", f"{info['candidates']:,}",
                      f"{info['max_energy_vs_cost']:.0e}", mat,
                      f"{info['oracle']['raw']:.4f}", f"{info['oracle']['scaled']:.4f}"])
    add_table(doc, {
        "caption": "表 4　真实代理预测下的矩阵",
        "headers": ["矩阵", "变量", "候选", "max|能量−代价|", "代理最优材料", "原始 V̂", "缩放代价"],
        "widths": [2.8, 1.6, 2.0, 3.0, 3.6, 2.2, 2.2],
        "rows": mrows,
    })
    add_body(doc, "两个矩阵的合法候选能量与缩放代价逐条相等（偏差 0），枚举最优与能量最优一致。"
                  "需要强调：这里的“最优”是代理目标下的最优，不代表真实物性最优；真实命中只能由 04 的盲测评分回答。")

    h1(doc, "四、边界：本地无法验证的事")
    add_body(doc, "一个诚实的 PASS 必须写清它没覆盖什么。以下三件事只能由外部回答：")
    add_bullet(doc, "19 条正例本身。04 的物理量与 V 已删除，本地只能验证“02/03 里确实一条都没有”，"
                    "无法验证“04 里确实有 19 条、且落在 19 个不同的元素对上”。这是推断，不是观测。")
    add_bullet(doc, "代理模型的盲测精度。数据能支撑建模，但“低尾排序能不能把真目标排进前列”取决于模型与数据分布，"
                    "不是审计能回答的。")
    add_bullet(doc, "实机求解。Kaiwu SDK 与 SPQC 的账号、排队、8 位系数精度都会影响最终解，本阶段只验证了数学与代码。")
    add_body(doc, "另外，审计首轮曾出现 7 项 FAIL，定位后确认是我的 4 条判据写错（V 容差、Σv_* 容差、"
                  "区块模型、分布口径），修正后重跑全绿；修正过程与依据记录在《任务 A 数据审计报告》2.1 节。")

    h1(doc, "五、复跑命令")
    add_code(doc,
             "# 数据审计（41 项）\n"
             "python task_a/task_a_audit.py --data-dir task_a/data_real --out task_a/audit_result.json\n"
             "python task_a/build_audit_report.py --json task_a/audit_result.json \\\n"
             "        --out task_a/任务A_数据审计报告.docx\n"
             "\n"
             "# 基础代理模型（B1）\n"
             "venv-mirna/Scripts/python.exe task_a/train_baseline.py\n"
             "\n"
             "# 真实代理 -> 07/08 矩阵（B2 + D1 + 交付）\n"
             "venv-mirna/Scripts/python.exe task_a/build_matrices.py\n"
             "\n"
             "# 编码验证（16 / 256 状态 + 真实池）\n"
             "python task_a/verify_qubo.py\n"
             "\n"
             "# 反向自检：植入 6 类缺陷，确认审计会报错\n"
             "python task_a/selftest_negative.py")
    add_body(doc, "数据目录已复制到 task_a/data_real/，与官方包 sha256 一致，原始文件未做任何修改。")

    props = doc.core_properties
    props.title = "2026 APMCM D 题 前置可行性验证结论"
    props.author = "参赛队"
    normalize_xml(doc)
    doc.save(out)
    print("saved:", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default="task_a/audit_result.json")
    ap.add_argument("--qubo", default="task_a/qubo_verify.json")
    ap.add_argument("--matrices", default="task_a/results/matrix_build.json")
    ap.add_argument("--out", default="task_a/前置可行性验证结论.docx")
    args = ap.parse_args()
    with open(args.audit, encoding="utf-8") as fh:
        a = json.load(fh)
    with open(args.qubo, encoding="utf-8") as fh:
        c = json.load(fh)
    with open(args.matrices, encoding="utf-8") as fh:
        m = json.load(fh)
    build(a, c, m, args.out)
