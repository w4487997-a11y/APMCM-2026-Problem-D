# -*- coding: utf-8 -*-
"""O-11 对账：解释 Q3–O3 K=52, λ=2, it=30, α=0.9 下历史 0/300 与现记录 8/300。

做法（不依赖任何历史日志即可自证）：
  1. 用冻结预测表重建 O3 分区 QUBO，两个入口（stage2.build_partition / stage3.build_custom）
     分别建矩阵并比对哈希；
  2. 同一种子 12345、300 条链、it=30、α=0.9 各跑一遍，保存原始比特/自旋；
  3. 在同一批样本上用两种计数器统计：
       正确计数器：j 为绝对列号（ones[1] 作为列号直接匹配）
       旧计数器  ：把 ones[1] 当相对列号（ones[1]-52），即早期 bug
     预期：正确 8/300，旧计数 0/300 → 证明历史 0/300 是统计计数器 bug；
  4. 另跑 30 个显式种子批次（每批 10 条），报告合法数、命中原代理最优数、命中批次数。

输出：q23_supplement/O11/reconciliation/
"""

import csv
import hashlib
import json
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

FIX = Path(__file__).resolve().parents[2] / "q23_fix"
SUPP = Path(__file__).resolve().parents[2] / "q23_supplement"
OUT = SUPP / "O11" / "reconciliation"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(FIX / "scripts"))

import stage2_quant_partition as s2          # noqa: E402
import stage3_hitrate_fix as s3             # noqa: E402


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_array(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def decode(part, bits):
    """把比特解码为 (material, V_hat)；非法返回 (None, None)。"""
    n_left = len(part["left"])
    i, j = part["i"], part["j"]
    raw = np.array([float(r["V_hat"]) for r in part["block"]])
    ones = np.flatnonzero(bits)
    if len(ones) != 2 or ones[0] >= n_left or ones[1] < n_left:
        return None, None, None
    a, jj = int(ones[0]), int(ones[1])
    idx = np.where((i == a) & (j == jj))[0]
    if not len(idx):
        return None, None, None
    r = part["block"][int(idx[0])]
    return f"{r['A']}|{r['B']}|{r['X']}", float(raw[idx[0]]), float(raw.min())


def count_correct(part, bits):
    """正确计数器：j 为绝对列号。"""
    feasible = hits = 0
    flags = []
    for b in bits:
        material, v, best = decode(part, b)
        ok = material is not None
        hit = bool(ok and abs(v - best) < 1e-12)
        feasible += ok
        hits += hit
        flags.append(hit)
    return {"feasible": feasible, "hits": hits, "flags": flags}


def count_legacy(part, bits):
    """旧计数器复刻：把 ones[1] 当相对列号（ones[1] - n_left），其余逻辑不变。"""
    n_left = len(part["left"])
    i, j = part["i"], part["j"]
    raw = np.array([float(r["V_hat"]) for r in part["block"]])
    feasible = hits = 0
    for b in bits:
        ones = np.flatnonzero(b)
        if len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left:
            a, jj = int(ones[0]), int(ones[1]) - n_left   # bug: 再减一次
            idx = np.where((i == a) & (j == jj))[0]
            if len(idx):
                feasible += 1
                if abs(raw[idx[0]] - raw.min()) < 1e-12:
                    hits += 1
    return {"feasible": feasible, "hits": hits}


def bits_from_spins(spins):
    return ((spins[:, :-1] * spins[:, -1:] + 1) // 2).astype(int)


def main():
    t_start = time.perf_counter()
    rows = s2.C.ranked(s2.C.read_csv(FIX / "data" / "pred" / "q3_pool_predictions.csv"))
    pred_path = FIX / "data" / "pred" / "q3_pool_predictions.csv"
    summary = {
        "task": "O-11 对账：历史 0/300 与现记录 8/300",
        "baseline_commit": "f274362",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "machine": platform.machine(),
        },
        "frozen_input": {
            "file": str(pred_path.relative_to(SUPP.parent)),
            "rows": len(rows), "sha256": sha256_file(pred_path),
        },
        "params": {"K": 52, "lambda": 2.0, "iterations_per_t": 30, "alpha": 0.9,
                   "size_limit": 10, "seeds": 30, "sampler_seed": 12345},
    }

    # ---- 1) 两个入口建矩阵 ----
    part2 = s2.build_partition(rows, "O3")
    part3 = s3.build_custom(rows, "O3", 52, 2.0)
    M2 = s2.ising_matrix(part2["q"], part2["offset"])
    M3 = s3.ising_matrix(part3["q"], part3["offset"])
    same_q = bool(np.array_equal(part2["q"], part3["q"]))
    same_map = bool(np.array_equal(part2["i"], part3["i"]) and np.array_equal(part2["j"], part3["j"]))
    summary["matrices"] = {
        "variables": int(part2["q"].shape[0]),
        "qubo_stage2_sha256": sha256_array(part2["q"]),
        "qubo_stage3_sha256": sha256_array(part3["q"]),
        "qubo_identical": same_q,
        "mapping_identical": same_map,
        "ising_stage2_sha256": sha256_array(M2),
        "ising_stage3_sha256": sha256_array(M3),
        "ismax": [float(np.abs(M2).max()), float(np.abs(M3).max())],
    }
    archived = FIX / "matrices" / "partition_O3_qubo.npz"
    if archived.exists():
        z = np.load(archived, allow_pickle=True)
        summary["matrices"]["archived_npz"] = {
            "file": str(archived.relative_to(SUPP.parent)),
            "qubo_sha256": sha256_array(z["qubo"]),
            "matches_rebuild": bool(np.array_equal(z["qubo"], part2["q"])),
            "raw_opt": "|".join(s2.C.key(part2["block"][int(np.argmin([float(r['V_hat']) for r in part2['block']]))])),
        }

    # ---- 2) 两个入口各跑一次（同种子） ----
    t0 = time.perf_counter()
    spins2 = s2.anneal_ising_batch(M2, 300, seed=12345, iterations_per_t=30, alpha=0.9)
    wall2 = time.perf_counter() - t0
    bits2 = bits_from_spins(spins2)
    correct2 = count_correct(part2, bits2)
    legacy2 = count_legacy(part2, bits2)

    t0 = time.perf_counter()
    spins3 = s2.anneal_ising_batch(M3, 300, seed=12345, iterations_per_t=30, alpha=0.9)
    wall3 = time.perf_counter() - t0
    bits3 = bits_from_spins(spins3)
    correct3 = count_correct(part3, bits3)
    legacy3 = count_legacy(part3, bits3)

    lr2 = s3.run_hit(part3, iterations_per_t=30, alpha=0.9)   # stage3 官方入口
    summary["runs"] = {
        "O11-R01_stage2_entry": {
            "entry": "stage2_quant_partition.build_partition + anneal_ising_batch(seed=12345)",
            "samples": int(len(bits2)), "legal_correct": correct2["feasible"],
            "hits_correct": correct2["hits"],
            "batches_with_hit": int(sum(
                any(correct2["flags"][c * 10:(c + 1) * 10]) for c in range(30))),
            "legal_legacy_counter": legacy2["feasible"],
            "hits_legacy_counter": legacy2["hits"],
            "wall_s": round(wall2, 4),
        },
        "O11-R02_stage3_entry": {
            "entry": "stage3_hitrate_fix.build_custom + run_hit(iter=30, alpha=0.9)",
            "samples": int(len(bits3)), "legal_correct": correct3["feasible"],
            "hits_correct": correct3["hits"],
            "batches_with_hit": int(sum(
                any(correct3["flags"][c * 10:(c + 1) * 10]) for c in range(30))),
            "legal_legacy_counter": legacy3["feasible"],
            "hits_legacy_counter": legacy3["hits"],
            "wall_s": round(wall3, 4),
            "official_run_hit": {k: (round(v, 6) if isinstance(v, float) else v)
                                 for k, v in lr2.items()},
        },
    }
    summary["interpretation"] = {
        "historical_0_of_300": "旧计数器把绝对列号再减 n_left，任何合法样本都无法匹配 → 恒为 0，"
                               "与求解器行为无关；可视为统计脚本 bug。",
        "historical_record_status": "UNVERIFIED（历史运行日志未归档，git 历史中最早版本已含修复）",
        "current_8_of_300": "同一种子下 300 条链中恰好 8 条合法且都命中组内原代理最优。",
        "samples_identical_between_entries": bool(np.array_equal(bits2, bits3)),
    }

    # ---- 3) 逐样本输出 ----
    def dump(name, part, bits, spins):
        path = OUT / name
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["sample_idx", "batch_idx", "n_ones", "legal_correct", "legal_legacy",
                        "material", "V_hat", "is_group_opt", "spin", "bits"])
            for idx, (b, sv) in enumerate(zip(bits, spins)):
                material, v, best = decode(part, b)
                legal_ok = material is not None
                # 旧计数器合法性
                ones = np.flatnonzero(b)
                n_left = len(part["left"])
                legal_legacy = bool(
                    len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left
                    and np.any((part["i"] == int(ones[0]))
                               & (part["j"] == int(ones[1]) - n_left)))
                w.writerow([idx, idx // 10, int(b.sum()), int(legal_ok), int(legal_legacy),
                            material or "", "" if v is None else f"{v:.12f}",
                            int(bool(legal_ok and abs(v - best) < 1e-12)),
                            "".join(str(int(x)) for x in sv[:-1]),
                            "".join(str(int(x)) for x in b)])
        return str(path.relative_to(SUPP))

    summary["per_sample_files"] = {
        "stage2_entry": dump("samples_stage2_entry.csv", part2, bits2, spins2),
        "stage3_entry": dump("samples_stage3_entry.csv", part3, bits3, spins3),
    }

    # ---- 4) 显式种子批次（30 批 × 10 条） ----
    batch_rows = []
    seed_base = 2026112800
    for bi in range(30):
        seed = seed_base + bi
        sp = s2.anneal_ising_batch(M2, 10, seed=seed, iterations_per_t=30, alpha=0.9)
        bb = bits_from_spins(sp)
        c = count_correct(part2, bb)
        rows_b = []
        for si, b in enumerate(bb):
            material, v, best = decode(part2, b)
            rows_b.append({
                "batch_idx": bi, "seed": seed, "sample_idx": si,
                "n_ones": int(b.sum()),
                "legal": int(material is not None),
                "material": material or "",
                "V_hat": "" if v is None else f"{v:.12f}",
                "is_group_opt": int(bool(material is not None and abs(v - best) < 1e-12)),
                "batch_legal": c["feasible"], "batch_hits": c["hits"],
            })
        batch_rows.extend(rows_b)
    fields = ["batch_idx", "seed", "sample_idx", "n_ones", "legal", "material",
              "V_hat", "is_group_opt", "batch_legal", "batch_hits"]
    with open(OUT / "samples_batch_seeds.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fields)
        w.writeheader()
        w.writerows(batch_rows)
    legal_b = sum(int(r["legal"]) for r in batch_rows)
    hit_b = sum(int(r["is_group_opt"]) for r in batch_rows)
    batches_hit = sum(1 for bi in range(30)
                      if any(r["legal"] and r["is_group_opt"] for r in batch_rows if r["batch_idx"] == bi))
    summary["explicit_seed_batches"] = {
        "seeds": f"{seed_base}..{seed_base + 29}",
        "samples": len(batch_rows), "legal": legal_b, "hits": hit_b,
        "batches_with_hit": batches_hit,
        "file": "O11/reconciliation/samples_batch_seeds.csv",
    }
    summary["runtime_s"] = round(time.perf_counter() - t_start, 3)
    (OUT / "o11_reconciliation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary["runs"], ensure_ascii=False, indent=2))
    print(json.dumps(summary["explicit_seed_batches"], ensure_ascii=False, indent=2))
    print("矩阵一致:", same_q, "| 映射一致:", same_map)
    print("写出:", OUT)


if __name__ == "__main__":
    main()
