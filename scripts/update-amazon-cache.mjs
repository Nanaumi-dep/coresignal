import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CACHE_PATH = path.resolve(__dirname, '../src/data/amazon-cache.json');

// 環境変数から取得（GitHub Actionsのsecretsから渡される）
const CLIENT_ID = process.env.AMAZON_CLIENT_ID;
const CLIENT_SECRET = process.env.AMAZON_CLIENT_SECRET;
const PARTNER_TAG = process.env.AMAZON_PARTNER_TAG;

if (!CLIENT_ID || !CLIENT_SECRET || !PARTNER_TAG) {
console.error('Missing environment variables');
process.exit(1);
}

// レート制限
let lastRequestTime = 0;
async function waitForRateLimit() {
const now = Date.now();
const elapsed = now - lastRequestTime;
if (elapsed < 1100) {
    await new Promise(resolve => setTimeout(resolve, 1100 - elapsed));
}
lastRequestTime = Date.now();
}

// トークン取得
async function getAccessToken() {
await waitForRateLimit();
const response = await fetch('https://api.amazon.co.jp/auth/o2/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&scope=creatorsapi::default`,
});
if (!response.ok) {
    console.error('Token error:', response.status, await response.text());
    return null;
}
const data = await response.json();
return data.access_token;
}

// 商品取得（リトライ付き）
async function fetchProduct(asin, token) {
for (let attempt = 0; attempt < 3; attempt++) {
    await waitForRateLimit();
    const response = await fetch('https://creatorsapi.amazon/catalog/v1/getItems', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'x-marketplace': 'www.amazon.co.jp',
    },
    body: JSON.stringify({
        itemIds: [asin],
        itemIdType: 'ASIN',
        partnerTag: PARTNER_TAG,
        partnerType: 'Associates',
        languagesOfPreference: ['ja_JP'],
        resources: ['itemInfo.title', 'offersV2.listings.price', 'images.primary.large'],
    }),
    });

    if (response.status === 429) {
    const waitTime = (attempt + 1) * 2000;
    console.warn(`Rate limited for ${asin}, retry in ${waitTime}ms (${attempt + 1}/3)`);
    await new Promise(resolve => setTimeout(resolve, waitTime));
    continue;
    }

    if (!response.ok) {
    console.error(`API error for ${asin}:`, response.status);
    return null;
    }

    const data = await response.json();
    const item = data.itemsResult?.items?.[0];
    if (!item) return null;

    return {
    title: item.itemInfo?.title?.displayValue ?? '',
    price: item.offersV2?.listings?.[0]?.price?.money?.displayAmount ?? '',
    imageUrl: item.images?.primary?.large?.url ?? '',
    detailUrl: item.detailPageURL ?? '',
    updatedAt: new Date().toISOString(),
    };
}
console.error(`Failed after 3 retries for ${asin}`);
return null;
}

// メイン処理
async function main() {
// キャッシュ読み込み
let cache = {};
try {
    cache = JSON.parse(fs.readFileSync(CACHE_PATH, 'utf-8'));
} catch {
    console.log('No existing cache, starting fresh');
}

const asins = Object.keys(cache);
if (asins.length === 0) {
    console.log('No ASINs in cache, nothing to update');
    return;
}

console.log(`Updating ${asins.length} ASINs...`);

const token = await getAccessToken();
if (!token) {
    console.error('Failed to get token, aborting');
    process.exit(1);
}

let updated = 0;
for (const asin of asins) {
    const product = await fetchProduct(asin, token);
    if (product) {
    cache[asin] = product;
    updated++;
    console.log(`✓ ${asin}: ${product.title} (${product.price})`);
    } else {
    console.warn(`✗ ${asin}: failed to update, keeping old data`);
    }
}

// 保存
fs.writeFileSync(CACHE_PATH, JSON.stringify(cache, null, 2));
console.log(`Done. Updated ${updated}/${asins.length} products.`);
}

main().catch(error => {
console.error('Fatal error:', error);
process.exit(1);
});