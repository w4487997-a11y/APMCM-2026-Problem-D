# -*- coding: utf-8 -*-
"""交付一致性测试：把复审反复指出的三类错误变成自动化断言。

运行：python scripts/consistency_test.py
输出：逐项 PASS/FAIL，日志写到 q23_supplement/results/consistency_test.log
退出码：0 = 全部通过；1 = 有失败
"""

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = []
LOG_PATH = ROOT / "results" / "consistency_test.log"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def check(name, fn):
    try:
        detail = fn()
        RESULTS.append((True, name, detail))
    except AssertionError as exc:
        RESULTS.append((False, name, str(exc)))
    except Exception as exc:  # 代码级错误也算失败
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
    return f"31 行；预算 6、扫描 18"


def o11_no_none():
    rows = o11_rows()
    bad = []
    for idx, r in enumerate(rows, start=2):
        for k, v in r.items():
            if v is None or v == "None":
                bad.append((idx, k))
    assert not bad, f"存在 None 单元格: {bad[:5]}"
    return "无 None 单元格"


def o11_scan_ties():
    rows = [r for r in o11_rows() if r["kind"] == "K×λ 模型扫描"]
    vals = {r["min_tier_ties"] for r in rows}
    assert vals == {"1"}, f"最低档并列数取值 {vals} != {{'1'}}"
    return f"18 行 min_tier_ties 全为 1"


def o11_dual_metric():
    rows = read_csv(ROOT / "O11" / "sorting_retention.csv")
    picked = [r for r in rows if r["scheme"] in ("qubo_x127/4", "qubo_xfloor")]
    assert len(picked) == 4, f"均匀量化行数 {len(picked)} != 4"
    for r in picked:
        assert r["best_in_min_tier"] == "True", f"{r['problem']}/{r['scheme']} best_in_min_tier 应为 True"
        assert r["argmin_after_id_break"] == "False", f"{r['problem']}/{r['scheme']} 按 ID 决胜不应为第一"
    return "4 行：原最优在最低档=True，ID 决胜第一=False"


def o11_tie_numbers():
    rows = read_csv(ROOT / "O11" / "sorting_retention.csv")
    want = {("q2", "qubo_x127/4"): 6, ("q2", "qubo_xfloor"): 6,
            ("q3", "qubo_x127/4"): 21, ("q3", "qubo_xfloor"): 24}
    got = {(r["problem"], r["scheme"]): int(r["min_tier_ties"]) for r in rows
           if (r["problem"], r["scheme"]) in want}
    assert got == want, f"并列数 {got} != {want}"
    return "Q2 6/6、Q3 21/24 与文档一致"


# ---------- O-14 ----------
O14_MODELS = [("q2", "NO2", "float"), ("q2", "NO2", "integer"),
              ("q3", "O3", "float"), ("q3", "O3", "integer"),
              ("q3", "NO2", "float"), ("q3", "NO2", "integer"),
              ("q3", "FO2", "float"), ("q3", "FO2", "integer")]


def _o14_gap(prob, g, enc):
    z = np.load(ROOT / "O14" / "matrices" / f"{prob}_{g}_{enc}.npz", allow_pickle=True)
    q = z["qubo"]
    off = float(z["offset"])
    i = z["left_idx"].astype(int)
    j = z["right_idx"].astype(int)
    legal = q[i, i] + q[j, j] + q[i, j] + off
    n_left = int(sum(not s.startswith("b:") for s in z["var_names"]))
    illegal = [float(q[a, a] + off) for a in range(n_left)]
    return float(min(illegal) - legal.min())


def o14_gap():
    res = read_json(ROOT / "O14" / "results" / "o14_results.json")
    field = {(p, e["group"], e["encoding"]): e["illegal_min_minus_legal_min"]
             for p, pack in res["problems"].items() for e in pack["models"]}
    bad = []
    for key in O14_MODELS:
        g = _o14_gap(*key)
        if abs(g - 2.0) > 1e-9 or abs(field.get(key, -1) - 2.0) > 1e-9:
            bad.append((key, g, field.get(key)))
    assert not bad, f"能隙异常: {bad[:3]}"
    return "8 组矩阵重算能隙=2，JSON 字段=2"


def o14_samples():
    n_bad = []
    for prob, g, enc in O14_MODELS:
        p = ROOT / "O14" / "results" / f"samples_{prob}_{g}_{enc}.csv"
        rows = read_csv(p)
        if len(rows) != 300 or "spin" not in rows[0] or "bits" not in rows[0]:
            n_bad.append(p.name)
    assert not n_bad, f"逐样本异常: {n_bad[:3]}"
    return "8 份逐样本各 300 条，含 spin/bits"


# ---------- O-15 ----------
def o15_build_calls():
    rows = read_csv(ROOT / "O15" / "timings.csv")
    got = {}
    for r in rows:
        if "完整流水线" in r["stage"]:
            got[r["scope"]] = int(r["build_calls_per_call"])
    want = {"q2_NO2": 1, "q3_O3": 1, "q3_NO2": 1, "q3_FO2": 1, "q3_三组合并(8,112)": 3}
    assert got == want, f"构建次数 {got} != {want}"
    return "单组 1 次、三组合并 3 次（计时区间内）"


def o15_readme_same_data():
    rows = read_csv(ROOT / "O15" / "timings.csv")
    readme = (ROOT / "O15" / "README.md").read_text(encoding="utf-8")
    bad = []
    for r in rows:
        if "完整流水线" in r["stage"]:
            txt = f"{float(r['median_ms']):.3f} ms"
            if txt not in readme:
                bad.append((r["scope"], txt))
    assert not bad, f"README 与 CSV 不一致: {bad[:3]}"
    return "README 流水线数值与 timings.csv 完全一致"


def o15_cost_rows():
    rows = read_csv(ROOT / "O15" / "resource_cost.csv")
    blob = json.dumps(rows, ensure_ascii=False)
    assert "20.81–20.96" in blob, "缺 SDK 20.81–20.96 s"
    assert any(r.get("value") == "7" and "额度" in r.get("item", "") for r in rows), "缺额度扣减 7 次"
    return "含 SDK 20.81–20.96 s 与额度扣减 7 次"


# ---------- O-13 ----------
def o13_manifest():
    man = read_json(ROOT / "O13" / "o13_manifest.json")
    actual = {p.relative_to(ROOT / "O13").as_posix()
              for p in (ROOT / "O13").rglob("*")
              if p.is_file() and p.name != "o13_manifest.json"}
    assert set(man["files"]) == actual, f"清单与实际文件不一致（缺 {len(actual - set(man['files']))}）"
    return f"清单 {len(man['files'])} 个文件与实际一致"


def o13_receipt():
    rows = read_csv(ROOT / "O13" / "receipt_template.csv")
    assert len(rows) == 6, f"回执行数 {len(rows)} != 6"
    new = [r for r in rows if r["matrix_file"].endswith(".csv") and r["matrix_file"].startswith("q")]
    assert len(new) == 4, "新任务行数 != 4"
    for r in new:
        assert r["credits_used"] == "1", f"{r['task_name']} 额度应为实测 1"
    return "6 行回执，4 个新任务额度=1"


def o13_credits():
    ev = read_json(ROOT / "O13" / "results" / "credits_evidence.json")
    assert ev["before"] - ev["after"] == ev["deducted"] == 7, ev
    assert "31 - 24 = 7" in ev["consistency"], ev["consistency"]
    pngs = list((ROOT / "O13" / "evidence").glob("*.png"))
    assert len(pngs) >= 11, f"凭证截图 {len(pngs)} < 11"
    return f"31→24=7，凭证 {len(pngs)} 张"


# ---------- O-10 ----------
def o10_npz():
    z = np.load(ROOT / "O10" / "matrices" / "q3_projection_107.npz", allow_pickle=True)
    need = {"penalized_qubo", "penalized_offset", "ising_matrix", "ising_constant"}
    assert need <= set(z.files), f"缺字段 {need - set(z.files)}"
    return "含惩罚矩阵/偏置/Ising 矩阵"


def o10_samples():
    rows = read_csv(ROOT / "O10" / "results" / "o10_samples.csv")
    assert len(rows) == 300 and "spin" in rows[0], f"样本 {len(rows)} 或缺少 spin"
    return "300 条逐样本含自旋"


def o10_readme():
    txt = (ROOT / "O10" / "README.md").read_text(encoding="utf-8")
    assert "投影目标最优" in txt and "原始预测分最优" in txt, "README 未分开列两个最优"
    return "README 分开列投影最优/原始最优"


def main():
    for name, fn in [
        ("O11 行数与分类（31 行：3+6+18+4）", o11_counts),
        ("O11 无 None 单元格", o11_no_none),
        ("O11 扫描 18 行最低档并列数=1", o11_scan_ties),
        ("O11 双口径（最低档/ID 决胜）", o11_dual_metric),
        ("O11 并列数 6/6/21/24", o11_tie_numbers),
        ("O14 八组能隙重算=2", o14_gap),
        ("O14 逐样本含 spin/bits", o14_samples),
        ("O15 计时区间构建次数 1/1/1/1/3", o15_build_calls),
        ("O15 README 与 CSV 同源", o15_readme_same_data),
        ("O15 成本含 SDK 与额度 7 次", o15_cost_rows),
        ("O13 清单与实际文件一致", o13_manifest),
        ("O13 回执 6 任务、新任务额度=1", o13_receipt),
        ("O13 额度 31→24=7 且有凭证", o13_credits),
        ("O10 含惩罚矩阵/偏置/Ising", o10_npz),
        ("O10 逐样本 300 条", o10_samples),
        ("O10 双最优表述", o10_readme),
    ]:
        check(name, fn)

    lines = []
    ok = 0
    for passed, name, detail in RESULTS:
        lines.append(("PASS  " if passed else "FAIL  ") + f"{name} | {detail}")
        ok += passed
    lines.append("")
    lines.append(f"{ok}/{len(RESULTS)} 项通过")
    text = "\n".join(lines)
    print(text)
    LOG_PATH.write_text(text + "\n", encoding="utf-8")
    print(f"\n日志：{LOG_PATH}")
    sys.exit(0 if ok == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
