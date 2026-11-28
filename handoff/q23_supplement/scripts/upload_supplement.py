# -*- coding: utf-8 -*-
"""把 q23_supplement 按目录结构上传到 GitHub（不放压缩包）。

用法：
    set GITHUB_TOKEN=ghp_xxx
    python upload_supplement.py --dry-run
    python upload_supplement.py
"""

import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # q23_supplement
OWNER, REPO = "w4487997-a11y", "APMCM-2026-Problem-D"
API = "https://api.github.com"
PREFIX = "handoff/q23_supplement"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
SKIP_DIRS = {"__pycache__", ".mplconfig"}


def call(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    headers = {"Authorization": f"Bearer {TOKEN}",
               "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "apmcm-upload"}
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", "replace")[:200]}


def collect():
    files = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.suffix in (".pyc", ".zip") or p.name.startswith("."):
            continue
        if "_selftest" in p.name:
            continue
        files.append(p)
    return files


def main():
    dry = "--dry-run" in sys.argv
    files = collect()
    total = sum(p.stat().st_size for p in files)
    print(f"待上传 {len(files)} 个文件，{total:,} bytes -> {PREFIX}/")
    if dry:
        for p in files:
            print("  ", p.relative_to(ROOT).as_posix(), p.stat().st_size)
        return
    if not TOKEN:
        sys.exit("缺少 GITHUB_TOKEN")
    st, me = call("GET", "/user")
    if st != 200:
        sys.exit(f"令牌无效/已撤销：{st}")
    st, repo = call("GET", f"/repos/{OWNER}/{REPO}")
    if st != 200:
        sys.exit(f"仓库不可读：{st}")
    branch = repo["default_branch"]
    print(f"账号 {me['login']}｜{repo['full_name']}｜{branch}")

    ok = fail = 0
    uploaded = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        api_path = f"{PREFIX}/{rel}"
        qpath = urllib.parse.quote(api_path, safe="/")
        data = p.read_bytes()
        payload = {"message": f"chore(supplement): add {rel}",
                   "content": base64.b64encode(data).decode(),
                   "branch": branch}
        st, head = call("GET", f"/repos/{OWNER}/{REPO}/contents/{qpath}?ref={branch}")
        if st == 200:
            payload["sha"] = head["sha"]
        st, resp = call("PUT", f"/repos/{OWNER}/{REPO}/contents/{qpath}", payload)
        if st in (200, 201):
            ok += 1
            uploaded.append((api_path, hashlib.sha256(data).hexdigest()))
        else:
            fail += 1
            print(f"  ✗ {api_path}: {st} {resp}")
    print(f"上传完成：成功 {ok}，失败 {fail}")

    raw = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{branch}/"
    for api_path, want in uploaded[:3]:
        url = raw + urllib.parse.quote(api_path, safe="/")
        got = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "v"}),
                                     timeout=300).read()
        print(f"回读 {api_path}: {len(got)} bytes 一致={hashlib.sha256(got).hexdigest() == want}")


if __name__ == "__main__":
    main()
