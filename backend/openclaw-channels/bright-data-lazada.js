// bright-data-lazada.js
/**
 * Bright Data Lazada Channel
 *
 * Schedule: Every 3 hours
 * Timeout: 10 minutes
 *
 * Features:
 * - Monitor Lazada product prices and promotions
 * - Track brand stores
 * - Discover hot category products
 * - Collect competitor information
 *
 * Data flow:
 * Bright Data API -> Batch write to PostgreSQL -> Update cards.amazon_data
 */

// Bright Data API 配置
const BRIGHT_DATA_API = 'https://api.brightdata.com/datasets/v3/scrape';
const BRIGHT_DATA_TOKEN = '1c7806b0-3f98-48da-93ce-8a745c40b062';

// Dataset ID
const DATASET_ID = 'gd_lk14r4zxuiw2uxpk6';

// 监控的 Lazada 类别 (多国家/地区)
const LAZADA_CATEGORIES = {
    // Malaysia
    'my_women_bags': 'https://www.lazada.com.my/shop-women-bags/',
    'my_men_sports': 'https://www.lazada.com.my/men-sports-running-shoes/',

    // Singapore
    'sg_women_bags': 'https://www.lazada.sg/women-handbags/',
    'sg_men_sports': 'https://www.lazada.sg/men-sports-running-shoes/',

    // Vietnam
    'vn_fashion': 'https://www.lazada.vn/den-trang-tri/',

    // Philippines
    'ph_electronics': 'https://www.lazada.com.ph/shop-women-bags/',

    // Indonesia
    'id_fashion': 'https://www.lazada.co.id/wanita-tas-wanita/'
};

// 热门关键词 (用于发现)
const HOT_KEYWORDS = {
    'fashion': ['dress', 'handbag', 'shoes', 'watch'],
    'electronics': ['headphones', 'charger', 'case'],
    'home': ['decoration', 'kitchen', 'furniture']
};

async function httpRequest(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
}

async function fetchLazadaCategory(categoryKey, categoryUrl) {
    // Get products for specified category

    const payload = {
        input: [{
            category_url: categoryUrl
        }]
    };

    const params = new URLSearchParams({
        dataset_id: DATASET_ID,
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

async function fetchLazadaByKeyword(domain, keyword) {
    // Search Lazada products by keyword

    const payload = {
        input: [{
            keyword: keyword,
            domain: domain
        }]
    };

    const params = new URLSearchParams({
        dataset_id: DATASET_ID,
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

async function fetchLazadaBrand(brandUrl) {
    // Get brand store products

    const payload = {
        input: [{
            url: brandUrl
        }]
    };

    const params = new URLSearchParams({
        dataset_id: DATASET_ID,
        notify: 'false',
        include_errors: 'true',
        type: 'discover_new',
        discover_by: 'brand'
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
            url: p.url || p.product_link || p.ProductUrl,
            image: p.image || p.image_url || p.ImageUrl,
            category: categoryKey,
            platform: 'lazada',
            source: 'bright_data_lazada',
            fetched_at: new Date().toISOString()
        })),
        source: 'bright_data_lazada'
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
    console.log('🚀 Bright Data Lazada Channel Started');

    const stats = {
        categories_fetched: 0,
        products_collected: 0,
        errors: []
    };

    // 获取每个类别的产品
    for (const [categoryKey, categoryUrl] of Object.entries(LAZADA_CATEGORIES)) {
        try {
            console.log(`🛍️ Fetching ${categoryKey}...`);

            const data = await fetchLazadaCategory(categoryKey, categoryUrl);

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

    for (const [domain, keywords] of Object.entries(HOT_KEYWORDS)) {
        for (const keyword of keywords.slice(0, 2)) {  // 每个类别只搜索2个关键词
            try {
                const data = await fetchLazadaByKeyword(
                    domain === 'fashion' ? 'https://www.lazada.sg' : 'https://www.lazada.com.my',
                    keyword
                );

                if (data.results && data.results.length > 0) {
                    const products = data.results[0].content;
                    if (products && products.length > 0) {
                        await sendToBackend(products.slice(0, 10), `keyword_${keyword}`);
                        stats.products_collected += Math.min(10, products.length);
                        console.log(`✅ Keyword '${keyword}': ${Math.min(10, products.length)} products`);
                    }
                }
            } catch (error) {
                console.error(`❌ Error searching for '${keyword}':`, error.message);
                stats.errors.push(`keyword_${keyword}: ${error.message}`);
            }
        }
    }

    console.log('📊 Stats:', stats);

    return {
        success: stats.categories_fetched > 0,
        stats: stats
    };
}

// 导出给 OpenClaw
module.exports = { main };
