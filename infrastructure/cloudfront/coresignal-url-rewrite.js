// CloudFront Functions: coresignal-url-rewrite
// ランタイム: cloudfront-js-2.0
// イベントタイプ: viewer-request
// 目的: www → non-www リダイレクト＋サブディレクトリへのアクセス時に index.html を補完する

function handler(event) {
  var request = event.request;
  var host = request.headers.host.value;
  var uri = request.uri;

  // www.coresignal.jp → coresignal.jp へ 301 リダイレクト
  if (host === "www.coresignal.jp") {
    return {
      statusCode: 301,
      statusDescription: "Moved Permanently",
      headers: {
        location: { value: "https://coresignal.jp" + uri },
      },
    };
  }

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
