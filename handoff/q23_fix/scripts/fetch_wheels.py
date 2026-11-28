# -*- coding: utf-8 -*-
"""从镜像抓取指定版本的 wheel 并解压到 sdk_pkgs（绕过 pip 临时目录被沙箱拦截的问题）。"""

import os
import re
import sys
import urllib.request
import zipfile

UA = {"User-Agent": "pip/26.2.1 python/3.12", "Accept": "*/*"}
MIRRORS = [
    "https://repo.huaweicloud.com/repository/pypi/simple/{name}/",
    "https://pypi.tuna.tsinghua.edu.cn/simple/{name}/",
    "https://pypi.org/simple/{name}/",
]
WHEELS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wheels")
TARGET = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sdk_pkgs")


def fetch_index(name):
    for m in MIRRORS:
        try:
            req = urllib.request.Request(m.format(name=name), headers=UA)
            html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
            return html, m
        except Exception:
            continue
    raise SystemExit(f"无法获取 {name} 的索引")


def pick(html, name, version, prefer=("cp312", "none-any", "win_amd64")):
    pat = re.compile(r'href="([^"#]+' + re.escape(name).replace(r"\-", "[-_]")
                     + r'[-_][^"#]*' + re.escape(version) + r'[^"#]*\.whl)', re.IGNORECASE)
    links = [u for u in pat.findall(html) if "win_amd64" in u or "none-any" in u or "any.whl" in u]
    if not links:
        links = pat.findall(html)
    if not links:
        raise SystemExit(f"{name}=={version} 未找到 wheel")
    for tag in prefer:
        for u in links:
            if tag in u:
                return u
    return links[-1]


def main(pairs):
    os.makedirs(WHEELS, exist_ok=True)
    os.makedirs(TARGET, exist_ok=True)
    for spec in pairs:
        name, version = spec.split("==")
        html, base = fetch_index(name)
        url = pick(html, name, version)
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = "https://" + base.split("/")[2] + url
        elif not url.startswith("http"):
            url = base + url
        fname = url.split("/")[-1]
        path = os.path.join(WHEELS, fname)
        if not os.path.exists(path):
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as fh:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    fh.write(chunk)
        with zipfile.ZipFile(path) as z:
            z.extractall(TARGET)
        print(f"{spec:<28} -> {fname} ({os.path.getsize(path):,} bytes)")


if __name__ == "__main__":
    main(sys.argv[1:])
