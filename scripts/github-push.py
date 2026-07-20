#!/usr/bin/env python3
"""
GitHub REST API 経由で複数ファイルを atomic commit ＆ push するスクリプト。

sandbox の FUSE マウント制限で git コマンドが使えないため、
Git Data API を使って直接リモート（origin/main）にコミットする。

使い方:
    python3 scripts/github-push.py --message "commit message" \\
        --add path/to/new-or-modified1.mdx path/to/new2.webp \\
        --delete path/to/remove.mdx

引数:
    --message  : commit message（必須）
    --add      : 追加/変更するファイルのローカルパス（複数可）
    --delete   : 削除するファイルのリポジトリ内パス（複数可）
    --branch   : 対象ブランチ（デフォルト main）
    --dry-run  : 実際には送信せず、動作確認のみ

前提:
    /Users/hideki/CoreSignal/.git-credentials に PAT が保存されている
    フォーマット: https://Nanaumi-dep:<PAT>@github.com
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error


# ==========================
# 設定
# ==========================
REPO_OWNER = "Nanaumi-dep"
REPO_NAME = "coresignal"
# sandbox セッション名は毎回変わるため、スクリプト自身の位置から動的に解決する
# scripts/github-push.py → CoreSignal-media → CoreSignal（.git-credentials 置き場）
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
CREDENTIALS_FILE = os.path.join(os.path.dirname(LOCAL_REPO_ROOT), ".git-credentials")


# ==========================
# PAT 読み込み
# ==========================
def load_pat():
    """
    .git-credentials から PAT を抽出する。
    フォーマット: https://Nanaumi-dep:<PAT>@github.com
    """
    if not os.path.exists(CREDENTIALS_FILE):
        sys.exit(f"ERROR: credentials file not found: {CREDENTIALS_FILE}")

    with open(CREDENTIALS_FILE, "r") as f:
        line = f.read().strip()

    # https://<user>:<PAT>@github.com からPAT部分を抽出
    m = re.match(r"https://([^:]+):([^@]+)@github\.com", line)
    if not m:
        sys.exit(f"ERROR: invalid .git-credentials format")

    return m.group(1), m.group(2)  # (username, pat)


# ==========================
# GitHub API 呼び出しヘルパー
# ==========================
def github_api(method, endpoint, pat, data=None):
    """
    GitHub REST API を呼び出す。data は dict（JSON化される）。
    戻り値: parsed JSON レスポンス
    """
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/{endpoint}"

    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "coresignal-auto-publish",
    }

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"ERROR: GitHub API {method} {endpoint} failed with {e.code}\n{body}")


# ==========================
# amazon-cache.json 専用マージ処理
# ==========================
def _merge_amazon_cache_with_remote(pat, local_path, branch):
    """
    amazon-cache.json のマージ処理:
    - GitHub 最新版を base（PA-API 週次更新の結果を尊重）
    - ローカルの新規ASINだけを追加
    - 既存ASINは GitHub 最新を優先（ローカルの古い版で上書きしない）

    これにより GitHub Actions の週次 PA-API 更新と、auto-round/monitor の
    新ASIN追加が競合しなくなる。
    """
    # GitHub から最新版を取得
    try:
        result = github_api(
            "GET",
            f"contents/src/data/amazon-cache.json?ref={branch}",
            pat
        )
        remote_content = base64.b64decode(result["content"]).decode("utf-8")
        remote_cache = json.loads(remote_content)
    except SystemExit:
        # リモートに amazon-cache.json が無い、または取得失敗
        # → フォールバック：ローカル版をそのまま送る
        print("[merge] WARNING: remote amazon-cache.json not found, using local as-is")
        with open(local_path, "rb") as f:
            return f.read()

    # ローカル版を読む
    with open(local_path, "r", encoding="utf-8") as f:
        local_cache = json.load(f)

    # マージ：既存ASINは remote、新規ASINは local
    merged = dict(remote_cache)  # remote をベースにする
    added_asins = []
    for asin, info in local_cache.items():
        if asin not in remote_cache:
            merged[asin] = info
            added_asins.append(asin)

    if added_asins:
        print(f"[merge] Added ASINs from local: {', '.join(added_asins)}")
    else:
        print(f"[merge] No new ASINs to add, remote version kept as-is")

    # JSON 整形して bytes 化（update-amazon-cache.mjs と同じフォーマット）
    return json.dumps(merged, ensure_ascii=False, indent=2).encode("utf-8")


# ==========================
# Git Data API による atomic commit
# ==========================
def commit_files(pat, branch, message, files_to_add, files_to_delete):
    """
    複数ファイルを1つのコミットにまとめて push する。
    files_to_add: [(repo_path, local_path), ...]
    files_to_delete: [repo_path, ...]
    """

    # 1. 現在のブランチの最新 commit SHA を取得
    ref = github_api("GET", f"git/refs/heads/{branch}", pat)
    latest_commit_sha = ref["object"]["sha"]
    print(f"[1/6] Latest commit on {branch}: {latest_commit_sha[:8]}")

    # 2. その commit の tree SHA を取得
    latest_commit = github_api("GET", f"git/commits/{latest_commit_sha}", pat)
    base_tree_sha = latest_commit["tree"]["sha"]
    print(f"[2/6] Base tree: {base_tree_sha[:8]}")

    # 3. 追加/変更ファイルを Blob として作成
    tree_entries = []
    for repo_path, local_path in files_to_add:
        if not os.path.exists(local_path):
            sys.exit(f"ERROR: file not found: {local_path}")

        # amazon-cache.json だけ特別処理：GitHub 最新版とマージ
        # 目的：GitHub Actions の週次 PA-API 更新（既存ASINの価格）を上書きせず、
        #      ローカルの新規ASINだけを追加する
        if repo_path == "src/data/amazon-cache.json":
            content_bytes = _merge_amazon_cache_with_remote(pat, local_path, branch)
        else:
            with open(local_path, "rb") as f:
                content_bytes = f.read()

        content_b64 = base64.b64encode(content_bytes).decode("ascii")
        blob = github_api("POST", "git/blobs", pat, {
            "content": content_b64,
            "encoding": "base64",
        })
        tree_entries.append({
            "path": repo_path,
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })
        print(f"[3/6] Blob created: {repo_path} → {blob['sha'][:8]}")

    # 4. 削除ファイルは sha: null で tree entry を作る
    for repo_path in files_to_delete:
        tree_entries.append({
            "path": repo_path,
            "mode": "100644",
            "type": "blob",
            "sha": None,
        })
        print(f"[3/6] Delete entry: {repo_path}")

    if not tree_entries:
        sys.exit("ERROR: no files to commit")

    # 5. 新しい tree を作成
    new_tree = github_api("POST", "git/trees", pat, {
        "base_tree": base_tree_sha,
        "tree": tree_entries,
    })
    print(f"[4/6] New tree: {new_tree['sha'][:8]}")

    # 6. 新しい commit を作成
    new_commit = github_api("POST", "git/commits", pat, {
        "message": message,
        "tree": new_tree["sha"],
        "parents": [latest_commit_sha],
    })
    print(f"[5/6] New commit: {new_commit['sha'][:8]} - {message}")

    # 7. ブランチの ref を更新（実質的にこれが push）
    updated_ref = github_api("PATCH", f"git/refs/heads/{branch}", pat, {
        "sha": new_commit["sha"],
        "force": False,
    })
    print(f"[6/6] Branch {branch} updated → {updated_ref['object']['sha'][:8]}")
    print(f"\nSUCCESS: https://github.com/{REPO_OWNER}/{REPO_NAME}/commit/{new_commit['sha']}")

    return new_commit["sha"]


# ==========================
# ローカルパス → リポジトリ内パス変換
# ==========================
def local_to_repo_path(local_path):
    """
    /sessions/.../mnt/CoreSignal/CoreSignal-media/xxx/yyy.mdx → xxx/yyy.mdx
    """
    abs_path = os.path.abspath(local_path)
    if not abs_path.startswith(LOCAL_REPO_ROOT):
        sys.exit(f"ERROR: path {local_path} is outside repo root {LOCAL_REPO_ROOT}")
    rel = abs_path[len(LOCAL_REPO_ROOT):].lstrip("/")
    return rel


# ==========================
# メイン
# ==========================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", required=True, help="commit message")
    ap.add_argument("--add", nargs="*", default=[], help="local paths to add/modify")
    ap.add_argument("--delete", nargs="*", default=[], help="repo paths to delete")
    ap.add_argument("--branch", default="main", help="target branch (default: main)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be done, don't push")
    args = ap.parse_args()

    if not args.add and not args.delete:
        sys.exit("ERROR: must specify --add or --delete")

    username, pat = load_pat()
    print(f"Loaded credentials for user: {username}")
    print(f"Target: {REPO_OWNER}/{REPO_NAME}, branch: {args.branch}")
    print(f"Message: {args.message}\n")

    # --add のローカルパスをリポジトリ内パスに変換
    files_to_add = [(local_to_repo_path(p), p) for p in args.add]

    if args.dry_run:
        print("DRY RUN - would commit the following:")
        for repo_path, local_path in files_to_add:
            size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            print(f"  ADD    {repo_path} ({size} bytes)")
        for repo_path in args.delete:
            print(f"  DELETE {repo_path}")
        return

    commit_files(pat, args.branch, args.message, files_to_add, args.delete)


if __name__ == "__main__":
    main()
