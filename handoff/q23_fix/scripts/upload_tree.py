# -*- coding: utf-8 -*-
"""把补做交付解压后的文件逐个上传到 GitHub（不放压缩包）。

用法：
    set GITHUB_TOKEN=ghp_xxx
    python upload_tree.py            # 上传
    python upload_tree.py --dry-run  # 只看清单

行为：
  1. 逐个 PUT 到 <repo>/handoff/q23_fix/<相对路径>（内容 base64）；
  2. 删除仓库里旧的 Q23_补做交付_v1.zip（如有），满足“不放压缩包”；
  3. 抽样回读 3 个文件比对 SHA256。
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

HERE = Path(__file__).resolve().parent          # q23_fix/scripts
ROOT = HERE.parent                               # q23_fix
OWNER, REPO = "w4487997-a11y", "APMCM-2026-Problem-D"
API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
TARGET_PREFIX = "handoff/q23_fix"
INCLUDE = ["ONE_PAGE.md", "REVIEW_RESPONSE.md", "MANIFEST.json"]
INCLUDE_DIRS = ["scripts", "results", "matrices", "logs"]
SKIP_SUFFIX = (".pyc",)
SKIP_DIRS = {"__pycache__", "sdk_pkgs", "wheels"}
TO_DELETE = ["handoff/q23_fix/Q23_补做交付_v1.zip", "handoff/q23_fix/Q23_补做交付_v2.zip"]


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
        return e.code, {"error": e.read().decode("utf-8", "replace")[:300]}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def collect():
    files = []
    for name in INCLUDE:
        p = ROOT / name
        if p.exists():
            files.append(p)
    for d in INCLUDE_DIRS:
        for root, dirs, names in os.walk(ROOT / d):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for n in sorted(names):
                if n.endswith(SKIP_SUFFIX):
                    continue
                files.append(Path(root) / n)
    return files


def main():
    dry = "--dry-run" in sys.argv
    files = collect()
    print(f"待上传 {len(files)} 个文件，目标目录 {TARGET_PREFIX}/")
    total = sum(p.stat().st_size for p in files)
    print(f"总大小 {total:,} bytes")
    if dry:
        for p in files:
            print("  ", p.relative_to(ROOT).as_posix(), p.stat().st_size)
        return
    if not TOKEN:
        sys.exit("缺少 GITHUB_TOKEN")

    st, me = call("GET", "/user")
    if st != 200:
        sys.exit(f"令牌无效：{st} {me}")
    st, repo = call("GET", f"/repos/{OWNER}/{REPO}")
    if st != 200:
        sys.exit(f"仓库不可读：{st}")
    branch = repo["default_branch"]
    print(f"账号 {me['login']}｜仓库 {repo['full_name']}｜分支 {branch}")

    ok = fail = 0
    uploaded = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        api_path = f"{TARGET_PREFIX}/{rel}"
        qpath = urllib.parse.quote(api_path, safe="/")
        data = p.read_bytes()
        payload = {"message": f"chore(handoff): add {rel}",
                   "content": base64.b64encode(data).decode(),
                   "branch": branch}
        st, head = call("GET", f"/repos/{OWNER}/{REPO}/contents/{qpath}?ref={branch}")
        if st == 200:
            payload["sha"] = head["sha"]
        st, resp = call("PUT", f"/repos/{OWNER}/{REPO}/contents/{qpath}", payload)
        if st in (200, 201):
            ok += 1
            uploaded.append((api_path, sha(p), len(data)))
        else:
            fail += 1
            print(f"  ✗ {api_path}: {st} {resp}")
    print(f"上传完成：成功 {ok}，失败 {fail}")

    for api_path in TO_DELETE:
        qpath = urllib.parse.quote(api_path, safe="/")
        st, head = call("GET", f"/repos/{OWNER}/{REPO}/contents/{qpath}?ref={branch}")
        if st == 200:
            st2, _ = call("DELETE", f"/repos/{OWNER}/{REPO}/contents/{qpath}",
                          {"message": f"chore(handoff): remove archive {api_path}",
                           "sha": head["sha"], "branch": branch})
            print(f"删除压缩包 {api_path}: HTTP {st2}")
        else:
            print(f"压缩包不存在，跳过 {api_path}")

    # 抽样回读校验
    raw_base = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{branch}/"
    for api_path, want, size in uploaded[:3]:
        url = raw_base + urllib.parse.quote(api_path, safe="/")
        got = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "v"}),
                                     timeout=300).read()
        print(f"回读 {api_path}: {len(got)} bytes 一致={hashlib.sha256(got).hexdigest() == want}")


if __name__ == "__main__":
    main()
