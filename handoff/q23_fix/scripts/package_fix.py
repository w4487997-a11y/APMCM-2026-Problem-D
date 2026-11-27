# -*- coding: utf-8 -*-
"""打包补做交付：脚本、结果、矩阵、日志、一页说明；附 SHA256 清单。"""

import hashlib
import json
import os
import zipfile
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # q23_fix
HERE = os.path.dirname(os.path.abspath(__file__))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    # 记录安装的 wheel
    wheels_dir = os.path.join(os.path.dirname(ROOT), "q23_fix", "wheels")
    wheels = sorted(os.listdir(wheels_dir)) if os.path.isdir(wheels_dir) else []
    lines = ["包名\t大小\tSHA256"]
    for w in wheels:
        p = os.path.join(wheels_dir, w)
        lines.append(f"{w}\t{os.path.getsize(p)}\t{sha(p)}")
    with open(os.path.join(ROOT, "logs", "wheels.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    include_dirs = ["scripts", "results", "matrices", "logs", "data"]
    include_files = ["ONE_PAGE.md", "REVIEW_RESPONSE.md", "RECHECK_RESPONSE.md"]
    manifest = {}
    for f in include_files:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            manifest[f] = sha(p)
    for d in include_dirs:
        base = os.path.join(ROOT, d)
        for root, _, files in os.walk(base):
            if "__pycache__" in root:
                continue
            for f in sorted(files):
                p = os.path.join(root, f)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                manifest[rel] = sha(p)

    with open(os.path.join(ROOT, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump({"generated_at": datetime.now().isoformat(timespec="seconds"),
                   "note": "Kaiwu SDK 安装目录 sdk_pkgs/ 与 wheels/ 不在包内，见 logs/wheels.txt",
                   "files": manifest}, fh, ensure_ascii=False, indent=2)

    zpath = os.path.join(ROOT, "Q23_补做交付_v3.zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(manifest):
            z.write(os.path.join(ROOT, rel), os.path.join("q23_fix", rel))
        z.write(os.path.join(ROOT, "MANIFEST.json"), "q23_fix/MANIFEST.json")
    print("zip:", zpath, os.path.getsize(zpath), "bytes,", len(manifest), "files")
    for rel in sorted(manifest):
        print("  ", rel)


if __name__ == "__main__":
    main()
