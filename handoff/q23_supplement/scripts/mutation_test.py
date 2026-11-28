# -*- coding: utf-8 -*-
"""在临时副本验证一致性检查和文档的重复生成。"""

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "results" / "mutation_test.log"


def run(root, script):
    return subprocess.run([sys.executable, "-B", f"scripts/{script}.py"], cwd=root,
                          capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, "PYTHONUTF8": "1"}, check=False)


def swap_cells(path, prefixes, indices):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    locations = [next(i for i, line in enumerate(lines) if line.startswith(prefix)) for prefix in prefixes]
    first, second = locations
    a, b = lines[first].split("|"), lines[second].split("|")
    old_a, old_b = a[indices[0]], b[indices[1]]
    # 仅互换数值，保留各单元格自身的单位和样式。
    val_a = old_a.strip().strip("*").removesuffix(" ms")
    val_b = old_b.strip().strip("*").removesuffix(" ms")
    assert val_a != val_b, f"待交换的两个耗时相等: {path.name}"
    if first == second:
        a[indices[1]] = old_b.replace(val_b, val_a, 1)
        a[indices[0]] = old_a.replace(val_a, val_b, 1)
        lines[first] = "|".join(a)
    else:
        a[indices[0]] = old_a.replace(val_a, val_b, 1)
        b[indices[1]] = old_b.replace(val_b, val_a, 1)
        lines[first], lines[second] = "|".join(a), "|".join(b)
    path.write_text("".join(lines), encoding="utf-8")


def blank_samples(path):
    with path.open(encoding="utf-8-sig", newline="") as src:
        rows = list(csv.DictReader(src))
    next(row for row in rows if row["kind"] == "退火预算扫描")["samples"] = ""
    with path.open("w", encoding="utf-8-sig", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def change_unit(path):
    text = path.read_text(encoding="utf-8")
    prefix = "| q2_NO2 | **完整流水线（构建→转换→适配→自检）** |"
    line = next(line for line in text.splitlines() if line.startswith(prefix))
    assert " ms |" in line
    path.write_text(text.replace(line, line.replace(" ms |", " s |", 1), 1), encoding="utf-8")


def alter_manifest_file(path):
    path.write_bytes(path.read_bytes() + b"\n")


def run_suite(root):
    baseline = run(root, "consistency_test")
    if baseline.returncode:
        return False, ["基线失败", baseline.stdout, baseline.stderr]
    summary = baseline.stdout.strip().splitlines()[-1]
    messages = [f"基线: {summary}"]
    pipeline = " | **完整流水线（构建→转换→适配→自检）** |"
    summary_row = "| **完整流水线（含构建）** |"
    cases = [
        ("互换 O-15 明细耗时", "O15/README.md",
         lambda p: swap_cells(p, ("| q2_NO2" + pipeline, "| q3_O3" + pipeline), (3, 3)),
         "O15 README 逐行耗时"),
        ("互换总 README 摘要耗时", "README.md",
         lambda p: swap_cells(p, (summary_row, summary_row), (2, 3)),
         "顶层 README 摘要与 CSV"),
        ("清空预算记录的 samples", "O11/mcc_summary.csv", blank_samples, "按记录类型校验必填列"),
        ("将一行耗时的 ms 改为 s", "O15/README.md", change_unit, "O15 README 逐行耗时"),
        ("更改 O-13 清单中的文件内容", "O13/README.md", alter_manifest_file, "O13 清单与文件 SHA-256"),
    ]
    passed = []
    for name, relative, mutate, expected in cases:
        file = root / relative
        backup = file.read_bytes()
        try:
            mutate(file)
            result = run(root, "consistency_test")
            failures = [ln for ln in result.stdout.splitlines() if ln.startswith("FAIL")]
            hit = next((ln for ln in failures if expected in ln), "")
            ok = result.returncode == 1 and bool(hit)
            passed.append(ok)
            messages.append(f"{'PASS' if ok else 'FAIL'} {name} | {hit or result.stderr.strip() or '未命中预期'}")
        finally:
            file.write_bytes(backup)

    doc_paths = [root / name for name in ("README.md", "O15/README.md")]
    original = [path.read_text(encoding="utf-8") for path in doc_paths]
    render1 = run(root, "render_docs")
    first = [path.read_text(encoding="utf-8") for path in doc_paths]
    render2 = run(root, "render_docs")
    second = [path.read_text(encoding="utf-8") for path in doc_paths]
    stable = render1.returncode == render2.returncode == 0 and original == first == second
    messages.append(f"{'PASS' if stable else 'FAIL'} 连续两次文档生成与已提交版本一致")
    baseline = run(root, "consistency_test")
    messages.append(f"还原后基线: {baseline.stdout.strip().splitlines()[-1] if baseline.stdout else baseline.stderr}")
    return all(passed) and stable and baseline.returncode == 0, messages


def main():
    with TemporaryDirectory(prefix="q23_consistency_") as directory:
        copy = Path(directory) / "q23_supplement"
        shutil.copytree(ROOT, copy)
        ok, messages = run_suite(copy)
    text = "\n".join([*messages, f"结论: {'PASS' if ok else 'FAIL'}"]) + "\n"
    print(text, end="")
    LOG.write_text(text, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

