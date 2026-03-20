// CloudFront Functions: coresignal-security-headers
// ランタイム: cloudfront-js-2.0
// イベントタイプ: viewer-response
// 目的: 全レスポンスにセキュリティヘッダーとキャッシュ制御ヘッダーを付与する

function handler(event) {
  var response = event.response;
  var headers = response.headers;
  var uri = event.request.uri; // キャッシュ制御のためURIを取得

  // =====================
  // セキュリティヘッダー
  // =====================

  // HTTPS強制（1年間、サブドメイン含む）
  headers["strict-transport-security"] = {
    value: "max-age=31536000; includeSubDomains",
  };

  // クリックジャッキング防止
  headers["x-frame-options"] = { value: "DENY" };

  // MIMEタイプスニッフィング防止
  headers["x-content-type-options"] = { value: "nosniff" };

  // リファラーポリシー
  headers["referrer-policy"] = {
    value: "strict-origin-when-cross-origin",
  };

  // TODO: CSPは将来追加予定（GA4・AdSense追加時に設定）
  // headers["content-security-policy"] = { value: "..." };

  // =====================
  // キャッシュ制御ヘッダー
  // =====================

  // _astro/配下（ハッシュ付きアセット）→ 1年間キャッシュ
  if (uri.includes("/_astro/")) {
    headers["cache-control"] = {
      value: "public, max-age=31536000, immutable",
    };
  // HTMLファイル・ディレクトリ → 1日キャッシュ
  } else if (uri.endsWith(".html") || uri.endsWith("/")) {
    headers["cache-control"] = {
      value: "public, max-age=86400",
    };
  // 画像ファイル → 1週間キャッシュ
  } else if (uri.match(/\.(jpg|jpeg|png|webp|gif|svg|ico)$/)) {
    headers["cache-control"] = {
      value: "public, max-age=604800",
    };
  // サイトマップ・robots.txt → 1日キャッシュ
  } else if (uri.match(/sitemap.*\.xml$/) || uri.endsWith("robots.txt")) {
    headers["cache-control"] = {
      value: "public, max-age=86400",
    };
  }

  return response;
}
