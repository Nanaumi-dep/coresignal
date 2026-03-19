// CloudFront Functions: coresignal-security-headers
// ランタイム: cloudfront-js-2.0
// イベントタイプ: viewer-response
// 目的: 全レスポンスにセキュリティヘッダーを付与する

function handler(event) {
  var response = event.response;
  var headers = response.headers;

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

  // TODO: CSPは将来追加予定
  // headers["content-security-policy"] = { value: "..." };

  return response;
}
