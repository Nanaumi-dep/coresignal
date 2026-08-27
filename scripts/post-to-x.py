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

# X の加重文字カウント（twitter-text 準拠）
#   ASCII・ラテン系 = 1 / 日本語などの CJK = 2 / URL = 23 固定
#   上限 280 なので、日本語のみなら実質 140 文字
TWEET_MAX_WEIGHT = 280
URL_WEIGHT = 23
POST_INTERVAL_SEC = 5    # 複数投稿時の間隔

# 重み1として扱う Unicode 範囲（twitter-text の weightedRanges）
LIGHT_RANGES = (
    (0x0000, 0x10FF),   # ASCII, ラテン, ギリシャ, キリル, ヘブライ, アラビア 等
    (0x2000, 0x200D),
    (0x2010, 0x201F),
    (0x2032, 0x2037),
)


def char_weight(ch: str) -> int:
    cp = ord(ch)
    for lo, hi in LIGHT_RANGES:
        if lo <= cp <= hi:
            return 1
    return 2


def weighted_len(text: str) -> int:
    """X の加重文字数を返す（URL は別途 URL_WEIGHT で計算する前提）。"""
    return sum(char_weight(c) for c in text)


def truncate_weighted(text: str, budget: int, sentence_end: bool = False) -> str:
    """加重 budget に収まるよう末尾を切る。

    sentence_end=True なら「。」で終わる位置を優先して切り、
    語の途中で切れた不格好な末尾を避ける（見つからなければ … で切る）。
    """
    if weighted_len(text) <= budget:
        return text

    acc, out = 0, []
    for ch in text:
        w = char_weight(ch)
        if acc + w > budget - 2:      # 末尾の … と余白分
            break
        acc += w
        out.append(ch)
    cut = "".join(out)

    if sentence_end:
        # 「。」で終われるならそこまで（短くなりすぎない範囲で）
        idx = cut.rfind("。")
        if idx >= 0 and weighted_len(cut[: idx + 1]) >= budget * 0.5:
            return cut[: idx + 1]

    return cut.rstrip("、。・ ") + "…"

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
    """加重280に収まるツイート本文を組み立てる（日本語は1文字=2）。"""
    title = fm.get("title", "").strip()
    desc = fm.get("description", "").strip()
    hashtags = build_hashtags(fm)

    # タイトルの "｜" 以降は補足。加重が重いので原則そちらは落とす
    title_main = title.split("｜")[0].strip()

    # 固定消費分: URL(23) + ハッシュタグ + 改行(\n\n × 最大3 = 加重6)
    fixed = URL_WEIGHT + weighted_len(hashtags) + 6
    body_budget = TWEET_MAX_WEIGHT - fixed

    # 1. タイトル本体を入れる（長すぎれば切る）
    body = truncate_weighted(title_main, body_budget)

    # 2. 余りがあれば description の頭を足す（最低でも加重40は欲しい）
    used = weighted_len(body)
    remain = body_budget - used - 2      # 改行分
    if desc and remain >= 40:
        snippet = truncate_weighted(desc, remain, sentence_end=True)
        body = f"{body}\n\n{snippet}"

    parts = [body, url]
    if hashtags:
        parts.append(hashtags)
    return "\n\n".join(parts)


def tweet_weight(text: str, url: str) -> int:
    """完成したツイートの加重長（URL は23固定換算）。"""
    return weighted_len(text.replace(url, "")) + URL_WEIGHT


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
