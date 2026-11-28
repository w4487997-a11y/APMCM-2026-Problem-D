# -*- coding: utf-8 -*-
"""解码平台返回（O-13）。

用法：
    python decode_platform.py --meta matrices/q2_NO2_meta.json --log receipts/o13_q2NO2.log

日志格式：平台导出的 JSON 数组 [{"result":0,"quboValue":-4,"solutionVector":[...]}, ...]，
或纯 0/1 文本序列。
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np


def load(path):
    text = Path(path).read_text(encoding="utf-8").strip()
    if text.startswith("["):
        data = json.loads(text)
        return [(np.array(it["solutionVector"], dtype=int), it.get("quboValue")) for it in data]
    nums = [int(x) for x in re.findall(r"(?<![0-9.])[01](?![0-9.])", text)]
    return [(np.array(nums, dtype=int), None)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    meta = json.loads(Path(a.meta).read_text(encoding="utf-8"))
    n_left = meta["left_count"]
    left = meta["left_names"]
    right = meta["right_names"]
    group = meta["group"]
    scores = meta["candidate_raw_scores"]
    keys = meta["candidate_keys"]
    best_v = meta["enumeration"]["best_V_hat"]
    best_key = meta["enumeration"]["best_material"]
    offset = meta["offset"]

    rows = []
    for sid, (vec, qv) in enumerate(load(a.log)):
        ones = np.flatnonzero(vec)
        legal = len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left
        material = score = None
        if legal:
            material = f"{left[int(ones[0])]}|{right[int(ones[1]) - n_left]}|{group}"
            if material in keys:
                score = scores[keys.index(material)]
        rows.append((sid, int(vec.sum()), legal, qv, material, score))

    legal_rows = [r for r in rows if r[2]]
    print(f"样本 {len(rows)}｜合法 {len(legal_rows)}｜枚举最优 {best_key} "
          f"V_hat={best_v:.6f}｜offset={offset:.0f}")
    for sid, ones, legal, qv, material, score in rows:
        total = None if qv is None else qv + offset
        gap = None if score is None else score - best_v
        print(f"  #{sid:<2} ones={ones} legal={legal} quboValue={qv} "
              f"total={total} {material or '-'} "
              f"V_hat={None if score is None else round(score, 6)} "
              f"gap={None if gap is None else round(gap, 6)}")
    scored = [r for r in legal_rows if r[5] is not None]
    if scored:
        best = min(scored, key=lambda r: r[5])
        print(f"返回最优：{best[4]} V_hat={best[5]:.6f} "
              f"与枚举差 {best[5] - best_v:+.6f} 命中={abs(best[5] - best_v) < 1e-12}")


if __name__ == "__main__":
    main()
