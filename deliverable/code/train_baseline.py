# -*- coding: utf-8 -*-
"""任务 2：基础代理模型（V0.4 的 B1）。

只做流程验证：
  Baseline 0 —— 训练集 V 的中位数；
  Baseline 1 —— 独热(A,B,X) + 岭回归；
  Baseline 2 —— 独热(A,B,X) + 随机森林。
输入只有 A、B、X，02 训练、03 验证，随机种子固定。
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

SEED = 42
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data_real")
RES = os.path.join(HERE, "results")


def load(name):
    return pd.read_csv(os.path.join(DATA, name), encoding="utf-8-sig")


def build_features(train, others):
    """按训练集元素表构造独热，保证各表列一致。"""
    elems = sorted(set(train["A"]) | set(train["B"]))
    xs = sorted(train["X"].unique())
    cols = ([f"A:{e}" for e in elems] + [f"B:{e}" for e in elems] + [f"X:{x}" for x in xs])

    def encode(df):
        m = np.zeros((len(df), len(cols)), dtype=np.float32)
        ai = {e: i for i, e in enumerate(elems)}
        xi = {x: i + 2 * len(elems) for i, x in enumerate(xs)}
        m[np.arange(len(df)), df["A"].map(ai).to_numpy()] = 1.0
        m[np.arange(len(df)), df["B"].map(ai).to_numpy() + len(elems)] = 1.0
        m[np.arange(len(df)), df["X"].map(xi).to_numpy()] = 1.0
        return m

    return encode(train), [encode(d) for d in others], cols, elems, xs


def metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    err = np.abs(y_true - y_pred)
    low_cut = np.quantile(y_true, 0.10)
    low_mask = y_true <= low_cut
    return {
        "MAE": round(float(err.mean()), 6),
        "RMSE": round(float(np.sqrt(((y_true - y_pred) ** 2).mean())), 6),
        "Low10_MAE": round(float(err[low_mask].mean()), 6),
        "n_val": int(len(y_true)),
        "n_low10": int(low_mask.sum()),
        "low10_threshold": round(float(low_cut), 6),
    }


def top_overlap(y_true, y_pred, ids, k=25):
    order_true = np.lexsort((ids, y_true))[:k]
    order_pred = np.lexsort((ids, y_pred))[:k]
    inter = len(set(order_true.tolist()) & set(order_pred.tolist()))
    return inter / k, inter


def main():
    os.makedirs(RES, exist_ok=True)
    tr, va = load("02_castelli_train.csv"), load("03_castelli_val.csv")

    Xtr, (Xva,), cols, elems, xs = build_features(tr, [va])
    ytr, yva = tr["V"].to_numpy(float), va["V"].to_numpy(float)
    ids_va = va["id"].to_numpy()
    print(f"train {Xtr.shape}, val {Xva.shape}, feats {len(cols)}")

    out = {"seed": SEED, "features": "one-hot(A,B,X)", "n_features": len(cols),
           "train_rows": int(len(tr)), "val_rows": int(len(va)),
           "models": {}, "quantiles": {}}

    # Baseline 0
    med = float(np.median(ytr))
    p0 = np.full_like(yva, med)
    m0 = metrics(yva, p0)
    ov0, i0 = top_overlap(yva, p0, ids_va)
    m0.update({"Top25_overlap": ov0, "Top25_intersection": i0, "const": round(med, 6)})
    out["models"]["baseline0_median"] = m0

    # Baseline 1: Ridge
    ridge = Ridge(alpha=1.0, random_state=None)
    ridge.fit(Xtr, ytr)
    p1 = ridge.predict(Xva)
    m1 = metrics(yva, p1)
    ov1, i1 = top_overlap(yva, p1, ids_va)
    m1.update({"Top25_overlap": ov1, "Top25_intersection": i1})
    out["models"]["baseline1_ridge"] = m1

    # Baseline 2: RandomForest
    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                               random_state=SEED, n_jobs=1)
    rf.fit(Xtr, ytr)
    p2 = rf.predict(Xva)
    m2 = metrics(yva, p2)
    ov2, i2 = top_overlap(yva, p2, ids_va)
    m2.update({"Top25_overlap": ov2, "Top25_intersection": i2})
    out["models"]["baseline2_rf"] = m2

    # 分位数
    for name, df in (("02", tr), ("03", va)):
        v = df["V"].to_numpy(float)
        out["quantiles"][name] = {
            "n": int(len(v)), "min": float(v.min()),
            "q01": float(np.quantile(v, 0.01)),
            "q05": float(np.quantile(v, 0.05)),
            "median": float(np.median(v)), "max": float(v.max()),
        }

    # 预测结果
    pred = pd.DataFrame({"id": ids_va, "V_true": yva,
                         "pred_median": p0, "pred_ridge": p1, "pred_rf": p2})
    pred.to_csv(os.path.join(RES, "baseline_val_predictions.csv"), index=False,
                encoding="utf-8-sig")
    with open(os.path.join(RES, "baseline_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    for k, v in out["models"].items():
        print(f"{k:18s} MAE={v['MAE']:.4f} RMSE={v['RMSE']:.4f} "
              f"Low10={v['Low10_MAE']:.4f} Top25={v['Top25_overlap']:.2f}")
    for k, v in out["quantiles"].items():
        print(f"V {k}: min={v['min']:.6f} q1%={v['q01']:.4f} q5%={v['q05']:.4f} "
              f"median={v['median']:.4f} max={v['max']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
