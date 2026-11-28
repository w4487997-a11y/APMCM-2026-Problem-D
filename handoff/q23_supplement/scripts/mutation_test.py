# -*- coding: utf-8 -*-
"""变异测试：验证一致性测试能否拦截两类真实错误。

变异 1a：把 O15/README 中 Q2 与 Q3-O3 的“完整流水线”耗时互换 → 必须 FAIL
变异 1b：把顶层 README 摘要表中 Q2 与 Q3-O3 的流水线耗时互换 → 必须 FAIL
变异 2 ：把 mcc_summary.csv 中一条退火预算记录的 samples 置空 → 必须 FAIL

每个变异都在内存中备份原文件，跑完立即还原；最后再跑一次基线确认恢复成功。
日志：results/mutation_test.log
退出码：0 = 两个用例均被拦截且基线恢复；1 = 有遗漏
"""

import csv
import io
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "scripts" / "consistency_test.py"
LOG = ROOT / "results" / "mutation_test.log"
O15_README = ROOT / "O15" / "README.md"
TOP_README = ROOT / "README.md"
MCC = ROOT / "O11" / "mcc_summary.csv"


def run_test():
    proc = subprocess.run([sys.executable, str(TEST)], capture_output=True, text=True, cwd=str(ROOT))
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def find_fail(out):
    return [ln for ln in out.splitlines() if ln.startswith("FAIL")]


def mutate_swap_o15():
    """交换 O15/README 中 q2_NO2 与 q3_O3 的流水线耗时。"""
    text = O15_README.read_text(encoding="utf-8")
    pat = re.compile(r"^(\| (?:q2_NO2|q3_O3) \| \*\*完整流水线（构建→转换→适配→自检）\*\* \| )([\d.]+)( ms \| 1 \|)$", re.M)
    hits = list(pat.finditer(text))
    assert len(hits) == 2, f"未找到两行流水线数据（找到 {len(hits)} 行）"
    v2, v3 = hits[0].group(2), hits[1].group(2)
    new = text[:hits[0].start()] + hits[0].group(1) + v3 + hits[0].group(3) \
        + text[hits[0].end():hits[1].start()] + hits[1].group(1) + v2 + hits[1].group(3) \
        + text[hits[1].end():]
    O15_README.write_text(new, encoding="utf-8")
    return f"O15/README 流水线耗时互换：q2_NO2={v2} <-> q3_O3={v3}"


def mutate_swap_top():
    """交换顶层 README 摘要表中 Q2 与 Q3-O3 的流水线耗时单元格。"""
    text = TOP_README.read_text(encoding="utf-8")
    line_re = re.compile(r"^\| \*\*完整流水线（含构建）\*\* \|([^|]+)\|([^|]+)\|", re.M)
    m = line_re.search(text)
    assert m, "顶层 README 未找到流水线行"
    c1, c2 = m.group(1), m.group(2)
    new_line = f"| **完整流水线（含构建）** |{c2}|{c1}|" + text[m.end():m.end() + 0]
    # 保留该行其余部分：仅替换前两个单元格
    rest = text[m.end():].split("\n", 1)[0]
    start = m.start()
    end = text.index("\n", start)
    line = text[start:end]
    parts = line.split("|")
    parts[2], parts[3] = parts[3], parts[2]
    TOP_README.write_text(text[:start] + "|".join(parts) + text[end:], encoding="utf-8")
    return f"顶层 README 摘要互换：{c1.strip()} <-> {c2.strip()}"


def mutate_blank_samples():
    """清空一条退火预算记录的 samples。"""
    rows = list(csv.DictReader(open(MCC, encoding="utf-8-sig")))
    fields = list(rows[0].keys())
    target = next(r for r in rows if r["kind"] == "退火预算扫描")
    old = target["samples"]
    target["samples"] = ""
    with open(MCC, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fields)
        w.writeheader()
        w.writerows(rows)
    return f"预算记录 {target['config']} 的 samples: {old!r} -> ''"


def run_case(label, mutate, expect_fail_keyword, restore):
    print(f"\n=== {label} ===")
    mutate_desc = mutate()
    print("注入:", mutate_desc)
    code, out = run_test()
    fails = find_fail(out)
    hit = [f for f in fails if expect_fail_keyword in f]
    ok = code != 0 and bool(hit)
    print(f"测试退出码={code}，FAIL 行数={len(fails)}，命中预期={bool(hit)}")
    for f in hit[:2]:
        print("   ", f)
    restore()
    return ok, f"{label}｜{mutate_desc}｜退出码 {code}｜命中: {hit[0] if hit else '无'}"


def main():
    lines = []
    # 基线
    code, out = run_test()
    summary = out.strip().splitlines()[-1] if out.strip() else ""
    ok_base = code == 0
    print(f"基线: 退出码={code}, {summary}")
    lines.append(f"基线: 退出码={code}, {summary}")
    if not ok_base:
        print("基线未通过，终止变异测试")
        LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    backups = {
        O15_README: O15_README.read_text(encoding="utf-8"),
        TOP_README: TOP_README.read_text(encoding="utf-8"),
        MCC: MCC.read_text(encoding="utf-8"),
    }

    def restore_all():
        for p, content in backups.items():
            p.write_text(content, encoding="utf-8")

    results = []
    # 用例 1a
    def restore_o15():
        O15_README.write_text(backups[O15_README], encoding="utf-8")

    ok, rec = run_case("变异 1a：互换 O15/README 中 Q2 与 Q3-O3 流水线耗时",
                       mutate_swap_o15, "O15 README 逐行耗时", restore_o15)
    results.append(ok)
    lines.append(rec)

    # 用例 1b
    def restore_top():
        TOP_README.write_text(backups[TOP_README], encoding="utf-8")

    ok, rec = run_case("变异 1b：互换顶层 README 摘要表 Q2 与 Q3-O3 流水线耗时",
                       mutate_swap_top, "顶层 README 摘要与 CSV", restore_top)
    results.append(ok)
    lines.append(rec)

    # 用例 2
    def restore_mcc():
        MCC.write_text(backups[MCC], encoding="utf-8")

    ok, rec = run_case("变异 2：清空一条预算记录的 samples",
                       mutate_blank_samples, "按记录类型校验必填列", restore_mcc)
    results.append(ok)
    lines.append(rec)

    # 还原后基线
    restore_all()
    code, out = run_test()
    summary = out.strip().splitlines()[-1]
    ok_restore = code == 0
    print(f"\n还原后基线: 退出码={code}, {summary}")
    lines.append(f"还原后基线: 退出码={code}, {summary}")

    all_ok = all(results) and ok_restore
    lines.append("")
    lines.append(f"结论: {'PASS（两个回归用例均拦截成功，且文件已还原）' if all_ok else 'FAIL'}")
    text = "\n".join(lines)
    print("\n" + text)
    LOG.write_text(text + "\n", encoding="utf-8")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
