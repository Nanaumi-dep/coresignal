---
name: coresignal-site
description: CoreSignalサイト（coresignal.jp）の記事作成スキル。MDXフォーマット、frontmatter、AmazonCardコンポーネント、記事構成テンプレート、AmazonCard運用の細則、未発売商品の記事化判断、サイト×Note併存の使い分け、6観点チェック、セキュリティチェック、記事作成フローを定義。「サイト記事を書く」「MDX」「drafts」「coresignal.jpの記事」「ガジェット記事」「クレカ記事」「スペック記事」が話題に出たら必ず使う。writer / common スキルと併用すること。
---

# CoreSignal サイト記事作成ルール（coresignal.jp）

このスキルを使うときは、必ず以下も併せて読み込むこと。

- `coresignal-common`（メディアコンセプト・編集指針・情報源ルール・記事ログ運用）
- `coresignal-writer`（書き手「ナナ」の人格・キャラ・にじませ方・未体験品ルール・商品相性判断軸）

このスキルは「サイトでの表現の落とし方（MDXフォーマット、記法、収益導線、記事構成）」に絞る。書き手の人格と全体コンセプトはそれぞれ writer / common に集約されている。

## 書き手のにじませ方（サイト固有部分）

書き手の属性・キャラクター・文体の詳細は `coresignal-writer` を参照。ここではサイト側の運用ルールのみ抜粋する。

- **一人称は使わない**。「私」「自分」「僕」「俺」は文中に含めない
- 「エンジニアです」と自己紹介しない。判断基準・比較の切り口で視点をにじませる
- 主観動詞（「と思う」「と感じる」「個人的に」「気がする」「期待している」）は使わない。代わりに「〜と読み取れる」「〜と整理できる」「〜と想定される」で置換
- サイトはYouTubeやNoteから来た人に「人がいる気配」が伝わるトーンで書く（人格自体は writer に定義）

## カテゴリ別のトーン

書き手のキャラは writer 参照。サイトでのカテゴリ別の落とし方だけここで定義する。

**ガジェット（gadget）**

- スペック紹介・比較が主軸。書き手の視点は「判断基準の提示」や「評価の切り口」でにじませる
- 上から目線のレビューではなく、選択肢の中で自分の最適解を探す過程を共有する語り口
- エンジニア的合理性と、モノへの愛着が共存する
- メリット・デメリットは正直に書く

**クレジットカード（creditcard）**

- 公式発表・ニュースの事実整理が主軸。書き手の個人的な感想・体験談は入れない
- 変更点・影響範囲・比較表を正確にまとめる
- 数値・日付・条件は必ず公式情報と照合（`coresignal-common` の情報源ルール参照）

## ファイル保存

- 形式：MDX（.mdx）
- 保存先（下書き）：`CoreSignal-media/src/content/drafts/`（.gitignoreに含まれている）
- 保存先（公開）：`CoreSignal-media/src/content/posts/gadget/` または `creditcard/`
- 命名規則：半角英数字・ハイフンのみ・小文字・20文字以内。ファイル名 = URLスラッグ
- 既存の公開記事は原則として直接編集しない（feedback: follow_rules）

## MDX frontmatter

```yaml
---
title: "記事タイトル"
description: "120〜160文字の説明文"
date: "YYYY-MM-DD"
category: "gadget"  # または "creditcard"
tags: ["タグ1", "タグ2"]
eyecatch: "/images/posts/[slug].webp"
affiliate: true
brand: "Anker"                  # ガジェット記事のみ、任意
productName: "商品名"           # ガジェット記事のみ、任意
compatibleWith: ["macbook-air"] # ガジェット記事のみ、任意
---
```

⚠️ **重要（frontmatter 記法のNGパターン）**：

- `date:` と `category:` は**必ずダブルクォート付き string** で書く
- ❌ NG: `date: 2026-07-20`（YAMLがDateオブジェクトに変換 → Astroビルド失敗）
- ✅ OK: `date: "2026-07-20"`
- ❌ NG: `category: gadget`（クォートなしはスキーマ違反リスク）
- ✅ OK: `category: "gadget"`
- 同様に `title:` `description:` `productName:` もダブルクォート必須（コロン・カッコ・スラッシュ等の記号が入るため）
- `tags:` `compatibleWith:` は配列なので `[..., ...]` 記法、要素文字列はクォート推奨


### frontmatter `date` の運用（新設）

3種類の用途を意識して指定する。

| 用途 | 何を入れるか | 例 |
|---|---|---|
| 執筆基準日 | 記事を書いた日／drafts作成日 | 通常のスペック記事、レビュー記事 |
| イベント日 | 発売日・キャンペーン施行日・改定日 | 「7月1日から dカードがドコモFG体制へ」なら 2026-07-01 相当を意識できるが、公開日を優先する |
| 改定日 | 記事内容更新時 | 将来 `lastUpdated` フィールドで管理予定 |

### date の時刻付き運用（2026-07-23 新設）

- **`date` は時刻付き文字列で書く**：`date: "2026-07-23T20:00"`（JSTの公開時刻、ダブルクォート必須は従来通り）
- 理由：トップページ・カテゴリページのソートは `new Date(date)` 比較のため、日付のみだと**同日複数記事の並び順が不定**になる（2026-07-23 に朝の記事が最新扱いされた実害あり）
- 自動投稿ラウンドの時刻目安：朝 `T06:00`／昼 `T12:00`／夜 `T20:00`。手動公開時は実際の公開時刻でよい
- 表示側はレイアウトが `date.slice(0, 10)` で日付のみ表示するため、既存の日付のみ記事（`"2026-07-20"` 等）と混在しても表示は変わらない
- 既存記事の date 書き換えは不要

原則は「英生さんが公開作業をする日」を `date` に入れる。イベントに直結する記事は本文中に「XX月XX日施行」等の日付を明記して、`date` は公開日で運用する。

## eyecatch画像

- ファイル名：`/images/posts/[slug].webp`
- 保存先：`CoreSignal-media/public/images/posts/[slug].webp`
- 画像はメーカー公式素材（テキスト合成しない、CDN直リンクせず必ずダウンロード配置）
- 拡張子は基本 `.webp`（一部 `.png` や `.jpg` の既存例あり、新規は `.webp` 統一）
- 参考：既存記事の eyecatch はブランド公式サイトの製品画像（Anker公式Shopify CDN、Logicoolプレスリリース、BenQ公式ページ等）を利用
- サイトバナーは `/images/site/`、記事のeyecatchは `/images/posts/` で分ける（feedback: eyecatch_path）

## クレカ記事の画像運用（2026-07-22 新設）

**原則**：クレカ会社の券面画像・ロゴは使わない。eyecatchは自作グラフィック（Pillow生成、ロゴなしブランド名プレーンテキスト＋日本語コピー、feedback: creditcard_eyecatch 参照）。

**例外**：券面・デザイン自体がニュースの記事（新券面発表、デザインリニューアル等）に限り、以下の条件を**すべて**満たす場合は記事内で券面画像を使用可：

- カード会社の**ニュースリリース添付画像**であること（公式サイト商品ページからの転載は不可）
- **無加工**で掲載（トリミング・合成・色調変更なし）
- **出所明示（必須）**：手書きキャプションではなく `CitedImage` コンポーネントを使う（書式・スタイルをコンポーネント側で強制）
  - 根拠：引用構成なら著作権法48条の出所明示義務、配布素材利用なら各社利用条件への対応。常に記載して両方カバーする
  ```mdx
  import CitedImage from '../../../components/CitedImage.astro';

  <CitedImage
    src="/images/posts/[slug]-card.webp"
    alt="新デザインの券面"
    sourceName="〇〇カード ニュースリリース"
    sourceUrl="https://（公式リリースURL）"
    sourceDate="YYYY年MM月DD日"
  />
  ```
  - 画像ファイルはCDN直リンクせず必ずダウンロードして `/images/posts/` に配置（WebP変換可、ただし画像内容の加工は不可）
- **eyecatch / OGPには使わない**（装飾利用は引用の理屈が弱く、加工も発生しやすい）
- Visa / Mastercard等の国際ブランドロゴ単体は使わない（各社ブランドガイドラインの第三者利用制限）
- 判断が際どい場合は画像なしで通す（迷ったら使わない）

**ASP広告素材との関係**：A8.net／アクセストレードで提携承認済み案件の公式素材（券面入りバナー）はCTA枠で**無加工のまま**使用可。eyecatchへの流用・切り抜きは素材規約違反になりやすいため不可。

## アフィリエイトリンクの記法

### ガジェット記事（Amazonアソシエイト）— AmazonCardコンポーネント

MDXファイルの frontmatter 直後に import 文を書き、記事内に配置する。

```mdx
---
(frontmatter)
---

import AmazonCard from '../../../components/AmazonCard.astro';

## 記事本文...

<AmazonCard asin="XXXXXXXXXX" fallbackTitle="商品名をAmazonで見る" />
```

⚠️ **重要（import 文のNGパターン）**：

- ❌ NG: `import AmazonCard from '@/components/AmazonCard.astro';`（`@/` alias は未設定、Rollup ビルド失敗）
- ✅ OK: `import AmazonCard from '../../../components/AmazonCard.astro';`（相対パス、既存65記事すべてこの形）
- posts/gadget または posts/creditcard 配下からの相対パスは常に `../../../components/`（3階層上）

### 限定販売品の情報記事パターン（2026-07-20 新設）

Amazon で買えない商品（コンビニ限定、実店舗限定、海外限定など）を記事化する場合、以下の型が有効：

**成立条件**：
- 記事主題は「限定販売の情報整理」（読者は買い方調べに来ている、または情報として把握したい）
- 記事本文で明示的に「Amazon経由での購入を想定する場合は〇〇シリーズが選択肢」と誘導
- AmazonCard には「主題商品と同じブランドの、Amazon で買える現行モデル」を貼る（別シリーズでもOK）

**成立の理由**：
- 記事を読む人はその瞬間セブン/実店舗にはいない
- 「情報を知った上で、ネットで似た商品を選ぶ」需要を捕まえる
- Amazon 誘導は「今すぐ買える現実的な代替」として意味を持つ

**NG パターン**（誠実性を損なう）：
- 主題商品と全くカテゴリの違うAmazonCard（例：モバイルバッテリー記事にキーボードを貼る）
- 主題商品と価格帯が10倍以上乖離する上位モデルへの誘導（例：3,000円商品→30,000円商品）

**具体例（2026-07-20 実施）**：
- 記事：セブン限定 Anker LFP モバイルバッテリー（5000/10000mAh、3,000〜4,500円）
- AmazonCard：Anker Prime Power Bank（20100/26250mAh、高出力大容量、上位機として位置付け）
- 判断：カテゴリ同一（Ankerモバイルバッテリー）、価格帯上位版として代替提示

### ASIN 未取得時のフォールバック（2026-07-20 新設）

Amazon.co.jp で ASIN が取得できない場合、以下3択のいずれかで対応する。**仮ASIN `XXXXXXXXXX` の使用は絶対禁止**（リンク切れの元）：

#### (a) 通常運用：ASIN 取得できた場合
```mdx
<AmazonCard asin="B0XXXXXXX" fallbackTitle="商品名をAmazonで見る" />
```

#### (b) Amazon.co.jp に商品ページがない（発売間もない新製品等）
**AmazonSearchLink コンポーネント**で対応。Associates タグ自動付与＋CSS自動適用：
```mdx
import AmazonSearchLink from '../../../components/AmazonSearchLink.astro';

<AmazonSearchLink searchQuery="型番" fallbackTitle="製品名を Amazon で探す" />
```

⚠️ raw HTML の `<div class="amazon-card-fallback"><a href="...">` は使わない（scoped CSS でスタイル適用されず、タグも付かず収益ゼロになる）

#### (c) 完全に Amazon 未展開（セブン限定・海外限定など）
「限定販売品の情報記事パターン」を適用し、**同ブランドの Amazon で買える現行モデル**の AmazonCard を貼る（詳細は下記の同パターン説明参照）。

### 判定フロー

1. Step 3 事実確認で、型番を WebSearch (`amazon.co.jp` ドメイン絞り込み) で検索
2. `amazon.co.jp/dp/XXXXXXXXXX` 形式のURL が取れる → (a) 通常運用
3. 検索結果に商品なし、または同型番の別モデル → (b) Amazon 検索リンク
4. コンビニ限定・海外限定・輸入品などで Amazon 展開の見込みなし → (c) 同ブランド代替商品

### 編集者クレジット（2026-07-21 レイアウト自動挿入化）

**記事MDXには書かない**。`src/pages/[category]/[slug].astro` のレイアウトで全記事に自動挿入される：

```astro
{/* 編集者クレジット */}
<p class="text-sm mt-6 pt-4 border-t" style="color: var(--color-text-muted); border-color: var(--color-border);">
  編集者：<a href="/about/" class="underline" style="color: var(--color-text-muted);">ナナ</a>
</p>
```

- 位置：本文（`<Content />`）の直後、アフィリエイト開示の上
- 見た目：`text-sm` + `text-muted`（公開日/更新日と同じ控えめスタイル）、上に細い境界線

**目的**：
- Google の E-E-A-T の「Authoritativeness / Trustworthiness」シグナル
- サイト内回遊率向上（about ページへの流入）
- 「編集者が存在するメディア」の識別
- MDX に書かないので、文言変更は Astro レイアウト1箇所修正で全記事反映

**注意**：
- **MDX 末尾に「書き手：〜」や「編集者：〜」を書かない**（レイアウトで自動挿入されるので重複する）
- リンク先は `/about/`（末尾スラッシュ付き）

**配置ルール（feedback: amazoncard_placement）**

- **1箇所目**：記事の導入直後（スペック紹介の直前 or 直後）
- **2箇所目**：スペック紹介後、比較セクション直前（読者が「良さそう」と思うタイミング）
- **末尾**：AmazonCardを末尾に置かない。**手書きの「## 関連記事」セクションは廃止（2026-07-22）**：Astroレイアウトが同カテゴリ×タグ一致で関連記事3本を自動表示するため、MDXに書くと二重表示になる。文中の自然な内部リンク（アンカーテキスト付き）は推奨・継続
- **記事が長い場合の追加**：中盤にもう1個追加可（計3箇所まで）
- **重要**：`<div class="cta-amazon">` は旧記法。ガジェット記事では必ず `<AmazonCard>` を使う

### クレジットカード記事（A8.net / アクセストレード）

**CTAボタンはASP提携承認済みの案件のみ配置する（2026-07-22 変更）。**

- 未提携カード・ルール解説/ニュース系記事は**CTAなし**＋frontmatter `affiliate: false` で公開する
- 仮URLのCTAを置いても差し替えられず収益ゼロのまま表示だけ残るため、未提携時は最初から置かない
- 収益導線は代わりに**記事末尾の関連記事を提携済みカードのスペック記事に寄せる**（内部リンクでの送客をデフォルトとする）
- 提携済み案件でCTAを置く場合は2箇所配置。hrefは仮URLで書き、ナナがASPのアフィリエイトURLに差し替える。

```mdx
<div class="cta-amazon">
  <a href="https://www.amazon.co.jp" rel="nofollow sponsored" target="_blank">CTAテキスト →</a>
</div>
{/* ↑ A8.net or アクセストレードのアフィリエイトURLに差し替え */}
```

- **1箇所目**：記事中盤（変更点の整理が終わり、読者が「代替カードを探したい」と思うタイミング）
- **2箇所目**：記事末尾のまとめ後
- 記事末尾は公式リンク集で締める（**クレカ会社・サービス提供元の公式サイト・公式プレスリリースのみ許可**）
- 他メディア・個人ブログ・PR TIMESなどのメディアプラットフォームは公式扱いではない

## AmazonCard運用の細則（新設）

### 仮ASIN運用（発売前記事）

発売前で ASIN未確定の記事を書く場合：

- MDX内で `asin="XXXXXXXXXX"`（大文字X10文字）をプレースホルダとして使用
- 直下に MDX コメントで差し替えメモを書く：
  ```mdx
  <AmazonCard asin="XXXXXXXXXX" fallbackTitle="商品名をAmazonで見る" />
  {/* ↑ 実ASINに差し替え（発売後にAmazon掲載） */}
  ```
- 記事ログの対策KW欄に「仮ASIN」を含めておくと後で検索しやすい
- **発売から1週間以内に実ASINへ差し替える**運用を目安にする

### imageUrlプレースホルダの禁止（feedback: amazon_cache_imageurl）

`src/data/amazon-cache.json` を手で編集する場合、`imageUrl` に**実在しない文字列を絶対に入れない**。

- 新ASINを追加するときは以下のいずれかで対応：
  1. `imageUrl: ""`（空文字。既存に `price: ""` の前例あり、未取得を示す慣習）
  2. Claude in Chrome で実商品ページから正規imageUrlを取得してから埋める
  3. **エントリ追加自体を見送る**（GitHub Actionsが毎週月曜12:00 JSTにPA-APIで自動補完する）

- レガシー画像URL（`https://images-na.ssl-images-amazon.com/images/P/[ASIN]._SL500_.jpg`）は、新しい商品ASINでは 1×1 透明GIF（43バイト）が返ってきて実画像がないケースがある。**必ずダウンロードして中身確認**すること
- PA-API取得後は `https://m.media-amazon.com/images/I/[画像ID]._SL500_.jpg` 形式で自動格納される

### PA-API取得の週次スケジュール理解

`.github/workflows/update-amazon-cache.yml` が毎週月曜 12:00 JST（cron `0 18 * * 0` UTC）に自動実行される。手動実行は GitHub Actions の workflow_dispatch でも可。新ASINは自動実行を待つのが基本、緊急時は手動実行を提案する。

## 未発売商品の記事化判断（新設）

未発売商品を記事にするかは、以下の3段階で判断する。

### ✅ 公開可

以下がすべて揃っている場合、通常フローで記事化してよい。

- 発売日が公式アナウンスで確定している（「X月X日発売」）
- 公式サイトに製品ページと詳細スペックが公開されている
- Amazon等でASIN取得可能 or 予約ページが立っている
- 例：ロジクール G316 X 98（7/16発売、Amazon予約可、B0GJ8K9ZWR）

### 🟡 注意（公開可だが表現に配慮）

以下の場合は「発売前段階の情報として書く」ことを明示する。

- 発売時期が「X月上旬」「X月頃」など幅を持たせた表現
- 公式情報はあるが詳細スペックが一部未公開
- ASINは未取得（Amazon掲載前）
- 例：Anker×ポケモン新製品（7月上旬発売予定、公式ページは "Sold Out" 状態でASIN未確定）

対応：
- 本文冒頭で「発売前段階の情報を元に整理する」旨を明示
- AmazonCardは仮ASIN運用（詳細は上記細則）
- 発売開始を追跡し、公式アナウンス後に差し替え

### 🔲 保留（記事化しない）

以下は記事化を見送る。

- 発売日未確定（噂・リーク情報のみ）
- 一次情報が追えず、他メディアの伝聞のみ
- 公式ページなし・公式プレスリリースなし

writer の未体験品ルールと組み合わせて、「調べた限りでは〜」「公式情報では〜」の表現に留める。

## サイト×Note併存 vs 上書きの使い分け（新設）

同じ製品・トピックについてサイトとNoteの両方を作るときのパターン。

### パターン1：Noteが既に投稿済 → サイトを新規追加

- サイト版：drafts/ に新規MDX作成、である調・一人称なし
- Note版：そのまま（削除・書き換えしない）
- 記事ログ：2行構成（サイト行・Note行）
- 例：Soundcore P42i（7/6 Note投稿済み → 同日サイト版を新規追加）

### パターン2：Noteが未投稿（下書き段階）→ Note導入記事に書き換え

- Note原稿を3点構成の「Note導入記事」テンプレに書き換え、サイト誘導リンクを末尾に追加
- サイト版：drafts/ に新規MDX作成
- 記事ログ：2行構成（サイト行・Note導入記事行）
- 例：CIO 10周年発表（7/2、Note原稿をNote導入記事に書き換え + サイト版新規）

### パターン3：サイト単発（Note作らない）

- クレカ記事はNote導入記事なしが基本（書き手キャラ上、クレカ記事の主観トーンをNote側で出しにくい）
- サイト単発でも記事ログには「（サイト）」サフィックスを付ける

### パターン4：Note単発（サイト作らない）

- 書き手の近況記事、開発日記、Amazon Mastercardのようなアフィなし前提の情報整理記事
- 記事ログには「（note）」サフィックスを付ける

## ガジェット記事の構成

```
導入（製品概要・立ち位置）
↓
h2 基本スペック（比較表）
↓
AmazonCard①（スペック紹介直後）
↓
h2 詳細機能・独自訴求（1〜2セクション）
↓
h2 比較・棲み分け（table積極的に）
↓
AmazonCard②（比較後、中盤）
↓
h2 エンジニア視点で見るとどう使えるか
↓
h2 気になる点（正直にデメリット）
↓
h2 まとめ（本文はここで終了。末尾の「## 関連記事」セクションは書かない）
```

## クレジットカード記事の構成

```
導入（改定・変更点の要旨）
↓
h2 概要（table：日程・対象・特典等）
↓
CTAボタン①（記事中盤・自然な文脈、提携承認済み案件のみ）
↓
h2 詳細（変更点・影響範囲・比較表）
↓
h2 気になる点／注意事項
↓
h2 まとめ
↓
CTAボタン②（まとめ後、提携承認済み案件のみ。未提携時は①②とも省略し affiliate: false）
↓
公式リンク（クレカ会社・サービス提供元の公式のみ、ここで本文終了。「## 関連記事」セクションは書かない）
```

## 記事作成フロー

**Step 1：ドラフト作成**

1. 記事ログで重複・カニバリチェック（common参照）
2. ファクトチェック用のWebSearch実施（公式ドメイン優先）
3. MDXファイルを `drafts/` に作成
4. 比較表（Markdown table）を積極的に使う

**Step 2：6観点チェック**

| 観点 | チェック内容 | 判定 |
|---|---|---|
| タイトル・見出し | メインKWが含まれるか、h2だけで流れがわかるか | ✅⚠️❌ |
| 読者体験 | 比較表の活用、判断基準の明確さ | ✅⚠️❌ |
| 収益導線 | AmazonCard/CTAの配置、押し売り感の回避 | ✅⚠️❌ |
| ファクトチェック | WebSearchで数値を検証、価格・スペック・発売日の正確性 | ✅⚠️❌ |
| SEO | description 120〜160文字、slug 20文字以内、タグ適切性 | ✅⚠️❌ |
| カニバリ | 既存記事（サイト・Note両方）とメインKWが重複しないか。同一KWでも切り口が異なれば可 | ✅⚠️❌ |

**Step 3：セキュリティチェック**

- 外部リンクはメーカー公式サイト・プレスリリースのみ許可（apple.com、anker.com、jreast.co.jp、docomo.ne.jp 等）
- 他メディア・個人ブログ・SNS・PR TIMESへのリンクは不可
- Amazonリンクは `rel="nofollow sponsored"` 付き
- XSS要素なし（script、iframe、on* イベントがMDX内にないこと）
- 画像パスはサイト内相対パス（`/images/posts/...`）。外部URL参照なし

**Step 4：修正** — ⚠️❌箇所を反映

**Step 5：draftsに保存 → 英生さんの確認待ち**

**Step 6：公開（英生さん）**

- draftsから `posts/[category]/` にファイル移動
- AmazonリンクのhrefをアソシエイトURLに差し替え（rel属性は記述済み）
- eyecatch画像を `public/images/posts/[slug].webp` に配置
- git push → GitHub Actionsが自動デプロイ
- 記事ログに「（サイト）」サフィックス付きで1行追記

## 機械チェック（Claudeが記事作成完了時に自動で実施）

```bash
# 1. description文字数（120〜160字）
python3 -c "
import re
with open('[file]') as f:
    m = re.search(r'^description:\s*(.+)$', f.read(), re.MULTILINE)
    desc = m.group(1).strip('\"').strip(\"'\")
    print(f'{len(desc)}字: {desc[:40]}...')
"

# 1b. frontmatter 型検証（YAMLがDate/dictオブジェクトに化けていないか）
python3 << 'FMCHECK'
import yaml, sys
with open('[file]') as f:
    raw = f.read()
parts = raw.split('---', 2)
if len(parts) < 3:
    print('NG: frontmatter 区切りが見つからない'); sys.exit(1)
fm = yaml.safe_load(parts[1])
errors = []
for key in ('date', 'category', 'title', 'description'):
    v = fm.get(key)
    if v is None:
        errors.append(f'{key}: 未定義')
    elif not isinstance(v, str):
        errors.append(f'{key}: 型が str でなく {type(v).__name__}（ダブルクォート必須）')
if errors:
    print('NG: ' + ' / '.join(errors)); sys.exit(1)
print('OK: frontmatter 型OK')
FMCHECK

# 2. 一人称・主観動詞・未体験なのに使用体験風の表現
grep -nE "(私|自分|僕|俺|と思う|と感じ|個人的に|気がする|期待してい|楽しみ|嬉し|使ってみ|使い込ん|使い始め|試してみ|試したところ|手にとっ|触ってみ|感触は|打鍵感|触り心地|愛用|買った|購入し|手元にあ|うちの|私の家)" [file]

# 「実際に」は「実際に発売」等の中立表現を除外して検出
grep -nE "実際に" [file] | grep -vE "実際に(発売|発表|開始|終了|導入|運用|上映|使用可)"

# 3. AmazonCard/CTA配置箇所
grep -n "AmazonCard\|cta-amazon\|asin="

# 3b. 仮ASIN 検出（XXXXXXXXXX は絶対NG、リンク切れの原因）
if grep -q 'asin="XXXXXXXXXX"' [file]; then
  echo "NG: 仮ASIN（XXXXXXXXXX）検出。実ASIN取得 or Amazon検索リンク or 同ブランド代替商品へ差し替え必須"
fi [file]

# 4. slug長（20文字以内）
echo -n "[slug]" | wc -c

# 5. 内部リンクslug実在確認 + URL形式チェック
# URL形式：/posts/gadget/xxx/ プレフィックスは404、正しくは /gadget/xxx/ or /creditcard/xxx/
grep -oE "\]\(/(posts/)?[a-z]+/[a-z0-9-]+/?\)" [file] | while read link; do
  if echo "$link" | grep -q "/posts/"; then
    echo "NG: $link （/posts/ プレフィックスは404、/gadget/ or /creditcard/ に修正）"
  fi
  slug=$(echo "$link" | sed -E 's#.*/([a-z0-9-]+)/?\)#\1#')
  category=$(echo "$link" | sed -E 's#.*/(gadget|creditcard)/.*#\1#')
  file="src/content/posts/${category}/${slug}.mdx"
  [ -f "/sessions/stoic-kind-einstein/mnt/CoreSignal/CoreSignal-media/${file}" ] && echo "OK: $link" || echo "NG MISSING: $link"
done

# 6. 画像ファイル実在確認（eyecatch + 本文中画像）
grep -oE "/images/posts/[^)]*\.webp" [file] | while read path; do
  if [ ! -f "/Users/hideki/CoreSignal/CoreSignal-media/public${path}" ]; then
    echo "MISSING: $path"
  fi
done

# 7. amazon-cache.json 実在ASIN確認
grep [ASIN] src/data/amazon-cache.json

# 8. UTF-8文字化けチェック
# 置換文字（U+FFFD、文字化けの典型サイン）
if grep -P "\x{FFFD}" [file] > /dev/null; then
  echo "NG: 置換文字（U+FFFD）検出、文字化けの疑い"
fi

# UTF-8妥当性検証
iconv -f UTF-8 -t UTF-8 [file] > /dev/null 2>&1 || echo "NG: UTF-8妥当性違反"

# 制御文字混入検出（改行・タブ以外）
grep -PnE "[\x00-\x08\x0B-\x1F\x7F]" [file] | head -5
```

# 9. 画像出所チェック（3点確認、2026-07-22 新設）

# 9a. 自作画像のみの記事 → 出所表記が「存在しない」こと
if ! grep -q "CitedImage" [file]; then
  grep -nE "画像：|figcaption|ニュースリリース.*より" [file] \
    && echo "NG: CitedImage を使わずに出所表記あり（外部素材をコンポーネント外で貼った疑い）" \
    || echo "OK: 自作画像のみ・出所表記なし"
fi

# 9b. CitedImage 使用時 → 出所表記が「存在し、propsが完備している」こと
grep -q "CitedImage" [file] && python3 << 'PY'
import re
raw = open('[file]').read()
if '<CitedImage' in raw and "import CitedImage" not in raw:
    print('NG: CitedImage の import 文がない')
for i, m in enumerate(re.finditer(r'<CitedImage\b(.*?)/>', raw, re.S), 1):
    attrs = m.group(1)
    missing = [k for k in ('src','alt','sourceName','sourceUrl','sourceDate') if f'{k}=' not in attrs]
    print(f'NG: CitedImage #{i} 不足props: {missing}' if missing else f'OK: CitedImage #{i} props完備')
    u = re.search(r'sourceUrl="([^"]+)"', attrs)
    if not u or not u.group(1).startswith('https://'):
        print(f'NG: CitedImage #{i} sourceUrl が https:// 形式でない')
PY

# 9c. 引用元の正しさ検証（Claude が WebFetch で実施。コマンドでは担保できないため必須手順として実行）
CitedImage を1つでも使った記事では、公開前に以下を**全件**確認する：

1. **公式ドメイン**：sourceUrl のドメインが発行会社・サービス提供元の公式ドメインであること（common の公式サイトリスト参照）。PR TIMES・他メディア・個人ブログは出所として不可
2. **実在**：sourceUrl を WebFetch し、ページが実際に取得できること（リダイレクト先が別内容ならNG）
3. **内容一致**：取得したページに (a) sourceDate と同じ発表日 (b) sourceName に対応する発表主体 (c) 記事で扱っている発表内容、の3つが実在すること
4. **画像の出自**：配置した画像がそのリリースページからダウンロードしたものであること（ダウンロード元の画像URLがページ内に存在し、Read tool で画像内容がキャプションと一致することを目視確認）
5. **1つでも確認できなければ画像を外して記事を通す**（出所の確からしさより記事公開を優先。迷ったら使わない）

# 10. 手書き関連記事セクション検出（2026-07-22 新設、レイアウト自動表示と二重になるため禁止）
grep -n "^## 関連記事" [file] && echo "NG: 手書きの関連記事セクションは廃止（レイアウトが自動表示）" || echo "OK: 関連記事セクションなし"

⚠️ 一項目でもNGの場合は原稿を修正してから再度チェック実施。以下は特に厳密：
- 一人称・主観動詞・使用体験風表現：**writer/SKILL.md「未体験品ルール」への抵触**なので必ず書き直し
- 文字化け（U+FFFD等）：**公開すると信頼性を大きく損なう**ので必ず修正
- description120字未満/160字超：SEO影響大
- 画像出所チェック（9a〜9c）：**自作画像に出所表記が付く／引用画像に出所表記がない／出所が検証できない**のいずれも公開不可。特に9cはWebFetchでの実在検証を省略しない
