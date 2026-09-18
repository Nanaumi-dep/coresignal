#!/usr/bin/env node
/**
 * GA4 Data API から「過去28日でよく読まれた記事」を取得して
 * src/data/popular.json に書き出す。
 *
 * ビルド前に実行する。認証情報が無い・API が失敗した場合は
 * 何もせず正常終了する（index.astro 側が固定リストにフォールバックする）。
 * ここでビルドを止めないのが重要。解析データの欠損でサイトが落ちる理由は無い。
 *
 * 必要な環境変数:
 *   GA4_PROPERTY_ID  … GA4 のプロパティID（数字のみ。測定IDとは別物）
 *   GA4_SA_KEY       … サービスアカウントの鍵JSON（そのまま or base64）
 *
 * 依存パッケージなし（Node 18+ の fetch と crypto のみ）。
 */

import { createSign } from "node:crypto";
import { writeFileSync, readdirSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT_PATH = join(ROOT, "src/data/popular.json");
const POSTS_DIR = join(ROOT, "src/content/posts");

const LOOKBACK_DAYS = 28;
const LIMIT = 5;

/** 除外するパス（トップ・固定ページ・一覧ページ） */
const EXCLUDE_EXACT = new Set([
  "/",
  "/about/",
  "/contact/",
  "/privacy/",
  "/disclosure/",
  "/404/",
  "/gadget/",
  "/creditcard/",
]);

function log(msg) {
  console.log(`[fetch-popular] ${msg}`);
}

/** 正常終了。データは書かず、既存の popular.json があればそれを残す */
function skip(reason) {
  log(`スキップ: ${reason}`);
  log("固定リスト（FALLBACK_SLUGS）でビルドを続行します");
  process.exit(0);
}

/** 実在する記事の id 一覧（"gadget/foo" 形式）を集める */
function collectPostIds() {
  const ids = new Set();
  for (const category of readdirSync(POSTS_DIR, { withFileTypes: true })) {
    if (!category.isDirectory()) continue;
    for (const file of readdirSync(join(POSTS_DIR, category.name))) {
      if (!file.endsWith(".mdx")) continue;
      ids.add(`${category.name}/${file.replace(/\.mdx$/, "")}`);
    }
  }
  return ids;
}

/** サービスアカウント鍵を読む。生JSONでもbase64でも受ける */
function loadServiceAccount(raw) {
  const text = raw.trim().startsWith("{")
    ? raw
    : Buffer.from(raw, "base64").toString("utf8");
  const sa = JSON.parse(text);
  if (!sa.client_email || !sa.private_key) {
    throw new Error("client_email / private_key が鍵JSONに含まれていません");
  }
  return sa;
}

const b64url = (input) =>
  Buffer.from(input).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

/** サービスアカウントの鍵で JWT を作り、アクセストークンと交換する */
async function getAccessToken(sa) {
  const now = Math.floor(Date.now() / 1000);
  const claim = {
    iss: sa.client_email,
    scope: "https://www.googleapis.com/auth/analytics.readonly",
    aud: "https://oauth2.googleapis.com/token",
    exp: now + 3600,
    iat: now,
  };
  const unsigned = `${b64url(JSON.stringify({ alg: "RS256", typ: "JWT" }))}.${b64url(
    JSON.stringify(claim)
  )}`;
  const signature = createSign("RSA-SHA256")
    .update(unsigned)
    .sign(sa.private_key)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");

  const res = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: `${unsigned}.${signature}`,
    }),
  });
  if (!res.ok) {
    throw new Error(`トークン取得に失敗 (${res.status}): ${await res.text()}`);
  }
  return (await res.json()).access_token;
}

/** 過去28日のページ別PVを取得する */
async function runReport(token, propertyId) {
  const res = await fetch(
    `https://analyticsdata.googleapis.com/v1beta/properties/${propertyId}:runReport`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        dateRanges: [{ startDate: `${LOOKBACK_DAYS}daysAgo`, endDate: "yesterday" }],
        dimensions: [{ name: "pagePath" }],
        metrics: [{ name: "screenPageViews" }],
        orderBys: [{ metric: { metricName: "screenPageViews" }, desc: true }],
        // 記事以外が混ざるので多めに取ってからこちら側で絞る
        limit: 100,
      }),
    }
  );
  if (!res.ok) {
    throw new Error(`runReport に失敗 (${res.status}): ${await res.text()}`);
  }
  return (await res.json()).rows ?? [];
}

/** "/gadget/foo/?utm=..." → "gadget/foo" 。記事でなければ null */
function pathToPostId(pagePath, validIds) {
  const path = pagePath.split("?")[0].split("#")[0];
  const normalized = path.endsWith("/") ? path : `${path}/`;
  if (EXCLUDE_EXACT.has(normalized)) return null;

  const parts = normalized.split("/").filter(Boolean);
  if (parts.length !== 2) return null;

  const id = `${parts[0]}/${parts[1]}`;
  // GA4 側にしか存在しない（削除済みの）記事を並べないよう実在確認する
  return validIds.has(id) ? id : null;
}

async function main() {
  const propertyId = process.env.GA4_PROPERTY_ID;
  const saKey = process.env.GA4_SA_KEY;

  if (!propertyId || !saKey) {
    skip("GA4_PROPERTY_ID / GA4_SA_KEY が未設定");
  }

  const validIds = collectPostIds();
  log(`記事 ${validIds.size} 本を確認`);

  const sa = loadServiceAccount(saKey);
  const token = await getAccessToken(sa);
  const rows = await runReport(token, propertyId);
  log(`GA4 から ${rows.length} 行を取得`);

  const ranked = [];
  const seen = new Set();
  for (const row of rows) {
    const id = pathToPostId(row.dimensionValues[0].value, validIds);
    if (!id || seen.has(id)) continue;
    seen.add(id);
    ranked.push({ id, views: Number(row.metricValues[0].value) });
    if (ranked.length >= LIMIT) break;
  }

  if (ranked.length === 0) {
    skip("記事ページのPVが1件も取れなかった");
  }

  const payload = {
    generatedAt: new Date().toISOString(),
    lookbackDays: LOOKBACK_DAYS,
    items: ranked,
  };

  mkdirSync(dirname(OUT_PATH), { recursive: true });
  writeFileSync(OUT_PATH, `${JSON.stringify(payload, null, 2)}\n`, "utf8");

  log(`書き出し完了: ${OUT_PATH}`);
  for (const [i, item] of ranked.entries()) {
    log(`  ${i + 1}. ${item.id} (${item.views} PV)`);
  }
}

main().catch((err) => {
  // 解析データが取れないことは、サイトが落ちる理由にはならない
  log(`エラー: ${err.message}`);
  skip("GA4 の取得に失敗");
});
