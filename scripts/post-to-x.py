#!/usr/bin/env python3
"""
新規公開した記事を X (Twitter) に自動投稿する。

GitHub Actions から呼ばれる想定。直前のコミットで追加された
src/content/posts/**/*.mdx を検出し、frontmatter から
title / description / category / tags を読んで1件ずつツイートする。

必要な環境変数（GitHub Secrets 経由）:
  X_CONSUMER_KEY
  X_CONSUMER_SECRET
  X_ACCESS_TOKEN
  X_ACCESS_TOKEN_SECRET

依存: requests, requests-oauthlib
  pip install requests requests-oauthlib
"""

import os
import re
import sys
import time
import subprocess
from pathlib import Path

try:
    import requests
    from requests_oauthlib import OAuth1
except ImportError:
    print("ERROR: pip install requests requests-oauthlib が必要です", file=sys.stderr)
    sys.exit(1)

# ─────────────────────────────────────────
# 設定
# ─────────────────────────────────────────

SITE_URL = "https://coresignal.jp"
API_ENDPOINT = "https://api.twitter.com/2/tweets"
TWEET_MAX = 280
URL_LENGTH = 23          # X は URL を一律23文字として数える
POST_INTERVAL_SEC = 5    # 複数投稿時の間隔

# タグ → ハッシュタグ変換（該当なしはスキップ）
HASHTAG_MAP = {
    "gadget": "#ガジェット",
    "creditcard": "#クレジットカード",
}

# 除外するタグ（ハッシュタグにすると冗長なもの）
TAG_BLOCKLIST = {"デスク環境", "限定品", "セール"}


# ─────────────────────────────────────────
# frontmatter パース
# ─────────────────────────────────────────

def parse_frontmatter(path: Path) -> dict | None:
    """MDX の frontmatter を最低限パースする（PyYAML 非依存）。"""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ! 読み込み失敗: {path} ({e})", file=sys.stderr)
        return None

    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        print(f"  ! frontmatter なし: {path}", file=sys.stderr)
        return None

    data: dict = {}
    for line in m.group(1).split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        kv = re.match(r'^(\w+):\s*(.*)$', line)
        if not kv:
            continue
        key, raw = kv.group(1), kv.group(2).strip()

        # 配列 ["a", "b"]
        if raw.startswith("[") and raw.endswith("]"):
            data[key] = re.findall(r'"([^"]*)"', raw)
        # クォート付き文字列
        elif raw.startswith('"') and raw.endswith('"'):
            data[key] = raw[1:-1]
        elif raw in ("true", "false"):
            data[key] = raw == "true"
        else:
            data[key] = raw

    return data


# ─────────────────────────────────────────
# ツイート本文の組み立て
# ─────────────────────────────────────────

def build_hashtags(fm: dict) -> str:
    """カテゴリ + タグ最大2件のハッシュタグ文字列を作る。"""
    tags = []

    cat = HASHTAG_MAP.get(fm.get("category", ""))
    if cat:
        tags.append(cat)

    for t in (fm.get("tags") or [])[:3]:
        if t in TAG_BLOCKLIST:
            continue
        # 英数字・カタカナ等をそのままハッシュタグ化（記号・空白は除去）
        clean = re.sub(r"[^\w぀-ヿ一-鿿]", "", t)
        if clean and f"#{clean}" not in tags:
            tags.append(f"#{clean}")
        if len(tags) >= 3:
            break

    return " ".join(tags)


def build_tweet(fm: dict, url: str) -> str:
    """280文字に収まるツイート本文を組み立てる。"""
    title = fm.get("title", "").strip()
    desc = fm.get("description", "").strip()
    hashtags = build_hashtags(fm)

    # タイトルの "｜" 以降は補足なので、長い場合は落とす
    title_short = title.split("｜")[0].strip() if len(title) > 60 else title

    # URL(23) + 改行類 + ハッシュタグ の固定分を引いた残りが本文枠
    fixed = URL_LENGTH + len(hashtags) + 4  # 改行 x3 + 余白
    body_budget = TWEET_MAX - fixed

    body = title_short
    # タイトルが短ければ description の頭も足す
    if len(body) + 40 < body_budget and desc:
        remain = body_budget - len(body) - 2
        if remain > 20:
            snippet = desc[:remain].rstrip("、。 ")
            body = f"{body}\n\n{snippet}"

    if len(body) > body_budget:
        body = body[: body_budget - 1].rstrip() + "…"

    parts = [body, url]
    if hashtags:
        parts.append(hashtags)
    return "\n\n".join(parts)


# ─────────────────────────────────────────
# 新規記事の検出
# ─────────────────────────────────────────

def find_new_posts(repo_root: Path) -> list[Path]:
    """直前のコミットで Added された記事 MDX を返す。"""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=A", "HEAD~1", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        print(f"ERROR: git diff 失敗: {e}", file=sys.stderr)
        return []

    posts = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("src/content/posts/") and line.endswith(".mdx"):
            p = repo_root / line
            if p.exists():
                posts.append(p)
    return posts


def post_url_from_path(path: Path, fm: dict) -> str:
    """記事パスと frontmatter から公開 URL を組み立てる。"""
    slug = path.stem
    category = fm.get("category", "")
    return f"{SITE_URL}/{category}/{slug}/"


# ─────────────────────────────────────────
# X API 投稿
# ─────────────────────────────────────────

def get_auth() -> OAuth1:
    keys = {
        "client_key": os.environ.get("X_CONSUMER_KEY"),
        "client_secret": os.environ.get("X_CONSUMER_SECRET"),
        "resource_owner_key": os.environ.get("X_ACCESS_TOKEN"),
        "resource_owner_secret": os.environ.get("X_ACCESS_TOKEN_SECRET"),
    }
    missing = [k for k, v in keys.items() if not v]
    if missing:
        print(f"ERROR: 環境変数が不足しています: {missing}", file=sys.stderr)
        sys.exit(1)
    return OAuth1(**keys, signature_type="auth_header")


def post_tweet(text: str, auth: OAuth1, dry_run: bool = False) -> bool:
    if dry_run:
        print("  [DRY-RUN] 投稿内容:")
        print("  " + text.replace("\n", "\n  "))
        return True

    try:
        r = requests.post(API_ENDPOINT, json={"text": text}, auth=auth, timeout=30)
    except Exception as e:
        print(f"  ✗ リクエスト失敗: {e}", file=sys.stderr)
        return False

    if r.status_code == 201:
        tweet_id = r.json().get("data", {}).get("id", "?")
        print(f"  ✓ 投稿成功: https://x.com/i/status/{tweet_id}")
        return True

    print(f"  ✗ 投稿失敗 ({r.status_code}): {r.text[:300]}", file=sys.stderr)
    return False


# ─────────────────────────────────────────
# main
# ─────────────────────────────────────────

def main() -> int:
    dry_run = "--dry-run" in sys.argv
    repo_root = Path(__file__).resolve().parent.parent

    posts = find_new_posts(repo_root)
    if not posts:
        print("新規記事なし。何も投稿しません。")
        return 0

    print(f"新規記事 {len(posts)} 件を検出:")
    for p in posts:
        print(f"  - {p.relative_to(repo_root)}")
    print()

    auth = None if dry_run else get_auth()

    ok = 0
    for i, path in enumerate(posts):
        fm = parse_frontmatter(path)
        if not fm or not fm.get("title") or not fm.get("category"):
            print(f"  ! frontmatter 不備のためスキップ: {path.name}", file=sys.stderr)
            continue

        url = post_url_from_path(path, fm)
        text = build_tweet(fm, url)

        print(f"[{i + 1}/{len(posts)}] {path.name} ({len(text)}文字)")
        if post_tweet(text, auth, dry_run):
            ok += 1

        if i < len(posts) - 1:
            time.sleep(POST_INTERVAL_SEC)

    print(f"\n完了: {ok}/{len(posts)} 件投稿")
    # 投稿失敗してもデプロイは止めない方針なので常に 0 を返す
    return 0


if __name__ == "__main__":
    sys.exit(main())
