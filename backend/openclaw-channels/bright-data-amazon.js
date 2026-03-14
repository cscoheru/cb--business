// bright-data-amazon.js
/**
 * Bright Data Amazon Channel
 *
 * Schedule: Every 2 hours
 * Timeout: 10 minutes
 *
 * Features:
 * - Monitor Amazon product price and rating changes
 * - Track Best Sellers ranking changes
 * - Collect product review data
 * - Discover competitor information
 *
 * Data flow:
 * Bright Data API -> Batch write to PostgreSQL -> Update cards.amazon_data
 */

// Bright Data API 配置
const BRIGHT_DATA_API = 'https://api.brightdata.com/datasets/v3/scrape';
const BRIGHT_DATA_TOKEN = '1c7806b0-3f98-48da-93ce-8a745c40b062';

// Dataset IDs
const DATASETS = {
    SEARCH: 'gd_lwdb4vjm1ehb499uxs'
};

// 监控的 Amazon 关键词
const AMAZON_KEYWORDS = {
    'wireless_earbuds': 'wireless earbuds',
    'phone_chargers': 'phone chargers',
    'desk_lamps': 'desk lamps',
    'coffee_makers': 'coffee makers',
    'fitness_trackers': 'fitness trackers'
};

async function httpRequest(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    // Bright Data returns newline-delimited JSON (NDJSON)
    const text = await response.text();
    const lines = text.trim().split('\n').filter(line => line.trim());
    return lines.map(line => JSON.parse(line));
}

async function fetchAmazonByKeyword(keyword) {
    // Search Amazon products by keyword using search dataset

    const payload = {
        input: [{
            keyword: keyword,
            url: 'https://www.amazon.com',
            pages_to_search: 1
        }]
    };

    const params = new URLSearchParams({
        dataset_id: DATASETS.SEARCH,
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

async function fetchProductByKeyword(keyword) {
    // Search Amazon products by keyword

    const payload = {
        input: [{
            keyword: keyword,
            zipcode: ''
        }]
    };

    const params = new URLSearchParams({
        dataset_id: DATASETS.PRODUCTS,
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

async function fetchProductReviews(productUrl) {
    // Get product reviews

    const payload = {
        input: [{
            url: productUrl,
            reviews_to_not_include: []
        }]
    };

    const params = new URLSearchParams({
        dataset_id: DATASETS.REVIEWS,
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

async function sendToBackend(products, categoryKey) {
    // Send data to backend batch API

    const backendUrl = 'http://103.59.103.85:8000/api/v1/batch/products';

    const payload = {
        products: products.map(p => ({
            asin: p.asin,
            title: p.name || p.title,
            price: p.final_price || p.price,
            rating: p.rating,
            reviews_count: p.num_ratings || p.reviews_count || 0,
            url: p.url,
            image: p.image,
            category: categoryKey,
            source: 'bright_data_amazon',
            fetched_at: new Date().toISOString()
        })),
        source: 'bright_data_amazon'
    };

    // Use regular fetch for backend API (returns JSON)
    const response = await fetch(backendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        throw new Error(`Backend API error: ${response.status}`);
    }

    return await response.json();
}

async function main() {
    console.log('🚀 Bright Data Amazon Channel Started');

    const stats = {
        keywords_fetched: 0,
        products_collected: 0,
        errors: []
    };

    // 获取每个关键词的产品
    for (const [categoryKey, keyword] of Object.entries(AMAZON_KEYWORDS)) {
        try {
            console.log(`📦 Fetching ${categoryKey} (${keyword})...`);

            const products = await fetchAmazonByKeyword(keyword);

            if (products && products.length > 0) {
                // 发送到后端 (限制每个类别10个产品以节省时间)
                const productsToSend = products.slice(0, 10);
                const result = await sendToBackend(productsToSend, categoryKey);

                if (result.success) {
                    stats.products_collected += productsToSend.length;
                    stats.keywords_fetched += 1;
                    console.log(`✅ ${categoryKey}: ${products.length} products (sent ${productsToSend.length})`);
                }
            }
        } catch (error) {
            console.error(`❌ Error fetching ${categoryKey}:`, error.message);
            stats.errors.push(`${categoryKey}: ${error.message}`);
        }
    }

    console.log('📊 Stats:', stats);

    return {
        success: stats.keywords_fetched > 0,
        stats: stats
    };
}

// 导出给 OpenClaw
module.exports = { main };

// Run when executed directly
if (require.main === module) {
    main().then(result => {
        console.log('\n=== Execution Complete ===');
        console.log(JSON.stringify(result, null, 2));
        process.exit(result.success ? 0 : 1);
    }).catch(err => {
        console.error('Execution failed:', err);
        process.exit(1);
    });
}
