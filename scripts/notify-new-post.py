#!/usr/bin/env python3
"""
新規公開した記事の X 投稿文を組み立て、GitHub Issue として通知する。

X API への直接投稿（post-to-x.py）は無料枠が書き込み非対応のため停止中。
代わりに投稿文を Issue に書き出し、英生さんが手元でコピペして投稿する運用にする。
Issue は assignee 指定で作るので、GitHub からメール／モバイル通知が飛ぶ。

投稿文の組み立てロジックは post-to-x.py を import して再利用する
（加重文字カウント・タイトル整形・ハッシュタグ生成は共通）。

GitHub Actions から呼ばれる想定:
  python3 scripts/notify-new-post.py --base <sha> --head <sha>

手動リカバリ（取りこぼした記事を後から Issue 化する）:
  python3 scripts/notify-new-post.py --paths src/content/posts/gadget/foo.mdx

ローカル確認（書き込みなし）:
  python3 scripts/notify-new-post.py --paths <path> --dry-run

必要な環境変数:
  GITHUB_TOKEN        Actions が自動で渡す（permissions: issues: write が必要）
  GITHUB_REPOSITORY   Actions が自動で渡す（owner/repo）
  ISSUE_ASSIGNEE      任意。省略時は owner を assignee にする
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUE_LABEL = "x-post"
LABEL_COLOR = "1DA1F2"
LABEL_DESC = "X に手動投稿する記事の下書き"


# ─────────────────────────────────────────
# post-to-x.py の投稿文ロジックを再利用
# ─────────────────────────────────────────

def load_post_to_x():
    """post-to-x.py をモジュールとして読み込む（ファイル名にハイフンがあるため importlib）。"""
    path = REPO_ROOT / "scripts" / "post-to-x.py"
    if not path.exists():
        sys.exit(f"ERROR: {path} が見つかりません")
    spec = importlib.util.spec_from_file_location("post_to_x", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────
# 新規記事の検出
# ─────────────────────────────────────────

def git(*args) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout


def detect_added_posts(base: str | None, head: str) -> list[Path]:
    """base..head の範囲で Added された記事 MDX を返す。

    push に複数コミットが含まれてもすべて拾えるよう、
    HEAD~1 固定ではなく github.event.before からの範囲で見る。
    """
    ranges = []
    if base and set(base) != {"0"}:      # 全ゼロ = ブランチ新規作成時
        ranges.append(f"{base}..{head}")
    ranges.append(f"{head}~1..{head}")   # フォールバック

    for rng in ranges:
        try:
            out = git("diff", "--name-only", "--diff-filter=A", rng)
        except subprocess.CalledProcessError:
            continue
        posts = [
            REPO_ROOT / line.strip()
            for line in out.splitlines()
            if line.strip().startswith("src/content/posts/")
            and line.strip().endswith(".mdx")
        ]
        print(f"  差分範囲 {rng} → 新規 {len(posts)} 件")
        return [p for p in posts if p.exists()]

    print("  ! git diff に失敗しました", file=sys.stderr)
    return []


# ─────────────────────────────────────────
# GitHub API
# ─────────────────────────────────────────

class GitHub:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo

    def _call(self, method: str, endpoint: str, payload: dict | None = None):
        url = f"https://api.github.com/repos/{self.repo}/{endpoint}"
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "coresignal-notify-new-post",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"{method} {endpoint} → {e.code}: {body}") from None

    def ensure_label(self):
        """ラベルが無ければ作る（既存なら何もしない）。"""
        try:
            self._call("GET", f"labels/{ISSUE_LABEL}")
            return
        except RuntimeError:
            pass
        try:
            self._call("POST", "labels", {
                "name": ISSUE_LABEL, "color": LABEL_COLOR, "description": LABEL_DESC,
            })
            print(f"  ラベル '{ISSUE_LABEL}' を作成しました")
        except RuntimeError as e:
            print(f"  ! ラベル作成をスキップ: {e}", file=sys.stderr)

    def issue_exists(self, title: str) -> bool:
        """同じタイトルの Issue が既にあるか（open / closed 問わず）。"""
        try:
            issues = self._call("GET", "issues?state=all&labels=" + ISSUE_LABEL + "&per_page=100")
        except RuntimeError:
            return False
        return any(i.get("title") == title for i in issues)

    def create_issue(self, title: str, body: str, assignee: str | None) -> str:
        payload = {"title": title, "body": body, "labels": [ISSUE_LABEL]}
        if assignee:
            payload["assignees"] = [assignee]
        try:
            return self._call("POST", "issues", payload)["html_url"]
        except RuntimeError as e:
            # assignee やラベルが弾かれた場合は最小構成で作り直す
            print(f"  ! 通常作成に失敗、最小構成で再試行: {e}", file=sys.stderr)
            return self._call("POST", "issues", {"title": title, "body": body})["html_url"]


# ─────────────────────────────────────────
# Issue 本文
# ─────────────────────────────────────────

def build_issue(px, path: Path, fm: dict) -> tuple[str, str]:
    url = px.post_url_from_path(path, fm)
    tweet = px.build_tweet(fm, url)
    weight = px.weighted_len(tweet.replace(url, "")) + px.URL_WEIGHT

    slug = path.stem
    title = f"X投稿: {slug}"
    warn = "" if weight <= 280 else (
        f"\n> [!WARNING]\n> 加重 {weight} が上限280を超えています。投稿前に短くしてください。\n"
    )

    body = f"""記事を公開しました。下のブロックをコピーして X に投稿してください。

**{fm.get('title', slug)}**
{url}
{warn}
### 投稿文（加重 {weight}/280）

```
{tweet}
```

<details>
<summary>記事情報</summary>

| 項目 | 内容 |
|---|---|
| slug | `{slug}` |
| カテゴリ | {fm.get('category', '-')} |
| 公開日時 | {fm.get('date', '-')} |
| タグ | {', '.join(fm.get('tags') or []) or '-'} |
| ファイル | `{path.relative_to(REPO_ROOT)}` |

</details>

---
投稿したらこの Issue を **Close** してください。Open のまま残っているものが未投稿分です。

<sub>X API の無料枠が書き込み非対応のため、自動投稿（`post-to-x.yml`）は停止中です。この Issue は `notify-new-post.yml` が自動生成しています。</sub>
"""
    return title, body


# ─────────────────────────────────────────
# main
# ─────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="差分の起点 SHA（github.event.before）")
    ap.add_argument("--head", default="HEAD", help="差分の終点 SHA")
    ap.add_argument("--paths", nargs="*", help="対象記事を明示指定（手動リカバリ用）")
    ap.add_argument("--dry-run", action="store_true", help="Issue を作らず内容だけ表示")
    args = ap.parse_args()

    px = load_post_to_x()

    if args.paths:
        posts = [REPO_ROOT / p for p in args.paths]
        missing = [str(p) for p in posts if not p.exists()]
        if missing:
            sys.exit(f"ERROR: 存在しないパス: {missing}")
        print(f"明示指定 {len(posts)} 件")
    else:
        print("新規記事を検出中...")
        posts = detect_added_posts(args.base, args.head)

    if not posts:
        print("新規記事なし。Issue は作成しません。")
        return 0

    gh = None
    if not args.dry_run:
        token = os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("GITHUB_REPOSITORY")
        if not token or not repo:
            sys.exit("ERROR: GITHUB_TOKEN / GITHUB_REPOSITORY が未設定です")
        gh = GitHub(token, repo)
        gh.ensure_label()

    assignee = os.environ.get("ISSUE_ASSIGNEE") or (
        os.environ.get("GITHUB_REPOSITORY", "/").split("/")[0] or None
    )

    created = skipped = failed = 0
    for path in posts:
        fm = px.parse_frontmatter(path)
        if not fm or not fm.get("title") or not fm.get("category"):
            print(f"::warning::frontmatter 不備のためスキップ: {path.name}")
            failed += 1
            continue

        title, body = build_issue(px, path, fm)

        if args.dry_run:
            print("=" * 64)
            print(f"[DRY-RUN] {title}")
            print("=" * 64)
            print(body)
            created += 1
            continue

        if gh.issue_exists(title):
            print(f"  = 既に Issue があるためスキップ: {title}")
            skipped += 1
            continue

        try:
            print(f"  ✓ {title} → {gh.create_issue(title, body, assignee)}")
            created += 1
        except RuntimeError as e:
            print(f"::error::Issue 作成に失敗: {path.name} / {e}")
            failed += 1

    print(f"\n完了: 作成 {created} / スキップ {skipped} / 失敗 {failed}")
    # 通知が飛ばないと取りこぼしに気づけないので、失敗はワークフローを赤くする
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
