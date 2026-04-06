    interface AmazonProduct {
    title: string;
    price: string;
    imageUrl: string;
    detailUrl: string;
    }

    async function getAccessToken(): Promise<string | null> {
    try {
        const clientId = import.meta.env.AMAZON_CLIENT_ID;
        const clientSecret = import.meta.env.AMAZON_CLIENT_SECRET;

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
        return data.access_token;
    } catch (error) {
        console.error('Token fetch error:', error);
        return null;
    }
    }

    export async function getProductByAsin(asin: string): Promise<AmazonProduct | null> {
    try {
        const token = await getAccessToken();
        if (!token) return null;

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
        };
    } catch (error) {
        console.error(`Creators API error for ASIN ${asin}:`, error);
        return null;
    }
    }