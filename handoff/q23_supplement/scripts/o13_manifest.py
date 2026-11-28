# -*- coding: utf-8 -*-
"""重新生成 O13/o13_manifest.json（覆盖全部文件，含凭证截图与结果）。

用法：python scripts/o13_manifest.py
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

O13 = Path(__file__).resolve().parents[1] / "O13"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    files = {}
    for p in sorted(O13.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(O13).as_posix()
        if rel == "o13_manifest.json":
            continue
        files[rel] = {"sha256": sha(p), "bytes": p.stat().st_size}
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "note": "O-13 真机验证：矩阵、凭证截图、平台原始回执、逐样本解码与汇总",
        "tasks": {
            "c249dca66bcd4c55a49114a37f4ebf2a": "q2_NO2.csv_01",
            "27a3df4616c74fa6ac87287f2dc1a59f": "22222_01 (q3_O3)",
            "1e00e1fb34dc4a21ba1ee0520c9477d2": "333333_01 (q3_NO2)",
            "c528ea69a2094bc79ac4920f4e99ee8d": "444444_01 (q3_FO2)",
            "76ac237a1e124cb29a064a022f8c4e98": "q2_int_01 (历史 17 变量)",
            "7ab4ca3648d24cb3823668cc92f92869": "q3_int_01 (历史 30 变量)",
        },
        "files": files,
    }
    (O13 / "o13_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写出 O13/o13_manifest.json，{len(files)} 个文件")


if __name__ == "__main__":
    main()
