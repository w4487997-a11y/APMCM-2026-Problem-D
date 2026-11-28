# -*- coding: utf-8 -*-
"""处理 O-13 平台日志：匹配矩阵、解码、汇总（含历史 17/30 变量任务）。

任务映射（由矩阵重算 quboValue 与文件名共同确定）：
  q2_NO2.csv_01 -> q2_NO2（104 变量）
  22222         -> q3_O3
  333333        -> q3_NO2（与 q2_NO2 矩阵字节相同，按文件名区分）
  444444        -> q3_FO2
  q2_int_01(1)  -> 历史 17 变量短名单
  q3_int_01(1)  -> 历史 30 变量短名单
"""

import csv
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT.parent / "q23_fix"
OUT = ROOT / "O13"
REC, RES = OUT / "receipts", OUT / "results"
for d in (REC, RES):
    d.mkdir(parents=True, exist_ok=True)

TMP = Path(r"C:\Users\wuyik\AppData\Local\Temp")
NEW = [("q2_NO2", TMP / "q2_NO2.csv_01.log", "q2_NO2"),
       ("q3_O3", TMP / "22222_01.log", "q3_O3"),
       ("q3_NO2", TMP / "333333_01.log", "q3_NO2"),
       ("q3_FO2", TMP / "444444_01.log", "q3_FO2")]
HIST = [("hist_q2_int_01", TMP / "q2_int_01 (1).log", "q2"),
        ("hist_q3_int_01", TMP / "q3_int_01 (1).log", "q3")]

MATS = {t: (OUT / "matrices" / f"{t}.csv", OUT / "matrices" / f"{t}_meta.json")
        for _, _, t in NEW}


def load_log(p):
    data = json.loads(Path(p).read_text(encoding="utf-8"))
    return [(np.array(it["solutionVector"], dtype=int), it.get("quboValue")) for it in data]


def qubo_value(q, vec):
    idx = np.flatnonzero(vec)
    v = sum(int(q[i, i]) for i in idx)
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            v += int(q[idx[a], idx[b]])
    return v


def decode_meta(meta, vec):
    n_left = meta["left_count"]
    left, right, group = meta["left_names"], meta["right_names"], meta["group"]
    ones = np.flatnonzero(vec)
    if len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left:
        material = f"{left[int(ones[0])]}|{right[int(ones[1]) - n_left]}|{group}"
        if material in meta["candidate_keys"]:
            score = meta["candidate_raw_scores"][meta["candidate_keys"].index(material)]
            return True, material, score
    return False, None, None


def hist_setup(problem):
    base = FIX.parent / "q2_project" / "platform_upload"
    if problem == "q2":
        meta = json.loads((base / "qubo_q2_intising_meta.json").read_text(encoding="utf-8"))
        q = np.loadtxt(base / "qubo_q2_intising.csv", delimiter=",", dtype=np.int64)
        A, B = meta["elements_A"], meta["elements_B"]
        return meta, q, A, B, None, ("Y|Ti", 1.4919281724855757)
    meta = json.loads((base / "qubo_q3_intising_meta.json").read_text(encoding="utf-8"))
    q = np.loadtxt(base / "qubo_q3_intising.csv", delimiter=",", dtype=np.int64)
    A, B, X = meta["elements_A"], meta["elements_B"], meta["elements_X"]
    return meta, q, A, B, X, ("Na|Nb|O3", 0.5400229940675169)


def material_scores():
    out = {}
    for prob in ("q2", "q3"):
        rows = C_rows = None
        p = FIX / "data" / "pred" / f"{prob}_pool_predictions.csv"
        with open(p, encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            key = f"{r['A']}|{r['B']}" if prob == "q2" else f"{r['A']}|{r['B']}|{r['X']}"
            out[key] = float(r["V_hat"])
    return out


def main():
    scores = material_scores()
    results, summary = {}, []
    for name, path, tag in NEW:
        if not path.exists():
            print("缺失", path)
            continue
        shutil.copy2(path, REC / f"{name}.log")
        q = np.loadtxt(MATS[tag][0], delimiter=",", dtype=np.int64)
        meta = json.loads(MATS[tag][1].read_text(encoding="utf-8"))
        log = load_log(path)
        diffs = [abs(qubo_value(q, v) - qv) for v, qv in log]
        enum_best = meta["enumeration"]["best_material"]
        enum_v = meta["enumeration"]["best_V_hat"]
        samples, legal_n, hit_n, best_v = [], 0, 0, None
        for sid, (vec, qv) in enumerate(log):
            legal, material, score = decode_meta(meta, vec)
            legal_n += legal
            if legal:
                best_v = score if best_v is None else min(best_v, score)
                hit_n += abs(score - enum_v) < 1e-12
            samples.append({"sample": sid, "n_ones": int(vec.sum()), "legal": bool(legal),
                            "material": material, "V_hat": score,
                            "platform_qubo_value": qv,
                            "recomputed_qubo_value": qubo_value(q, vec)})
        results[name] = {"matrix": tag, "variables": int(len(q)),
                         "matrix_sha256": meta["matrix_sha256"],
                         "match_max_abs_diff": float(max(diffs)),
                         "samples_returned": len(log), "legal_samples": legal_n,
                         "legal_ratio": legal_n / len(log),
                         "hit_samples_true_optimum": hit_n,
                         "sample_hit_ratio": hit_n / len(log),
                         "enumeration_best_material": enum_best,
                         "enumeration_best_V_hat": enum_v,
                         "best_returned_V_hat": best_v,
                         "best_returned_gap": None if best_v is None else best_v - enum_v,
                         "samples": samples}
        summary.append({"task": name, "matrix": tag, "variables": len(q),
                        "samples": len(log), "legal": legal_n,
                        "legal_ratio": round(legal_n / len(log), 4), "hits": hit_n,
                        "sample_hit_ratio": round(hit_n / len(log), 4),
                        "best_returned_V": best_v, "enumeration_V": enum_v})
        print(f"{name:<10} -> {tag:<8} 匹配误差={max(diffs):.0f} 合法 {legal_n}/{len(log)} 命中 {hit_n} V={best_v}")

    for name, path, problem in HIST:
        if not path.exists():
            print("缺失", path)
            continue
        shutil.copy2(path, REC / f"{name}.log")
        meta, q, A, B, X, (best_key, best_v_ref) = hist_setup(problem)
        log = load_log(path)
        n_left = len(A) if problem == "q2" else len(A) * len(X)
        samples, legal_n, hit_n, best_v = [], 0, 0, None
        for sid, (vec, qv) in enumerate(log):
            ones = np.flatnonzero(vec)
            legal = len(ones) == 2 and ones[0] < n_left and ones[1] >= n_left
            material = score = None
            if legal:
                if problem == "q2":
                    material = f"{A[int(ones[0])]}|{B[int(ones[1]) - n_left]}"
                else:
                    u = int(ones[0])
                    material = f"{A[u // len(X)]}|{B[int(ones[1]) - n_left]}|{X[u % len(X)]}"
                score = scores.get(material)
            if legal and score is not None:
                legal_n += 1
                best_v = score if best_v is None else min(best_v, score)
                hit_n += abs(score - best_v_ref) < 1e-12
            samples.append({"sample": sid, "n_ones": int(vec.sum()), "legal": bool(legal),
                            "material": material, "V_hat": score,
                            "platform_qubo_value": qv, "recomputed_qubo_value": qubo_value(q, vec)})
        results[name] = {"matrix": f"{problem}_intising_{len(q)}vars",
                         "variables": int(len(q)),
                         "samples_returned": len(log), "legal_samples": legal_n,
                         "legal_ratio": legal_n / len(log),
                         "hit_samples_true_optimum": hit_n,
                         "sample_hit_ratio": hit_n / len(log),
                         "enumeration_best_material": best_key,
                         "enumeration_best_V_hat": best_v_ref,
                         "best_returned_V_hat": best_v,
                         "best_returned_gap": None if best_v is None else best_v - best_v_ref,
                         "samples": samples}
        summary.append({"task": name, "matrix": f"{problem}_hist", "variables": len(q),
                        "samples": len(log), "legal": legal_n,
                        "legal_ratio": round(legal_n / len(log), 4), "hits": hit_n,
                        "sample_hit_ratio": round(hit_n / len(log), 4),
                        "best_returned_V": best_v, "enumeration_V": best_v_ref})
        print(f"{name:<16} 变量{len(q)} 合法 {legal_n}/{len(log)} 命中 {hit_n} V={best_v}")

    (RES / "o13_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    with open(RES / "o13_summary.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    for name, out in results.items():
        with open(RES / f"samples_{name}.csv", "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, list(out["samples"][0]))
            w.writeheader()
            w.writerows(out["samples"])
    print("写出", RES)


if __name__ == "__main__":
    main()
