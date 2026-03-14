// bright-data-tiktok.js
/**
 * Bright Data TikTok Shop Channel
 *
 * Schedule: Every 4 hours
 * Timeout: 10 minutes
 *
 * Features:
 * - Monitor TikTok Shop trending products
 * - Track category trends
 * - Discover new products
 * - Collect product reviews and engagement data
 *
 * Data flow:
 * Bright Data API -> Batch write to PostgreSQL -> Update cards.amazon_data
 */

// Bright Data API 配置
const BRIGHT_DATA_API = 'https://api.brightdata.com/datasets/v3/scrape';
const BRIGHT_DATA_TOKEN = '1c7806b0-3f98-48da-93ce-8a745c40b062';

// Dataset IDs
const DATASETS = {
    SHOP_PRODUCTS: 'gd_m45m1u911dsa4274pi',
    CATEGORY_PRODUCTS: 'gd_mdr83qr42wd1wt7vm'
};

// 监控的 TikTok Shop 类别
const TIKTOK_CATEGORIES = {
    'fashion': 'https://www.tiktok.com/shop/c/necklaces/605280',
    'sports': 'https://www.tiktok.com/shop/c/sports-vests/835848',
    'beauty': 'https://www.tiktok.com/shop/c/lip-gloss/144018',
    'electronics': 'https://www.tiktok.com/shop/c/phone-cases/726158',
    'home': 'https://www.tiktok.com/shop/c/home-decor/163034'
};

// 多地区域名
const TIKTOK_DOMAINS = {
    'sg': 'https://shop-sg.tiktok.com',
    'vn': 'https://shop-vn.tiktok.com',
    'my': 'https://shop-my.tiktok.com',
    'ph': 'https://shop-ph.tiktok.com',
    'th': 'https://shop-th.tiktok.com'
};

// 热门关键词
const HOT_KEYWORDS = [
    'wireless earbuds',
    'phone case',
    'lipstick',
    'sports watch',
    'home decoration'
];

async function httpRequest(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
}

async function fetchTikTokCategoryProducts(categoryKey, categoryUrl) {
    // Get products for specified category

    const payload = {
        input: [{
            url: categoryUrl
        }]
    };

    const params = new URLSearchParams({
        dataset_id: DATASETS.CATEGORY_PRODUCTS,
        notify: 'false',
        include_errors: 'true'
    });

    const url = `${BRIGHT_DATA_API}?${params}`;

    const response = await httpRequest(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${BRIGHT_DATA_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    return response;
}

async function fetchTikTokByKeyword(keyword, domain = 'https://www.tiktok.com/shop') {
    // Search TikTok Shop products by keyword

    const payload = {
        input: [{
            keyword: keyword,
            domain: domain
        }]
    };

    const params = new URLSearchParams({
        dataset_id: DATASETS.SHOP_PRODUCTS,
        notify: 'false',
        include_errors: 'true',
        type: 'discover_new',
        discover_by: 'keyword'
    });

    const url = `${BRIGHT_DATA_API}?${params}`;

    const response = await httpRequest(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${BRIGHT_DATA_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    return response;
}

async function fetchTikTokCategoryDiscovery(categoryUrl) {
    // Category discovery

    const payload = {
        input: [{
            category_url: categoryUrl
        }]
    };

    const params = new URLSearchParams({
        dataset_id: DATASETS.SHOP_PRODUCTS,
        notify: 'false',
        include_errors: 'true',
        type: 'discover_new',
        discover_by: 'category'
    });

    const url = `${BRIGHT_DATA_API}?${params}`;

    const response = await httpRequest(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${BRIGHT_DATA_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    return response;
}

async function sendToBackend(products, categoryKey) {
    """发送数据到后端批量 API"""

    const backendUrl = 'http://103.59.103.85:8000/api/v1/batch/products';

    const payload = {
        products: products.map(p => ({
            asin: p.asin || p.item_id || p.product_id,
            title: p.title || p.name || p.Title,
            price: p.price || p.Price || p.special_price,
            rating: p.rating || p.rating_score,
            reviews_count: p.reviews_count || p.review_count || 0,
            url: p.url || p.product_link || p.ProductUrl || p.share_url,
            image: p.image || p.cover || p.image_url || p.ImageUrl,
            category: categoryKey,
            platform: 'tiktok_shop',
            source: 'bright_data_tiktok',
            fetched_at: new Date().toISOString()
        })),
        source: 'bright_data_tiktok'
    };

    const response = await httpRequest(backendUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    return response;
}

async function main() {
    console.log('🚀 Bright Data TikTok Shop Channel Started');

    const stats = {
        categories_fetched: 0,
        products_collected: 0,
        keywords_searched: 0,
        errors: []
    };

    // 获取每个类别的产品
    for (const [categoryKey, categoryUrl] of Object.entries(TIKTOK_CATEGORIES)) {
        try {
            console.log(`🛍️ Fetching ${categoryKey}...`);

            const data = await fetchTikTokCategoryProducts(categoryKey, categoryUrl);

            if (data.results && data.results.length > 0) {
                const products = data.results[0].content;

                if (products && products.length > 0) {
                    // 发送到后端
                    const result = await sendToBackend(products, categoryKey);

                    if (result.success) {
                        stats.products_collected += result.created || 0;
                        stats.categories_fetched += 1;
                        console.log(`✅ ${categoryKey}: ${products.length} products`);
                    }
                }
            }
        } catch (error) {
            console.error(`❌ Error fetching ${categoryKey}:`, error.message);
            stats.errors.push(`${categoryKey}: ${error.message}`);
        }
    }

    // 额外：通过关键词发现热门产品
    console.log('🔍 Discovering products by keywords...');

    for (const keyword of HOT_KEYWORDS) {
        try {
            const data = await fetchTikTokByKeyword(keyword, TIKTOK_DOMAINS.sg);

            if (data.results && data.results.length > 0) {
                const products = data.results[0].content;

                if (products && products.length > 0) {
                    await sendToBackend(products.slice(0, 20), `keyword_${keyword}`);
                    stats.products_collected += Math.min(20, products.length);
                    stats.keywords_searched += 1;
                    console.log(`✅ Keyword '${keyword}': ${Math.min(20, products.length)} products`);
                }
            }
        } catch (error) {
            console.error(`❌ Error searching for '${keyword}':`, error.message);
            stats.errors.push(`keyword_${keyword}: ${error.message}`);
        }
    }

    console.log('📊 Stats:', stats);

    return {
        success: stats.categories_fetched > 0 || stats.keywords_searched > 0,
        stats: stats
    };
}

// 导出给 OpenClaw
module.exports = { main };
