    interface AmazonProduct {
    title: string;
    price: string;
    imageUrl: string;
    detailUrl: string;
    }

    // ── トークンキャッシュ ──
    // ビルドは1つのNode.jsプロセスで走るため、モジュールスコープの変数はビルド中保持される
    let cachedToken: string | null = null;
    let tokenExpiry: number = 0;

    // ── 商品キャッシュ ──
    // 同じASINが複数記事・複数箇所で使われてもAPIコール1回で済む
    const productCache = new Map<string, AmazonProduct | null>();

    // ── レート制限対策 ──
    // Creator APIは1 TPS制限。リクエスト間に最低1秒の間隔を確保する
    let lastRequestTime: number = 0;

    async function waitForRateLimit(): Promise<void> {
    const now = Date.now();
    const elapsed = now - lastRequestTime;
    if (elapsed < 1100) {
        // 1.1秒間隔を確保（余裕を持たせる）
        await new Promise(resolve => setTimeout(resolve, 1100 - elapsed));
    }
    lastRequestTime = Date.now();
    }

    async function getAccessToken(): Promise<string | null> {
    // キャッシュが有効ならAPIコールせずに返す
    if (cachedToken && Date.now() < tokenExpiry) {
        return cachedToken;
    }

    try {
        const clientId = import.meta.env.AMAZON_CLIENT_ID;
        const clientSecret = import.meta.env.AMAZON_CLIENT_SECRET;

        await waitForRateLimit();

        const response = await fetch(
        'https://api.amazon.co.jp/auth/o2/token',
        {
            method: 'POST',
            headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `grant_type=client_credentials&client_id=${clientId}&client_secret=${clientSecret}&scope=creatorsapi::default`,
        }
        );

        if (!response.ok) {
        console.error('Token error:', response.status, await response.text());
        return null;
        }

        const data = await response.json();
        cachedToken = data.access_token;
        // expires_inは秒単位。50秒前に期限切れ扱いにして安全マージンを確保
        tokenExpiry = Date.now() + ((data.expires_in ?? 3600) - 50) * 1000;
        return cachedToken;
    } catch (error) {
        console.error('Token fetch error:', error);
        return null;
    }
    }

    // ── 直列化キュー ──
    // Astroが複数ページを並列ビルドしても、APIコールが同時に走らないようにする
    let requestQueue: Promise<void> = Promise.resolve();

    export async function getProductByAsin(asin: string): Promise<AmazonProduct | null> {
    // 商品キャッシュにあればAPIコール不要
    if (productCache.has(asin)) {
        return productCache.get(asin)!;
    }

    // キューに繋いで直列実行を保証
    const result = new Promise<AmazonProduct | null>((resolve) => {
        requestQueue = requestQueue.then(async () => {
        // キュー待ちの間に別のリクエストがキャッシュ済みの場合
        if (productCache.has(asin)) {
            resolve(productCache.get(asin)!);
            return;
        }

        try {
            const token = await getAccessToken();
            if (!token) {
            productCache.set(asin, null);
            resolve(null);
            return;
            }

            await waitForRateLimit();

            const response = await fetch(
            'https://creatorsapi.amazon/catalog/v1/getItems',
            {
                method: 'POST',
                headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                'x-marketplace': 'www.amazon.co.jp',
                },
                body: JSON.stringify({
                itemIds: [asin],
                itemIdType: 'ASIN',
                partnerTag: import.meta.env.AMAZON_PARTNER_TAG,
                partnerType: 'Associates',
                languagesOfPreference: ['ja_JP'],
                resources: [
                    'itemInfo.title',
                    'offersV2.listings.price',
                    'images.primary.large',
                ],
                }),
            }
            );

            if (!response.ok) {
            console.error('API error:', response.status, await response.text());
            productCache.set(asin, null);
            resolve(null);
            return;
            }

            const data = await response.json();
            const item = data.itemsResult?.items?.[0];
            if (!item) {
            productCache.set(asin, null);
            resolve(null);
            return;
            }

            const product: AmazonProduct = {
            title: item.itemInfo?.title?.displayValue ?? '',
            price: item.offersV2?.listings?.[0]?.price?.money?.displayAmount ?? '',
            imageUrl: item.images?.primary?.large?.url ?? '',
            detailUrl: item.detailPageURL ?? '',
            };

            productCache.set(asin, product);
            resolve(product);
        } catch (error) {
            console.error(`Creators API error for ASIN ${asin}:`, error);
            productCache.set(asin, null);
            resolve(null);
        }
        });
    });

    return result;
    }
