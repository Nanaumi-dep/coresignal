#!/bin/bash
# CoreSignal publisher スクリプト (Phase 1)
# 使い方: bash scripts/publisher.sh <slug>
# 例:     bash scripts/publisher.sh soundcore-p42i
#
# 動作:
#   1. drafts/[slug].mdx の存在確認
#   2. frontmatter を読んで category を検出
#   3. eyecatch画像の配置確認 (未配置なら警告)
#   4. amazon-cache.json のASIN確認 (未登録なら警告)
#   5. drafts/ → posts/[category]/ にファイル移動
#   6. 記事ログ (記事ログ.txt) に1行追記
#   7. 英生さんが手動で残す作業をリマインド (AmazonリンクASP差し替え、git push)

set -e

SLUG="$1"

if [ -z "$SLUG" ]; then
  echo "❌ Usage: bash scripts/publisher.sh <slug>"
  echo "   例: bash scripts/publisher.sh soundcore-p42i"
  exit 1
fi

# パス設定
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRAFT_FILE="$REPO_ROOT/src/content/drafts/${SLUG}.mdx"
ARTICLE_LOG="$(dirname "$REPO_ROOT")/記事ログ.txt"
CACHE_JSON="$REPO_ROOT/src/data/amazon-cache.json"

echo "=========================================="
echo " CoreSignal Publisher (Phase 1)"
echo "=========================================="
echo "SLUG: $SLUG"
echo ""

# 1. drafts の存在確認
if [ ! -f "$DRAFT_FILE" ]; then
  echo "❌ draft not found: $DRAFT_FILE"
  echo "   drafts/ 内の記事一覧:"
  ls "$REPO_ROOT/src/content/drafts/" | grep '.mdx' | sed 's|^|     |'
  exit 1
fi

echo "✅ Draft found: $DRAFT_FILE"

# 2. frontmatter から category を検出
CATEGORY=$(grep -m1 '^category:' "$DRAFT_FILE" | sed 's/category:[[:space:]]*"\([^"]*\)".*/\1/')

if [ -z "$CATEGORY" ]; then
  echo "❌ category が frontmatter で検出できません"
  exit 1
fi

if [ "$CATEGORY" != "gadget" ] && [ "$CATEGORY" != "creditcard" ]; then
  echo "⚠️  category が unknown: $CATEGORY (gadget/creditcard 以外)"
fi

echo "✅ Category: $CATEGORY"

DEST_DIR="$REPO_ROOT/src/content/posts/$CATEGORY"
DEST_FILE="$DEST_DIR/${SLUG}.mdx"

if [ -f "$DEST_FILE" ]; then
  echo "❌ 公開先に既にファイルが存在: $DEST_FILE"
  echo "   既存を上書きせず処理を中断します"
  exit 1
fi

# 3. frontmatter から title / eyecatch を抽出
TITLE=$(grep -m1 '^title:' "$DRAFT_FILE" | sed 's/title:[[:space:]]*"\([^"]*\)".*/\1/')
EYECATCH=$(grep -m1 '^eyecatch:' "$DRAFT_FILE" | sed 's/eyecatch:[[:space:]]*"\([^"]*\)".*/\1/')

# 4. eyecatch画像の配置確認
if [ -n "$EYECATCH" ]; then
  EYECATCH_FILE="$REPO_ROOT/public${EYECATCH}"
  if [ -f "$EYECATCH_FILE" ]; then
    echo "✅ eyecatch: $EYECATCH_FILE"
  else
    echo "⚠️  eyecatch 未配置: $EYECATCH_FILE"
    echo "   → 公開後に配置してください（記事は移動可能）"
  fi
fi

# 5. amazon-cache.json のASIN確認 (MDX内の asin="XXXX" を抽出)
ASINS=$(grep -oE 'asin="[A-Z0-9]{10}"' "$DRAFT_FILE" | sed 's/asin="\([^"]*\)"/\1/' | sort -u)

if [ -n "$ASINS" ]; then
  echo ""
  echo "=== AmazonCard ASIN の確認 ==="
  for ASIN in $ASINS; do
    if [ "$ASIN" = "XXXXXXXXXX" ]; then
      echo "⚠️  仮ASIN検出: $ASIN → 実ASINに差し替えが必要"
    else
      if grep -q "\"$ASIN\":" "$CACHE_JSON"; then
        echo "✅ $ASIN: amazon-cache に登録済み"
      else
        echo "⚠️  $ASIN: amazon-cache に未登録 → GitHub Actions次回実行で自動追加"
      fi
    fi
  done
fi

# 6. 記事ログ追記文の生成（対策KWは手動）
echo ""
echo "=== 記事ログ追記文の生成 ==="
DATE=$(TZ='Asia/Tokyo' date '+%Y%m%d')
LOG_LINE="${DATE} | ${TITLE}（サイト） | 対策KW1 / 対策KW2 / 対策KW3 / 対策KW4 / 対策KW5"
echo "追記予定:"
echo "  $LOG_LINE"
echo "→ 対策KWは frontmatter や本文から手動で埋めてください"
echo ""

# 7. drafts → posts 移動を実行
echo "=== ファイル移動を実行 ==="
mv "$DRAFT_FILE" "$DEST_FILE"
echo "✅ 移動完了: $DEST_FILE"

# 8. 記事ログにテンプレ行を追加（対策KWは手動修正前提）
echo "$LOG_LINE" >> "$ARTICLE_LOG"
echo "✅ 記事ログ にテンプレ行を追記: $ARTICLE_LOG"
echo "   → 「対策KW1 /...」の部分を実際のKWに手動で差し替えてください"

# 9. 英生さんの残作業リマインド
echo ""
echo "=========================================="
echo " 🔔 残作業（英生さん手動）"
echo "=========================================="
echo "  1. 記事内の AmazonCard の href を A8.net or アクセストレード or アソシエイトタグに差し替え"
echo "     （AmazonCard コンポーネントは cache 経由で自動でタグ付与されるので、そのままでもOKな場合あり）"
echo "  2. 記事ログ の対策KW欄を実際のKWに差し替え"
if [ -n "$EYECATCH" ] && [ ! -f "$REPO_ROOT/public${EYECATCH}" ]; then
  echo "  3. eyecatch画像を配置: $REPO_ROOT/public${EYECATCH}"
fi
echo "  4. git add . && git commit -m \"add: ${SLUG}\" && git push"
echo "     → GitHub Actions が自動デプロイ"
echo "=========================================="
