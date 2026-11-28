# -*- coding: utf-8 -*-
"""O-13 前置材料：最终 104 变量整数矩阵的真机提交包。

产出 q23_supplement/O13/：
  matrices/*.csv / *_meta.json    平台上传矩阵 + 变量映射/期望值/哈希
  upload_steps.md                 上传指引与预期结果
  decode_platform.py              平台日志解码（从 scripts/ 复制）
  receipt_template.csv            回执采集模板
  o13_manifest.json               文件哈希
"""

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT.parent / "q23_fix"
sys.path.insert(0, str(FIX / "scripts"))
import common as C
import stage7_entry as S7

OUT = ROOT / "O13"
MAT = OUT / "matrices"
MAT.mkdir(parents=True, exist_ok=True)
(OUT / "receipts").mkdir(exist_ok=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def export_model(model, tag):
    q, offset = model["q"], model["offset"]
    raw = model["raw"]
    i, j = model["i"], model["j"]
    M = S7.ising_matrix(q, offset)[0]
    audit = S7.post_adapt_audit(M, model)
    csv_path = MAT / f"{tag}.csv"
    np.savetxt(csv_path, q.astype(np.int64), delimiter=",", fmt="%d")
    enum_best = int(np.argmin(raw))
    legal_energy = q[i, i] + q[j, j] + q[i, j]
    meta = {
        "tag": tag,
        "problem": model["problem"],
        "group": model["group"],
        "variables": int(len(q)),
        "n_candidates": int(len(model["block"])),
        "matrix_type": "QUBO",
        "convention": "H = x^T Q x + offset；上三角；整数系数",
        "offset": float(offset),
        "q_abs_max": float(np.abs(q).max()),
        "var_names": model["names"],
        "left_count": int(model["n_left"]),
        "left_names": model["left"],
        "right_names": model["right"],
        "candidate_ids": [int(r["id"]) for r in model["block"]],
        "candidate_keys": ["|".join(C.key(r)) for r in model["block"]],
        "candidate_raw_scores": [float(r["V_hat"]) for r in model["block"]],
        "enumeration": {
            "best_material": "|".join(C.key(model["block"][enum_best])),
            "best_V_hat": float(raw[enum_best]),
            "best_platform_qubo_value": float(legal_energy[enum_best]),
            "best_total_energy_with_offset": float(legal_energy[enum_best] + offset),
            "second_best_V_hat": float(np.sort(raw)[1]),
            "ties_at_minimum_integer": int(np.sum(legal_energy == legal_energy.min())),
        },
        "ising": {
            "h_max_abs": audit["h_max_abs"],
            "J_max_abs": audit["J_max_abs"],
            "integral": audit["matrix_integral"],
            "fits_8bit": audit["fits_8bit"],
            "illegal_witness_minus_legal": audit["illegal_minus_legal"],
        },
        "matrix_sha256": sha(csv_path),
        "note": "平台只返回 x^TQx（quboValue），比较时需 +offset；"
                f"最优期望 quboValue = {float(legal_energy[enum_best]):.0f}",
    }
    (MAT / f"{tag}_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main():
    rows = {p: C.ranked(C.read_csv(FIX / "data" / "pred" / f"{p}_pool_predictions.csv"))
            for p in ("q2", "q3")}
    metas = [export_model(S7.build_q2(rows["q2"]), "q2_NO2")]
    for x in ("O3", "NO2", "FO2"):
        metas.append(export_model(S7.build_partition(rows["q3"], x), f"q3_{x}"))
    for m in metas:
        print(f"{m['tag']:<8} vars={m['variables']} |q|max={m['q_abs_max']:.0f} "
              f"offset={m['offset']:.0f} |h|={m['ising']['h_max_abs']:.0f} "
              f"witness={m['ising']['illegal_witness_minus_legal']:+.0f} "
              f"best={m['enumeration']['best_material']} "
              f"quboValue={m['enumeration']['best_platform_qubo_value']:.0f}")

    shutil.copy2(Path(__file__).resolve().parent / "decode_platform.py", OUT / "decode_platform.py")

    steps = """# O-13 上传指引（最终 104 变量整数矩阵）

> 本机无平台账号权限，以下步骤需在 https://platform.qboson.com 控制台完成。
> 4 个任务，每题消耗 1 次优化额度。

## 一、准备

1. 控制台 → 机型选 **SPQC-550**（额度在这台）。
2. 确认 OPTIMIZATION CREDITS ≥ 4。
3. 矩阵在 `O13/matrices/`：`q2_NO2.csv`、`q3_O3.csv`、`q3_NO2.csv`、`q3_FO2.csv`
   （104×104，无表头，整数，系数 ∈ {−2, 0, 4}）。

## 二、逐个提交

对每个文件：

1. 新建任务 → 任务名 `o13_q2NO2` / `o13_q3O3` / `o13_q3NO2` / `o13_q3FO2`
2. 矩阵类型 **QUBO**
3. 上传对应 CSV
4. 下一步 → 确认机型 SPQC-550 → 提交
5. 记录任务 ID、创建/结束时间、单次演化时长、额度扣减
6. 任务详情页点 **下载**，导出原始返回为 `O13/receipts/<任务名>.log`

## 三、预期结果

| 任务 | 枚举最优 | 期望平台 quboValue | 说明 |
|---|---|---:|---|
| q2_NO2 | Y–Ti–NO2 | **-4** | +offset(4) 后为 0，等于缩放代价 |
| q3_O3 | Na–Nb–O3 | **-4** | 同上 |
| q3_NO2 | Y–Ti–NO2 | **-4** | 同上 |
| q3_FO2 | Na–Ti–FO2 | **-4** | 同上 |

- 非法态（只选一个位）的 quboValue = **-2**，高于最优，可作为罚项生效的旁证。
- 若返回 quboValue < -4，说明适配或上传有误，请把日志发回。
- 单组内最优与次优可能同档（代价都为 0 的候选极少，通常唯一），以解码结果为准。

## 四、拿到回执后

```bash
python O13/decode_platform.py \\
    --meta O13/matrices/q2_NO2_meta.json --log O13/receipts/o13_q2NO2.log
```

输出候选、合法性、V_hat、与枚举对照、命中与否。
把 `receipt_template.csv` 填好后，即可合并出 O-13 最终交付表（排队/执行/总耗时/额度）。
"""
    (OUT / "upload_steps.md").write_text(steps, encoding="utf-8")

    with open(OUT / "receipt_template.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["task_name", "task_id", "device", "matrix_file", "matrix_sha256",
                    "created", "finished", "queue_seconds", "exec_seconds",
                    "total_seconds", "evolve_ms", "credits_used",
                    "samples_returned", "legal_samples", "best_material", "best_qubo_value"])
        for m in metas:
            w.writerow([f"o13_{m['tag']}", "", "SPQC-550", f"{m['tag']}.csv",
                        m["matrix_sha256"], "", "", "", "", "", "", 1, "", "", "", ""])

    manifest = {}
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name != "o13_manifest.json" and "_selftest" not in p.name:
            manifest[p.relative_to(OUT).as_posix()] = sha(p)
    (OUT / "o13_manifest.json").write_text(
        json.dumps({"files": manifest}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("写出", OUT, "文件数", len(manifest))


if __name__ == "__main__":
    main()
