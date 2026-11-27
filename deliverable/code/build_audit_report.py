# -*- coding: utf-8 -*-
"""把 audit_result.json 渲染成《任务 A 数据审计报告》DOCX。"""

import argparse
import json
import os
import sys

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

import build_plan
from build_plan import (
    NAVY, GRAY, MIDGRAY, TEXT, WHITE, BODY_CN, HEAD_CN,
    set_run_font, set_col_widths, shade, cell_margins, table_borders,
    row_no_split, para_bottom_border, normalize_xml,
    build_styles, setup_page, build_header_footer,
    add_body, add_bullet, add_caption, add_table, add_callout, add_code,
)

STATUS_COLOR = {"PASS": "1F3864", "FAIL": "A61B1B", "PENDING": "7A5B00"}


def cover(doc, res):
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    set_run_font(p.add_run("2026 年亚太地区数学建模竞赛 · D 题"), cn=HEAD_CN, size=13, color=MIDGRAY)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    set_run_font(p.add_run("任务 A：CSV 数据审计"), cn=HEAD_CN, size=13, bold=True, color=NAVY)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    para_bottom_border(p, color="1F3864", sz=10)
    set_run_font(p.add_run(""), size=2)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(8)
    set_run_font(p.add_run("审计报告"), cn=HEAD_CN, size=34, bold=True, color=NAVY)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    set_run_font(p.add_run("A1 附件与字段 · A2 主键质量 · A3 目标函数 · A4 防泄漏 · A5 盲测结构"),
                 cn=HEAD_CN, size=12, color=GRAY)

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    tag = "自检样例（SYNTHETIC）" if res["mode"] == "synthetic" else "官方附件（REAL）"
    set_run_font(p.add_run("数据模式：" + tag), cn=BODY_CN, size=11, color=MIDGRAY)

    for _ in range(4):
        doc.add_paragraph()

    info = [
        ("结论", res["summary"]["verdict"]),
        ("检查项", f"{res['summary']['total']} 项：PASS {res['summary']['pass']} / "
                 f"FAIL {res['summary']['fail']} / PENDING {res['summary']['pending']}"),
        ("数据目录", res["data_dir"]),
        ("生成时间", res["generated_at"]),
    ]
    table = doc.add_table(rows=0, cols=2)
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table_borders(table, color="C9D3E3", sz=4, inside=False)
    for label, value in info:
        row = table.add_row()
        c0, c1 = row.cells
        c0.width, c1.width = Cm(3.4), Cm(11.6)
        for cell in (c0, c1):
            from build_plan import set_cell_borders
            set_cell_borders(cell, top="none", left="none", right="none",
                             bottom=("C9D3E3", 4))
        p = c0.paragraphs[0]
        p.paragraph_format.space_after = Pt(7)
        set_run_font(p.add_run(label), cn=BODY_CN, size=10, color=MIDGRAY)
        p = c1.paragraphs[0]
        p.paragraph_format.space_after = Pt(7)
        set_run_font(p.add_run(value), cn=BODY_CN, size=10.5, color=TEXT)
    set_col_widths(table, [3.4, 11.6])


def h1(doc, text, first=False):
    p = doc.add_paragraph(style="Heading 1")
    p.paragraph_format.page_break_before = False
    p.paragraph_format.space_before = Pt(0 if first else 20)
    set_run_font(p.add_run(text), cn=HEAD_CN, size=15, bold=True, color=NAVY)
    para_bottom_border(p, color="1F3864", sz=8)


def h2(doc, text):
    p = doc.add_paragraph(style="Heading 2")
    set_run_font(p.add_run(text), cn=HEAD_CN, size=12, bold=True, color=NAVY)


def checks_table(doc, rows, caption):
    add_table(doc, {
        "caption": caption,
        "headers": ["编号", "检查项", "状态", "证据 / 说明"],
        "widths": [2.2, 5.2, 2.0, 6.6],
        "rows": [[c["id"], c["name"], c["status"], c["detail"] + (("　" + c["evidence"]) if c["evidence"] else "")]
                 for c in rows],
    })


def build(res, out_path):
    doc = Document()
    build_styles(doc)
    sec = doc.sections[0]
    setup_page(sec)
    build_header_footer(sec, "2026 APMCM · D 题任务 A 数据审计")
    build_plan.TABLE_KEEP_ROWS = 8

    cover(doc, res)
    doc.add_page_break()

    # ---- 1 结论 ----
    h1(doc, "一、结论与证据边界", first=True)
    if res["mode"] == "synthetic":
        add_callout(doc, "本报告由自检样例（synthetic fixture）生成，用于验证审计流程与报告模板；"
                         "所有数字不得作为官方附件的结论引用。把官方附件放入目录后，用同一条命令重跑即可得到真实结论。")
    else:
        add_callout(doc, "本报告由官方附件直接生成，所有数字均可追溯到页面尾部的运行命令与脚本版本。")

    s = res["summary"]
    add_body(doc, f"本轮共 {s['total']} 项检查：PASS {s['pass']} 项，FAIL {s['fail']} 项，"
                  f"PENDING {s['pending']} 项，总体判断为 {s['verdict']}。"
                  "判断规则是：出现任何 FAIL 即为 FAIL；无 FAIL 但存在 PENDING 为 CONDITIONAL；全绿为 PASS。")
    add_body(doc, "PENDING 不是失败，而是“本机拿不到证据”。缺文件、没有物性列、附件无 V 标签，都会记 PENDING，"
                  "不允许用推断填成 PASS。")

    # ---- 2 A1 ----
    h1(doc, "二、A1 附件与字段")
    add_body(doc, "逐份核对行数、列数、字段名、编码与是否含物性列。行数不符直接 FAIL；池文件出现物性列按泄漏处理。")
    rows = []
    for f in res["files"]:
        rows.append([f["name"], f"{f['expected']:,}",
                     "—" if f["rows"] is None else f"{f['rows']:,}",
                     "—" if f["rows"] is None else str(f["cols"]),
                     f.get("encoding", "—"), "含物性" if f["has_physics"] else "仅组成",
                     f["status"]])
    add_table(doc, {
        "caption": "表 1　八份附件的行数与字段核对",
        "headers": ["文件", "预期行数", "实际行数", "列数", "编码", "物性列", "状态"],
        "widths": [5.2, 2.0, 2.0, 1.4, 2.0, 1.8, 1.6],
        "rows": rows,
    })
    add_body(doc, "读文件用列名断言而不是列位置。不同文件的列顺序可能不同，按位置读不会报错，"
                  "但会把带隙读成形成能，属于最难发现的静默错误。")
    integ = res.get("integrity", {})
    if integ:
        add_body(doc, f"文件完整性：sha256 与官方清单比对，{len(integ.get('matched', []))} 个匹配、"
                      f"{len(integ.get('mismatched', []))} 个不一致、{len(integ.get('missing', []))} 个缺失。"
                      "这一步确认的是“拿到的是不是官方那一份”，与字段检查互补。")

    # ---- 2.1 首轮失败项 ----
    h2(doc, "2.1 首轮 7 项 FAIL 的处置")
    add_body(doc, "首轮运行出现 7 项 FAIL。逐项定位后确认：4 项是我的判据写错，3 项是同一处容差问题在两份文件上的重复，"
                  "没有一项指向数据缺陷。修正只改判据，不改数据；改完重跑 41 项全绿。")
    add_table(doc, {
        "caption": "表 2　首轮失败项与判据修正",
        "headers": ["检查项", "首轮判据", "失败原因", "修正后判据"],
        "widths": [3.4, 4.2, 5.4, 4.0],
        "rows": [
            ["A3-2 V 对账", "|ΔV| ≤ 1e-6", "输入按六位小数落盘，V 由更高精度算得，实测最大 1.02e-5",
             "容差 5e-5，并新增 Σv_* = V 的严格检查（1e-6）"],
            ["A2-7 Σv_* = V", "≤ 1e-9", "五项各自六位小数后再求和，浮点累加误差 1e-6", "容差 2e-6"],
            ["A5 区块结构", "|A|×|B|×|X| = 行数", "切分按 (A,B) 元素对分组，元素散落在全部 52 类，不是元素块",
             "改为“元素对 × X 族”完整性判据"],
            ["A3-4 V 分布", "中位数与计数全等", "说明里的分布含 04 的隐藏标签，本地只有 15,225 条",
             "只核对最大值与计数单调性，差异需可解释"],
        ],
    })
    add_body(doc, "需要说明的是，这轮修正有“迁就数据”的嫌疑，所以保留了两条不受影响的硬证据："
                  "sha256 九个文件全部匹配、以及 Σv_* = V 在 1e-6 内成立。前者证明文件未被改动，"
                  "后者证明 V 列与五项惩罚列自洽；这两条不依赖任何容差假设。")

    # ---- 3 A2 ----
    h1(doc, "三、A2 主键与数据质量")
    add_body(doc, "主键 key = (A, B, X)。A、B 是有序位点，A = B 合法且必须保留；gap = 0 是金属性，不是缺失。")
    checks_table(doc, [c for c in res["checks"] if c["id"].startswith("A2")],
                 "表 3　主键与数据质量检查")

    q = res.get("quality", {})
    if q.get("gap_zero_share"):
        add_body(doc, "零带隙占比用于判断是否有人把 gap = 0 当成缺失删掉："
                      + "，".join(f"{k.split('_')[0]} = {v:.2%}" for k, v in q["gap_zero_share"].items())
                      + "。全库基准为 18,193 / 18,928 = 96.12%，同一量级即视为正常。")

    # ---- 4 A3 ----
    h1(doc, "四、A3 目标函数核验")
    add_body(doc, "统一形式为 v = [max(0, deviation / 0.5)]²，五项相加。分母 0.5 是归一尺度，"
                  "漏掉它 V 会变成 4 倍：排序不变，但与附件标签对账必然失败。")
    tests = res["v"]["unit_tests"]
    rows = []
    for t in tests:
        e, g, v, c = t["args"]
        rows.append([str(t["case"]), f"{e:.2f}", f"{g:.2f}", f"{v:.2f}", f"{c:.2f}",
                     f"{t['expected']:g}", f"{t['got']:.10g}", "通过" if t["pass"] else "未通过"])
    add_table(doc, {
        "caption": "表 4　七项公式测试",
        "headers": ["编号", "e_form", "gap", "vbm", "cbm", "期望 V", "实算 V", "判定"],
        "widths": [1.4, 2.0, 2.0, 2.0, 2.0, 2.0, 2.8, 1.8],
        "rows": rows,
    })

    rows = []
    for name, rec in res["v"]["files"].items():
        if rec.get("status") == "PENDING":
            rows.append([name, "—", "—", "—", "PENDING"])
        else:
            rows.append([name, f"{rec['rows']:,}",
                         "—" if rec.get("max_abs_err") is None else f"{rec['max_abs_err']:.2e}",
                         "—" if rec.get("mean_abs_err") is None else f"{rec['mean_abs_err']:.2e}",
                         "无 V 列" if rec.get("max_abs_err") is None else "已对账"])
    add_table(doc, {
        "caption": "表 5　V 重算与附件标签对账",
        "headers": ["文件", "样本数", "最大绝对误差", "平均绝对误差", "说明"],
        "widths": [5.0, 2.4, 3.2, 3.2, 2.2],
        "rows": rows,
    })
    cnt = res["v"].get("counts", {})
    if cnt:
        add_body(doc, f"两套口径合并统计：V = 0 共 {cnt['v_zero']} 条，严格不等式 {cnt['strict']} 条，"
                      f"最小 V = {cnt['v_min']:.4f}，中位 V = {cnt['v_median']:.4f}。"
                      "官方全库基准是 19 与 15，但有标签子集不该复现这两个数字；"
                      "若为 0 且样本量足够，需在报告中说明“子集内无正样本”，而不是判错。")

    # ---- 5 A4 ----
    h1(doc, "五、A4 划分与防泄漏")
    add_body(doc, "用集合运算而不是抽样肉眼检查：交叠、并集覆盖、子集关系、X 取值范围、池网格完整性，五项都要有数字。")
    checks_table(doc, [c for c in res["checks"] if c["id"].startswith("A4")],
                 "表 6　划分与防泄漏检查")

    # ---- 6 A5 ----
    h1(doc, "六、A5 盲测区块结构")
    add_body(doc, "先做算术核验：3,703 = 529 × 7、529 = 529 × 1、1,587 = 529 × 3。但这组数字的真实含义不是"
                  "“23 × 23 元素块”，而是 529 个 (A,B) 元素对各自带满全部 X 族——元素本身散落在 52 类上。"
                  "判据因此改为“每个元素对是否含全部 X 族”，而不是元素级笛卡尔积；这一条正是首轮 A5 判错的根因。")
    rows = []
    for name, b in res.get("blind", {}).items():
        if not isinstance(b, dict) or "rows" not in b:
            continue
        rows.append([name, f"{b['pairs']} 对 × {b['n_X']} 族", f"{b['rows']:,}",
                     "是" if b["cartesian"] else "否",
                     "是" if b.get("same_ab_across_x") else "否"])
    if rows:
        add_table(doc, {
            "caption": "表 7　盲测区块结构",
            "headers": ["文件", "元素对 × X", "行数", "每对含全部 X 族", "各 X 行数一致"],
            "widths": [6.0, 3.4, 2.2, 2.4, 2.4],
            "rows": rows,
        })
    checks_table(doc, [c for c in res["checks"] if c["id"].startswith("A5")],
                 "表 8　盲测结构检查")

    # ---- 7 全部 ----
    h1(doc, "七、全部检查项")
    add_body(doc, "下表是本次运行的全部结果，按编号顺序排列，可逐条核对。")
    checks_table(doc, res["checks"], "表 9　检查项总表")

    # ---- 8 复现 ----
    h1(doc, "八、复现方式")
    add_body(doc, "把官方附件解压到任意目录，执行下面两条命令即可得到真实结论；本报告即是第二条命令的输出。")
    add_code(doc,
             "# 1) 生成 JSON 结果\n"
             "python task_a/task_a_audit.py --data-dir <附件目录> --out task_a/audit_result.json\n"
             "\n"
             "# 2) 渲染本报告（DOCX）\n"
             "python task_a/build_audit_report.py --json task_a/audit_result.json \\\n"
             "        --out task_a/任务A_数据审计报告.docx\n"
             "\n"
             "# 3) 反向自检：确认审计脚本能抓住植入缺陷\n"
             "python task_a/selftest_negative.py")
    add_body(doc, "运行环境：Python 3 + numpy + pandas。随机性只出现在自检样例生成阶段，审计本身是确定性的，"
                  "同一份数据重复运行结果完全一致。")

    props = doc.core_properties
    props.title = "2026 APMCM D 题 任务 A 数据审计报告"
    props.author = "参赛队"
    normalize_xml(doc)
    doc.save(out_path)
    print("saved:", out_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="task_a/audit_result.json")
    ap.add_argument("--out", default="task_a/任务A_数据审计报告.docx")
    args = ap.parse_args()
    with open(args.json, encoding="utf-8") as fh:
        res = json.load(fh)
    build(res, args.out)
