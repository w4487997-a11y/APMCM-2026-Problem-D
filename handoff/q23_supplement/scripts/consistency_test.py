# -*- coding: utf-8 -*-
"""一致性测试 v2：新增“按行核对耗时”和“按记录类型校验必填列”。

运行：python scripts/consistency_test.py
日志：results/consistency_test.log
退出码：0 全部通过；1 有失败
"""

import csv
import json
import re
import sys
from hashlib import sha256
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)
LOG_PATH = RESULTS_DIR / "consistency_test.log"
RESULTS = []

def check(name, fn):
    try:
        RESULTS.append((True, name, fn()))
    except AssertionError as exc:
        RESULTS.append((False, name, str(exc)))
    except Exception as exc:
        RESULTS.append((False, name, f"{type(exc).__name__}: {exc}"))


def read_csv(p):
    with open(p, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def read_json(p):
    return json.loads(p.read_text(encoding="utf-8"))


# ---------- O-11 ----------
def o11_rows():
    return read_csv(ROOT / "O11" / "mcc_summary.csv")


def o11_counts():
    rows = o11_rows()
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    assert len(rows) == 31, f"行数 {len(rows)} != 31"
    assert kinds.get("退火预算扫描") == 6, f"预算扫描 {kinds.get('退火预算扫描')} != 6"
    assert kinds.get("K×λ 模型扫描") == 18, f"扫描 {kinds.get('K×λ 模型扫描')} != 18"
    return "31 行；预算 6、扫描 18"


def o11_no_none():
    bad = [(i, k) for i, r in enumerate(o11_rows(), start=2)
           for k, v in r.items() if v is None or v == "None"]
    assert not bad, f"存在 None 单元格: {bad[:5]}"
    return "无 None 单元格"


def o11_scan_ties():
    rows = [r for r in o11_rows() if r["kind"] == "K×λ 模型扫描"]
    vals = {r["min_tier_ties"] for r in rows}
    assert vals == {"1"}, f"最低档并列数取值 {vals}"
    return "18 行 min_tier_ties 全为 1"


def o11_dual_metric():
    rows = read_csv(ROOT / "O11" / "sorting_retention.csv")
    picked = [r for r in rows if r["scheme"] in ("qubo_x127/4", "qubo_xfloor")]
    assert len(picked) == 4, f"均匀量化行数 {len(picked)}"
    for r in picked:
        assert r["best_in_min_tier"] == "True", f"{r['problem']}/{r['scheme']} 最低档=False"
        assert r["argmin_after_id_break"] == "False", f"{r['problem']}/{r['scheme']} ID 决胜=True"
    return "4 行：最低档=True，ID 决胜=False"


def o11_tie_numbers():
    rows = read_csv(ROOT / "O11" / "sorting_retention.csv")
    want = {("q2", "qubo_x127/4"): 6, ("q2", "qubo_xfloor"): 6,
            ("q3", "qubo_x127/4"): 21, ("q3", "qubo_xfloor"): 24}
    got = {(r["problem"], r["scheme"]): int(r["min_tier_ties"]) for r in rows
           if (r["problem"], r["scheme"]) in want}
    assert got == want, f"并列数 {got}"
    return "Q2 6/6、Q3 21/24"


NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


def o11_required_by_type():
    """按记录类型校验必填列：退火预算记录必须有数值型采样/命中字段；
    纯模型扫描行（无求解器采样）允许采样字段留空。"""
    rows = o11_rows()
    for r in rows:
        if r["kind"] == "退火预算扫描":
            for field in ("samples", "legal_samples", "legal_ratio", "hits", "hit_rate"):
                v = (r[field] or "").strip()
                assert v, f"预算记录 {r['config']} 的 {field} 为空"
                assert NUM_RE.match(v), f"预算记录 {r['config']} 的 {field}={v!r} 非数值"
        elif r["kind"] == "K×λ 模型扫描":
            assert (r["min_tier_ties"] or "").strip(), f"扫描行 {r['config']} 缺 min_tier_ties"
            assert (r["samples"] or "").strip() == "", \
                f"扫描行 {r['config']} 的 samples 应留空（纯模型扫描）"
    return "6 条预算记录必填列均为数值；18 条扫描行允许留空且并列数非空"


# ---------- O-14 ----------
O14_MODELS = [("q2", "NO2", "float"), ("q2", "NO2", "integer"),
              ("q3", "O3", "float"), ("q3", "O3", "integer"),
              ("q3", "NO2", "float"), ("q3", "NO2", "integer"),
              ("q3", "FO2", "float"), ("q3", "FO2", "integer")]


def _o14_gap(prob, g, enc):
    z = np.load(ROOT / "O14" / "matrices" / f"{prob}_{g}_{enc}.npz", allow_pickle=True)
    q, off = z["qubo"], float(z["offset"])
    i, j = z["left_idx"].astype(int), z["right_idx"].astype(int)
    legal = q[i, i] + q[j, j] + q[i, j] + off
    n_left = int(sum(not s.startswith("b:") for s in z["var_names"]))
    illegal = [float(q[a, a] + off) for a in range(n_left)]
    return float(min(illegal) - legal.min())


def o14_gap():
    res = read_json(ROOT / "O14" / "results" / "o14_results.json")
    field = {(p, e["group"], e["encoding"]): e["illegal_min_minus_legal_min"]
             for p, pack in res["problems"].items() for e in pack["models"]}
    bad = [(k, _o14_gap(*k), field.get(k)) for k in O14_MODELS
           if abs(_o14_gap(*k) - 2.0) > 1e-9 or abs(field.get(k, -1) - 2.0) > 1e-9]
    assert not bad, f"能隙异常: {bad[:3]}"
    return "8 组重算=2，JSON=2"


def o14_samples():
    bad = []
    for prob, g, enc in O14_MODELS:
        rows = read_csv(ROOT / "O14" / "results" / f"samples_{prob}_{g}_{enc}.csv")
        if len(rows) != 300 or "spin" not in rows[0] or "bits" not in rows[0]:
            bad.append(f"{prob}_{g}_{enc}")
    assert not bad, f"逐样本异常: {bad[:3]}"
    return "8 份各 300 条，含 spin/bits"


# ---------- O-15 ----------
def o15_build_calls():
    rows = read_csv(ROOT / "O15" / "timings.csv")
    got = {r["scope"]: int(r["build_calls_per_call"]) for r in rows if "完整流水线" in r["stage"]}
    want = {"q2_NO2": 1, "q3_O3": 1, "q3_NO2": 1, "q3_FO2": 1, "q3_三组合并(8,112)": 3}
    assert got == want, f"构建次数 {got}"
    return "1/1/1/1/3"


def _timings():
    rows = read_csv(ROOT / "O15" / "timings.csv")
    by = {(r["scope"], r["stage"]): r for r in rows}
    assert len(rows) == len(by), "timings.csv 有重复的范围和阶段"
    return by


def _table_rows(section, headers):
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("*") for c in line.strip("|").split("|")]
        if cells[0] not in headers and not re.fullmatch(r"[-:]+", cells[0]):
            rows.append(cells)
    return rows


def _indexed(rows, key_columns):
    by = {tuple(row[:key_columns]): row[key_columns:] for row in rows}
    assert len(by) == len(rows), "README 表格有重复行"
    return by


def _scope_timing(by, scope, stage_prefix):
    rows = [r for (sc, stage), r in by.items() if sc == scope and stage.startswith(stage_prefix)]
    assert len(rows) <= 1, f"timings.csv 阶段不唯一: {scope} / {stage_prefix}"
    return f"{float(rows[0]['median_ms']):.3f}" if rows else None


def o15_readme_rows():
    """按「模型范围 + 计时阶段」定位 README 行，比较数值、单位与构建次数。"""
    by = _timings()
    text = (ROOT / "O15" / "README.md").read_text(encoding="utf-8")
    section = text.split("## 一、本机实测耗时", 1)[1].split("## 二、", 1)[0]
    actual = _indexed(_table_rows(section, {"范围"}), 2)
    assert actual.keys() == by.keys(), f"计时表的行键不一致: {sorted(actual.keys() ^ by.keys())}"
    for key, row in by.items():
        expected = [f"{float(row['median_ms']):.3f} ms", row["build_calls_per_call"] or "0"]
        assert actual[key] == expected, f"{key}: README {actual[key]} != CSV {expected}"
    return f"逐行核对 {len(actual)} 行，数值、单位和构建次数一致"


def o15_top_readme_rows():
    """顶层 README 摘要表同样要等于 CSV（防止文档手写漂移）。"""
    by = _timings()
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    section = text.split("## 三、O-15 核心结论", 1)[1].split("## 四点五、", 1)[0]
    rows = _indexed(_table_rows(section, {"阶段"}), 1)
    scopes = ("q2_NO2", "q3_O3", "q3_NO2", "q3_FO2", "q3_三组合并(8,112)")
    stages = [
        ("QUBO 构建", "QUBO 构建（预测表已载入）"),
        ("QUBO→Ising", "QUBO→Ising 转换"),
        ("8 位适配", "8 位适配"),
        ("适配后自检", "适配后自检"),
        ("完整流水线（含构建）", "完整流水线"),
        ("精确枚举（逐合法态能量）", "精确枚举"),
    ]
    assert rows.keys() == {(label,) for label, _ in stages}, "顶层摘要计时阶段不一致"
    for label, stage in stages:
        values = [_scope_timing(by, scope, stage) for scope in scopes]
        expected = ["—" if v is None else f"{v} ms" if idx in (0, 4) else v
                    for idx, v in enumerate(values)]
        assert rows[label,] == expected, f"{label}: README {rows[label,]} != CSV {expected}"
    return "摘要表六个阶段与 timings.csv 一致"


def o15_cost_readme():
    by = _timings()
    costs = {row["item"]: row for row in read_csv(ROOT / "O15" / "resource_cost.csv")}
    for (scope, stage), row in by.items():
        item = costs[f"{scope} {stage}"]
        assert item["unit"] == "ms" and float(item["value"]) == round(float(row["median_ms"]), 4), \
            f"成本表耗时不一致: {scope} / {stage}"
    readme = (ROOT / "O15" / "README.md").read_text(encoding="utf-8")
    rows = _table_rows(readme.split("## 三、", 1)[1].split("## 四、", 1)[0], {"项目"})
    scopes = ("q2_NO2", "q3_O3", "q3_NO2", "q3_FO2", "q3_三组合并(8,112)")
    pipeline = [_scope_timing(by, scope, "完整流水线") for scope in scopes]
    enum = [_scope_timing(by, scope, "精确枚举") for scope in (scopes[0], scopes[-1])]
    for prefix, values in (("本机完整流水线", pipeline), ("本机精确枚举", enum)):
        line, = [r[1] for r in rows if r[0].startswith(prefix)]
        assert line.endswith(" ms") and re.findall(r"\d+\.\d+", line) == values, \
            f"README 成本表耗时不一致: {prefix}"
    return f"成本 CSV 的 {len(by)} 行及 README 耗时摘要与实测一致"


def o15_local_sa():
    scopes = (("q2", "NO2"), ("q3", "O3"), ("q3", "NO2"), ("q3", "FO2"))
    rows = read_csv(ROOT / "O15" / "local_sa_timing.csv")
    by = {(r["problem"], r["model"]): f"{float(r['wall_s']):.2f}" for r in rows}
    assert len(rows) == len(by) and set(scopes) <= by.keys(), "本地退火范围有重复或缺失"
    for file, prefix in (("README.md", "本地退火（it=300"), ("O15/README.md", "| 本地退火（it=300")):
        line, = [s for s in (ROOT / file).read_text(encoding="utf-8").splitlines() if s.startswith(prefix)]
        assert re.findall(r"(\d+\.\d+) s\b", line) == [by[scope] for scope in scopes], \
            f"{file} 本地退火耗时与 CSV 不一致"
    return "Q2 与 Q3 本地退火分别按问题和模型核对"


def o15_cost_rows():
    rows = read_csv(ROOT / "O15" / "resource_cost.csv")
    blob = json.dumps(rows, ensure_ascii=False)
    assert "20.81–20.96" in blob, "缺 SDK 20.81–20.96 s"
    assert any(str(r.get("value")) == "7" and "额度" in r.get("item", "") for r in rows), "缺额度扣减 7 次"
    return "含 SDK 与额度 7 次"


# ---------- O-13 ----------
def o15_sa_run_ids():
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


def o13_manifest():
    man = read_json(ROOT / "O13" / "o13_manifest.json")
    actual = {p.relative_to(ROOT / "O13").as_posix()
              for p in (ROOT / "O13").rglob("*")
              if p.is_file() and p.name != "o13_manifest.json"}
    assert set(man["files"]) == actual, f"清单差 {len(actual - set(man['files']))}"
    for name, entry in man["files"].items():
        content = (ROOT / "O13" / name).read_bytes()
        assert len(content) == entry["bytes"] and sha256(content).hexdigest() == entry["sha256"], \
            f"清单校验失败: {name}"
    return f"清单 {len(man['files'])} 个文件的路径、字节数和 SHA-256 一致"


def o13_receipt():
    rows = read_csv(ROOT / "O13" / "receipt_template.csv")
    assert len(rows) == 6, f"回执 {len(rows)} 行"
    new = [r for r in rows if r["matrix_file"].endswith(".csv") and r["matrix_file"].startswith("q")]
    assert len(new) == 4, "新任务行数 != 4"
    for r in new:
        assert r["credits_used"] == "1", f"{r['task_name']} 额度 {r['credits_used']}"
    return "6 行；4 个新任务额度=1"


def o13_credits():
    ev = read_json(ROOT / "O13" / "results" / "credits_evidence.json")
    assert ev["before"] - ev["after"] == ev["deducted"] == 7, ev
    assert "31 - 24 = 7" in ev["consistency"]
    pngs = list((ROOT / "O13" / "evidence").glob("*.png"))
    assert len(pngs) >= 11, f"凭证 {len(pngs)}"
    return f"31→24=7；凭证 {len(pngs)} 张"


# ---------- O-10 ----------
def o10_npz():
    z = np.load(ROOT / "O10" / "matrices" / "q3_projection_107.npz", allow_pickle=True)
    need = {"penalized_qubo", "penalized_offset", "ising_matrix", "ising_constant"}
    assert need <= set(z.files), f"缺 {need - set(z.files)}"
    return "含惩罚矩阵/偏置/Ising"


def o10_samples():
    rows = read_csv(ROOT / "O10" / "results" / "o10_samples.csv")
    assert len(rows) == 300 and "spin" in rows[0]
    return "300 条含自旋"


def o10_readme():
    txt = (ROOT / "O10" / "README.md").read_text(encoding="utf-8")
    assert "投影目标最优" in txt and "原始预测分最优" in txt
    return "双最优"


def main():
    checks = [
        ("O11 行数与分类（31 行：3+6+18+4）", o11_counts),
        ("O11 无 None 单元格", o11_no_none),
        ("O11 扫描 18 行最低档并列数=1", o11_scan_ties),
        ("O11 双口径（最低档/ID 决胜）", o11_dual_metric),
        ("O11 并列数 6/6/21/24", o11_tie_numbers),
        ("O11 按记录类型校验必填列", o11_required_by_type),
        ("O14 八组能隙重算=2", o14_gap),
        ("O14 逐样本含 spin/bits", o14_samples),
        ("O15 计时区间构建次数 1/1/1/1/3", o15_build_calls),
        ("O15 README 逐行耗时与构建次数", o15_readme_rows),
        ("O15 顶层 README 摘要与 CSV 一致", o15_top_readme_rows),
        ("O15 成本表逐项核对", o15_cost_readme),
        ("O15 本地退火按问题与模型核对", o15_local_sa),
        ("O15 成本含 SDK 与额度 7 次", o15_cost_rows),
        ("O13 清单与文件 SHA-256 一致", o13_manifest),
        ("O13 回执 6 任务、新任务额度=1", o13_receipt),
        ("O13 额度 31→24=7 且有凭证", o13_credits),
        ("O10 含惩罚矩阵/偏置/Ising", o10_npz),
        ("O10 逐样本 300 条", o10_samples),
        ("O15 本地退火运行 ID 与未舍入合计", o15_sa_run_ids),
        ("O11 历史 0/300 对账", o11_reconciliation),
        ("P0-05 对账表完整", reconciliation_table),
        ("O10 双最优表述", o10_readme),
    ]
    for name, fn in checks:
        check(name, fn)
    lines, ok = [], 0
    for passed, name, detail in RESULTS:
        lines.append(("PASS  " if passed else "FAIL  ") + f"{name} | {detail}")
        ok += passed
    lines += ["", f"{ok}/{len(RESULTS)} 项通过"]
    text = "\n".join(lines)
    print(text)
    LOG_PATH.write_text(text + "\n", encoding="utf-8")
    sys.exit(0 if ok == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
