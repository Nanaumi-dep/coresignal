// CloudFront Functions: coresignal-url-rewrite
// ランタイム: cloudfront-js-2.0
// イベントタイプ: viewer-request
// 目的: サブディレクトリへのアクセス時に index.html を補完する

function handler(event) {
  var request = event.request;
  var uri = request.uri;

  // 末尾が / の場合、index.html を付与
  if (uri.endsWith("/")) {
    request.uri += "index.html";
  }
  // 拡張子がない場合、/index.html を付与
  else if (!uri.includes(".")) {
    request.uri += "/index.html";
  }

  return request;
}
